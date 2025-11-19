import logging
import json
import io
import sys
import os
import time
from datetime import datetime
from typing import Optional

import torch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to allow importing backend.job_orchestration_service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.job_orchestration_service.models import Base as JobBase, Job, JobStatusLog
from backend.job_orchestration_service.schemas import JobStatusUpdate

from .config import settings
from .schemas import DerivativeJobConfig, DerivativeResult
from .storage_utils import load_model_from_minio, save_derivatives_to_minio, save_logs_to_minio
from .derivative_calculator import DerivativeCalculator
from .feature_generator import FeatureGenerator # STORY-303: Import FeatureGenerator

# Import necessary components from pinn_training_service to reconstruct models
from backend.pinn_training_service.pinn_model import build_model
from backend.pinn_training_service.pinn_config import NetworkArchitecture as PinnNetworkArchitecture

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
                            feature_library_path: Optional[str] = None): # STORY-303: Added feature_library_path
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
            if feature_library_path: db_job.feature_library_path = feature_library_path # STORY-303: Update feature_library_path

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

async def run_derivative_job(job_id: int, derivative_config_dict: dict, user_id: int, dms_token: str):
    """Main function executed by the RQ worker for derivative computation."""
    logger.info(f"Worker received derivative computation job: {job_id}")
    log_capture = LogCapture()
    sys.stdout = log_capture
    sys.stderr = log_capture

    start_time = time.time()
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    logger.info(f"Using device: {device}")

    feature_library_path = None # Initialize to None

    try:
        derivative_config = DerivativeJobConfig(**derivative_config_dict)
        update_job_status_in_db(job_id, "RUNNING", 0, "Initializing derivative computation...", started_at=datetime.now())

        network_arch_config = PinnNetworkArchitecture(**derivative_config.network_architecture)
        
        model = build_model(input_dim=derivative_config.input_dim, config=network_arch_config)
        logger.info(f"PINN model architecture built for loading: {model}")

        await load_model_from_minio(model, derivative_config.pinn_model_path)
        logger.info(f"PINN model weights loaded from {derivative_config.pinn_model_path}")

        calculator = DerivativeCalculator(model, device=device)
        
        logger.info(f"Generating grid points and computing derivatives up to order {derivative_config.max_derivative_order}...")
        computed_derivatives_np = calculator.compute_derivatives_on_grid(
            derivative_config.output_grid,
            derivative_config.max_derivative_order
        )
        logger.info("Derivatives computed successfully.")

        # Save derivatives to MinIO
        output_object_name = f"derivatives/{job_id}/{derivative_config.output_name}.h5"
        results_path = await save_derivatives_to_minio(output_object_name, computed_derivatives_np, job_id, derivative_config.output_name)
        logger.info(f"Derivative results saved to: {results_path}")

        # STORY-303: Generate and save feature library if configured
        if derivative_config.generate_feature_library and derivative_config.feature_library_config:
            logger.info("Generating feature library...")
            
            # Prepare flattened data for FeatureGenerator
            flattened_data_for_features = {} 
            for key, value in computed_derivatives_np.items():
                if key.startswith('grid_'): # Independent variables are prefixed with 'grid_'
                    flattened_data_for_features[key[5:]] = value.flatten() # e.g., 'grid_x' -> 'x'
                else: # u and its derivatives
                    flattened_data_for_features[key] = value.flatten()
            
            # Extract independent and dependent variables for FeatureGenerator
            independent_vars = derivative_config.output_grid.independent_variables
            dependent_var = 'u' # Assuming single dependent variable 'u' for now, based on output_dim=1

            feature_generator = FeatureGenerator(independent_variables=independent_vars, dependent_variable=dependent_var)
            generated_features = feature_generator.generate_features(flattened_data_for_features, derivative_config.feature_library_config)
            
            # Save generated features to a separate HDF5 file
            feature_library_object_name = f"features/{job_id}/{derivative_config.output_name}_features.h5"
            feature_library_path = await save_derivatives_to_minio(feature_library_object_name, generated_features, job_id, derivative_config.output_name + "_features")
            logger.info(f"Feature library saved to: {feature_library_path}")

        full_logs = log_capture.getvalue()
        logs_path = await save_logs_to_minio(full_logs, job_id, derivative_config.output_name)
        logger.info(f"Logs saved to: {logs_path}")

        end_time = time.time()
        duration = end_time - start_time

        derivative_result = DerivativeResult(
            job_id=job_id,
            results_path=results_path,
            logs_path=logs_path,
            config_used=derivative_config_dict,
            feature_library_path=feature_library_path # STORY-303: Add feature library path to result
        )

        update_job_status_in_db(job_id, "COMPLETED", 100, "Derivative computation completed successfully.",
                                results_path=results_path, logs_path=logs_path, completed_at=datetime.now(),
                                feature_library_path=feature_library_path) # STORY-303: Update job status with feature library path
        logger.info(f"Job {job_id} completed. Results: {derivative_result.model_dump_json(indent=2)}")

    except Exception as e:
        error_msg = f"Derivative computation job {job_id} failed: {e}"
        logger.exception(error_msg)
        full_logs = log_capture.getvalue()
        output_name_for_error = derivative_config.output_name if 'derivative_config' in locals() else f"job_{job_id}"
        logs_path = await save_logs_to_minio(full_logs, job_id, output_name_for_error + "_error")
        update_job_status_in_db(job_id, "FAILED", 0, error_msg, error_message=str(e), logs_path=logs_path, completed_at=datetime.now(),
                                feature_library_path=None) # Ensure feature_library_path is reset on failure
    finally:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        logger.info(f"Worker finished processing job: {job_id}")
