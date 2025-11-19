import logging
import json
import io
import sys
import os
import time
from datetime import datetime

import torch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to allow importing backend.job_orchestration_service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.job_orchestration_service.models import Base as JobBase, Job, JobStatusLog
from backend.job_orchestration_service.schemas import JobStatusUpdate

from .config import settings
from .pinn_config import PinnTrainingConfig
from .pinn_model import build_model, DeepONet # Import DeepONet for type checking
from .pinn_solver import PinnSolver
from .pinn_results import TrainingMetrics, PinnTrainingResult
from .storage_utils import save_model_to_minio, save_logs_to_minio, fetch_dataset_from_dms

logger = logging.getLogger(__name__)

# Setup database connection for Job Orchestration Service (for status updates)
JobEngine = create_engine(settings.JOB_ORCHESTRATION_DATABASE_URL)
JobSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=JobEngine)

def get_job_db():
    db = JobSessionLocal()
    try:
        yield db
    finally:
        db.close()

def update_job_status_in_db(job_id: int, status: str, progress: int, message: str, 
                            results_path: Optional[str] = None, logs_path: Optional[str] = None,
                            error_message: Optional[str] = None, started_at: Optional[datetime] = None,
                            completed_at: Optional[datetime] = None,
                            feature_library_path: Optional[str] = None): # Added for consistency with JOS Job model
    """Helper function to update job status in the Job Orchestration Service database."""
    db = next(get_job_db())
    try:
        db_job = db.query(Job).filter(Job.id == job_id).first()
        if db_job:
            db_job.status = status
            db_job.progress = progress
            db_job.updated_at = datetime.now()
            if results_path: db_job.results_path = results_path
            if logs_path: db_job.logs_path = logs_path
            if error_message: db_job.error_message = error_message
            if started_at: db_job.started_at = started_at
            if completed_at: db_job.completed_at = completed_at
            if feature_library_path: db_job.feature_library_path = feature_library_path # Added

            db_log = JobStatusLog(
                job_id=job_id,
                status=status,
                message=message
            )
            db.add(db_job)
            db.add(db_log)
            db.commit()
            db.refresh(db_job)
            logger.info(f"Job {job_id} status updated to {status} with message: {message}")
        else:
            logger.error(f"Job {job_id} not found in database for status update.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update job {job_id} status in DB: {e}")
    finally:
        db.close()

class LogCapture(io.StringIO):
    """A StringIO subclass to capture logs and also print them."""
    def __init__(self):
        super().__init__()
        self.terminal = sys.stdout

    def write(self, s):
        super().write(s)
        self.terminal.write(s)

    def flush(self):
        super().flush()
        self.terminal.flush()

async def run_pinn_training_job(job_id: int, pinn_config_dict: dict, user_id: int, dms_token: str):
    """Main function executed by the RQ worker for PINN training."""
    logger.info(f"Worker received PINN training job: {job_id}")
    log_capture = LogCapture()
    sys.stdout = log_capture
    sys.stderr = log_capture

    start_time = time.time()
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    logger.info(f"Using device: {device}")

    try:
        pinn_config = PinnTrainingConfig(**pinn_config_dict)
        update_job_status_in_db(job_id, "RUNNING", 0, "Initializing PINN training...", started_at=datetime.now())

        data = None
        if pinn_config.dataset_ref:
            logger.info(f"Fetching dataset {pinn_config.dataset_ref.dataset_id} from DMS...")
            data = await fetch_dataset_from_dms(
                pinn_config.dataset_ref.dataset_id, 
                user_id, 
                dms_token, 
                pinn_config.dataset_ref.version_id,
                input_dataset_name=pinn_config.dataset_ref.input_dataset_name,
                output_dataset_name=pinn_config.dataset_ref.output_dataset_name
            )
            logger.info(f"Dataset fetched successfully. Input shape: {data['x'].shape}, Output shape: {data['y'].shape}")

        input_dim = 0
        if pinn_config.network_architecture.network_type == "DeepONet":
            if pinn_config.network_architecture.branch_input_dim is None or pinn_config.network_architecture.trunk_input_dim is None:
                raise ValueError("DeepONet requires 'branch_input_dim' and 'trunk_input_dim' in network_architecture.")
            input_dim = pinn_config.network_architecture.branch_input_dim + pinn_config.network_architecture.trunk_input_dim
            if data and data['x'].shape[1] != input_dim:
                raise ValueError(f"DeepONet input dimension mismatch. Expected {input_dim}, got {data['x'].shape[1]} from dataset.")
        elif data and 'x' in data:
            input_dim = data['x'].shape[1]
        elif pinn_config.physics_loss_config:
            input_dim = len(pinn_config.physics_loss_config.independent_variables)
        
        if input_dim == 0:
            raise ValueError("Could not determine input dimension for the PINN model. Ensure dataset or physics config is provided.")

        model = build_model(input_dim=input_dim, config=pinn_config.network_architecture)
        logger.info(f"PINN model built: {model}")

        solver = PinnSolver(model, pinn_config, device=device)
        
        def callback(progress: int, status: str, message: str):
            update_job_status_in_db(job_id, status, progress, message, feature_library_path=None) # Pass None for PINN training

        training_metrics_dict = solver.train(data, callback)

        model_path = await save_model_to_minio(model, job_id, pinn_config.output_name)
        logger.info(f"Model saved to: {model_path}")

        full_logs = log_capture.getvalue()
        logs_path = await save_logs_to_minio(full_logs, job_id, pinn_config.output_name)
        logger.info(f"Logs saved to: {logs_path}")

        end_time = time.time()
        duration = end_time - start_time

        training_metrics = TrainingMetrics(
            epochs_run=pinn_config.training_parameters.epochs,
            training_duration_seconds=duration,
            **training_metrics_dict
        )

        pinn_result = PinnTrainingResult(
            job_id=job_id,
            model_path=model_path,
            metrics=training_metrics,
            logs_path=logs_path,
            config_used=pinn_config_dict
        )

        update_job_status_in_db(job_id, "COMPLETED", 100, "PINN training completed successfully.", 
                                results_path=model_path, logs_path=logs_path, completed_at=datetime.now(),
                                feature_library_path=None) # Pass None for PINN training
        logger.info(f"Job {job_id} completed. Results: {pinn_result.model_dump_json(indent=2)}")

    except Exception as e:
        error_msg = f"PINN training job {job_id} failed: {e}"
        logger.exception(error_msg)
        full_logs = log_capture.getvalue()
        output_name_for_error = pinn_config.output_name if 'pinn_config' in locals() else f"job_{job_id}"
        logs_path = await save_logs_to_minio(full_logs, job_id, output_name_for_error + "_error")
        update_job_status_in_db(job_id, "FAILED", 0, error_msg, error_message=str(e), logs_path=logs_path, completed_at=datetime.now(),
                                feature_library_path=None) # Pass None for PINN training
    finally:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        logger.info(f"Worker finished processing job: {job_id}")
