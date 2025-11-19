import io
import json
import logging
import httpx
from datetime import datetime

from rq import Queue
from redis import Redis

from .config import settings
from .crud import update_report_status, create_report, get_report_by_id
from .database import SessionLocal
from .report_generator import ReportGenerator
from .schemas import ReportStatusUpdate, ReportCreate
from .storage_utils import upload_file_to_minio, get_object_content_from_minio

logger = logging.getLogger(__name__)

# Initialize Redis connection for RQ
redis_conn = Redis(host='localhost', port=6379, db=0)
report_queue = Queue('report_generation', connection=redis_conn)

async def _fetch_job_details_from_jos(job_id: int, dms_token: str) -> dict:
    """Fetches full job details from the Job Orchestration Service."""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {dms_token}"}
        response = await client.get(f"{settings.JOB_ORCHESTRATION_SERVICE_URL}/jobs/{job_id}", headers=headers)
        response.raise_for_status()
        return response.json()

async def _update_job_status_in_jos(job_id: int, status: str, report_path: str, dms_token: str):
    """Updates the job status and report path in the Job Orchestration Service."""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {dms_token}"}
        payload = {"status": status, "report_path": report_path}
        response = await client.put(f"{settings.JOB_ORCHESTRATION_SERVICE_URL}/jobs/{job_id}/status", json=payload, headers=headers)
        response.raise_for_status()
        logger.info(f"Updated JOS job {job_id} status to {status} with report path {report_path}.")

def generate_report_task(report_db_id: int, job_id: int, owner_id: int, report_type: str, output_name: str, dms_token: str):
    """
    RQ worker task to generate and upload reports.
    This function is synchronous as RQ tasks are typically synchronous.
    HTTP calls within this function will be made using httpx.Client (synchronous)
    or by running async functions in a new event loop.
    """
    logger.info(f"Starting report generation task for report_db_id: {report_db_id}, job_id: {job_id}, type: {report_type}")
    db = SessionLocal()
    try:
        report_generator = ReportGenerator(dms_token=dms_token)
        report_path = None
        report_content_bytes = None
        content_type = ""

        # Fetch job details from JOS (synchronously for RQ task)
        # Using a new event loop for async httpx call in a sync context
        import asyncio
        loop = asyncio.get_event_loop()
        job_details = loop.run_until_complete(report_generator._fetch_job_details_from_jos(job_id, settings.JOB_ORCHESTRATION_SERVICE_URL))

        if report_type == "json_summary":
            report_data = loop.run_until_complete(report_generator.generate_json_report(job_id, job_details, settings.JOB_ORCHESTRATION_SERVICE_URL))
            report_content_bytes = json.dumps(report_data, indent=2).encode('utf-8')
            object_name = f"reports/{owner_id}/{output_name}.json"
            content_type = "application/json"
        elif report_type == "jupyter_notebook":
            notebook_content = loop.run_until_complete(report_generator.generate_jupyter_notebook(job_id, job_details, settings.JOB_ORCHESTRATION_SERVICE_URL))
            report_content_bytes = notebook_content.encode('utf-8')
            object_name = f"reports/{owner_id}/{output_name}.ipynb"
            content_type = "application/x-ipynb+json"
        else:
            raise ValueError(f"Unsupported report type: {report_type}")

        # Upload to MinIO (synchronously for RQ task)
        file_data = io.BytesIO(report_content_bytes)
        file_size = len(report_content_bytes)
        report_path = loop.run_until_complete(upload_file_to_minio(object_name, file_data, file_size, content_type))

        # Update local DB status
        status_update = ReportStatusUpdate(status="GENERATED", report_path=report_path, metadata={"generated_at": datetime.now().isoformat()})
        update_report_status(db, report_db_id, status_update)
        logger.info(f"Report {report_db_id} status updated to GENERATED. Path: {report_path}")

        # Update JOS job status (synchronously for RQ task)
        loop.run_until_complete(_update_job_status_in_jos(job_id, "REPORT_GENERATED", report_path, dms_token))

    except Exception as e:
        logger.error(f"Error generating report for report_db_id {report_db_id}: {e}", exc_info=True)
        status_update = ReportStatusUpdate(status="FAILED", metadata={"error": str(e)})
        update_report_status(db, report_db_id, status_update)
        # Attempt to update JOS status to FAILED as well
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            loop.run_until_complete(_update_job_status_in_jos(job_id, "REPORT_FAILED", "", dms_token))
        except Exception as jos_e:
            logger.error(f"Failed to update JOS job {job_id} status to REPORT_FAILED: {jos_e}")
    finally:
        db.close()
