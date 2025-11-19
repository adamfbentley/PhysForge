from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from rq import Queue
from redis import Redis

from ..database import get_report_db
from ..security import get_current_active_user
from .. import schemas, crud
from ..storage_utils import get_presigned_download_url
from ..config import settings
from ..worker_task import generate_report_task # Import the task function

import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Redis connection for RQ
redis_conn = Redis(host='localhost', port=6379, db=0)
report_queue = Queue('report_generation', connection=redis_conn)

@router.post("/", response_model=schemas.ReportResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_report_job(
    report_config: schemas.ReportGenerationConfig,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_report_db)
):
    """
    Submits a new report generation job.
    The actual report generation is offloaded to a background RQ worker.
    """
    logger.info(f"User {current_user.id} requested report generation for job {report_config.job_id} (type: {report_config.report_type})")

    # Create a PENDING entry in the database immediately
    report_create_data = schemas.ReportCreate(
        job_id=report_config.job_id,
        owner_id=current_user.id,
        report_type=report_config.report_type,
        report_path="PENDING", # Placeholder, will be updated by worker
        status="PENDING",
        metadata={"output_name": report_config.output_name}
    )
    db_report = crud.create_report(db, report_create_data)

    # Enqueue the report generation task
    job = report_queue.enqueue(
        generate_report_task,
        report_db_id=db_report.id,
        job_id=report_config.job_id,
        owner_id=current_user.id,
        report_type=report_config.report_type,
        output_name=report_config.output_name,
        dms_token=current_user.token, # Pass the user's JWT for internal service calls
        job_timeout=3600 # 1 hour timeout for report generation
    )
    logger.info(f"Report generation job {job.id} enqueued for report_db_id {db_report.id}.")

    # Return the initial PENDING report response
    return schemas.ReportResponse.model_validate(db_report)

@router.get("/{report_id}", response_model=schemas.ReportResponse)
async def get_report(
    report_id: int,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_report_db)
):
    """
    Retrieves a specific report by ID and provides a presigned download URL.
    Ensures the user is the owner of the report.
    """
    db_report = crud.get_report_by_id(db, report_id)
    if not db_report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    if db_report.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this report")
    
    if db_report.status != "GENERATED":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Report status is {db_report.status}. Cannot download yet.")

    # Generate presigned URL for download
    # The dms_token is passed here for consistency, though MinIO client itself doesn't use it for auth.
    # It might be used by storage_utils if it needs to fetch from other token-protected MinIO buckets.
    # The report_path is expected to be in the format /bucket_name/object_name
    object_name_in_minio = db_report.report_path.split('/', 2)[-1]
    download_url = await get_presigned_download_url(object_name_in_minio)
    
    report_response = schemas.ReportResponse.model_validate(db_report)
    report_response.download_url = download_url
    return report_response

@router.get("/", response_model=List[schemas.ReportResponse])
async def list_reports(
    skip: int = 0,
    limit: int = 100,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_report_db)
):
    """
    Lists all reports owned by the authenticated user.
    """
    reports = crud.get_reports_by_owner(db, current_user.id, skip=skip, limit=limit)
    # For listing, we don't generate presigned URLs for all reports by default for performance.
    # A separate endpoint or a flag could be added if needed.
    return [schemas.ReportResponse.model_validate(report) for report in reports]
