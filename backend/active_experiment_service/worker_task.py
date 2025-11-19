import logging
import json
import io
import sys
import os
import time
from datetime import datetime
from typing import Optional, Dict, Any, List

import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to allow importing backend.job_orchestration_service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.job_orchestration_service.models import Base as JobBase, Job, JobStatusLog
from backend.job_orchestration_service.schemas import JobStatusUpdate

from .config import settings
from .schemas import ActiveExperimentConfig, ActiveExperimentResultResponse, LHSConfig, BayesianOptimizationConfig, ParameterSpaceDefinition, OptimizationHistoryEntry
from .storage_utils import load_pde_discovery_result_from_minio, save_proposed_parameters_to_minio, save_optimization_history_to_minio, save_logs_to_minio
from .experiment_designer import LatinHypercubeSampler, BayesianOptimizer
from . import crud # Import crud for ActiveExperimentResult
from .database import get_active_exp_db # Import the correct session getter for Active Experiment DB

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
                            feature_library_path: Optional[str] = None,
                            canonical_equation: Optional[str] = None,
                            equation_metrics: Optional[Dict[str, Any]] = None,
                            uncertainty_metrics: Optional[Dict[str, Any]] = None,
                            sensitivity_analysis_results_path: Optional[str] = None,
                            model_ranking_score: Optional[float] = None,
                            active_experiment_results_path: Optional[str] = None,
                            optimization_history_path: Optional[str] = None,
                            error_message: Optional[str] = None, started_at: Optional[datetime] = None,
                            completed_at: Optional[datetime] = None):
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
            if feature_library_path: db_job.feature_library_path = feature_library_path
            if canonical_equation: db_job.canonical_equation = canonical_equation
            if equation_metrics: db_job.equation_metrics = equation_metrics
            if uncertainty_metrics: db_job.uncertainty_metrics = uncertainty_metrics
            if sensitivity_analysis_results_path: db_job.sensitivity_analysis_results_path = sensitivity_analysis_results_path
            if model_ranking_score is not None: db_job.model_ranking_score = model_ranking_score
            if active_experiment_results_path is not None: db_job.active_experiment_results_path = active_experiment_results_path
            if optimization_history_path is not None: db_job.optimization_history_path = optimization_history_path

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

async def run_active_experiment_job(job_id: int, active_experiment_config_dict: dict, owner_id: int, dms_token: str):
    """Main function executed by the RQ worker for active experiment design (STORY-601, STORY-602, STORY-603, STORY-604)."""
    logger.info(f"Worker received active experiment design job: {job_id}")
    log_capture = LogCapture()
    sys.stdout = log_capture
    sys.stderr = log_capture

    start_time = time.time()

    proposed_parameters_path = None
    optimization_history_path = None
    pde_discovery_result_path = None

    try:
        active_exp_config = ActiveExperimentConfig(**active_experiment_config_dict)
        update_job_status_in_db(job_id, "RUNNING", 0, "Initializing active experiment design...", started_at=datetime.now())

        # Create initial entry in Active Experiment Service's DB
        db_active_exp = next(get_active_exp_db())
        active_exp_result_db = crud.create_active_experiment_result(db_active_exp, job_id, owner_id, active_exp_config)
        db_active_exp.close()

        if active_exp_config.experiment_design_method == "LHS":
            lhs_config = active_exp_config.lhs_config
            if not lhs_config:
                raise ValueError("LHS configuration is missing.")
            
            sampler = LatinHypercubeSampler(lhs_config)
            proposed_df = sampler.generate_samples()
            
            # Save proposed parameters
            output_object_name = f"lhs_parameters/{job_id}/{active_exp_config.output_name}_lhs_params.h5"
            proposed_parameters_path = await save_proposed_parameters_to_minio(output_object_name, proposed_df, dms_token)
            logger.info(f"LHS proposed parameters saved to: {proposed_parameters_path}")

        elif active_exp_config.experiment_design_method == "BayesianOptimization":
            bo_config = active_exp_config.bayesian_optimization_config
            if not bo_config:
                raise ValueError("Bayesian Optimization configuration is missing.")
            
            # 1. Load PDE discovery result for informing BO
            # The pde_discovery_job_id is used to construct the path to the PDE result JSON
            # Assuming PDE discovery results are stored in 'pde-discovery-results' bucket
            pde_discovery_result_object_name = f"pde_equations/{bo_config.pde_discovery_job_id}/{bo_config.pde_discovery_job_id}.json"
            pde_discovery_result = await load_pde_discovery_result_from_minio(f"/pde-discovery-results/{pde_discovery_result_object_name}", dms_token)
            pde_discovery_result_path = f"/pde-discovery-results/{pde_discovery_result_object_name}"
            logger.info(f"Loaded PDE discovery result for job {bo_config.pde_discovery_job_id}.")

            optimizer = BayesianOptimizer(bo_config, pde_discovery_result)

            # Generate initial samples
            initial_samples_df = pd.DataFrame()
            if bo_config.initial_design_method == "LHS":
                lhs_sampler = LatinHypercubeSampler(LHSConfig(num_samples=bo_config.num_initial_samples, parameter_space=bo_config.parameter_space))
                initial_samples_df = lhs_sampler.generate_samples()
            elif bo_config.initial_design_method == "Random":
                # Generate random samples within bounds
                random_samples = {}
                for name, bounds in bo_config.parameter_space.continuous_params.items():
                    random_samples[name] = np.random.uniform(bounds[0], bounds[1], size=bo_config.num_initial_samples)
                for name, values in bo_config.parameter_space.categorical_params.items():
                    random_samples[name] = np.random.choice(values, size=bo_config.num_initial_samples)
                initial_samples_df = pd.DataFrame(random_samples)
            
            # For initial samples, we need 'observed_metric' to train the GP.
            initial_samples_df['observed_metric'] = initial_samples_df.apply(lambda row: optimizer.objective_function(row.to_dict()), axis=1)
            logger.info(f"Generated {bo_config.num_initial_samples} initial samples for BO.")

            current_data = initial_samples_df.copy()
            proposed_parameters_list = []
            proposed_parameters_list.append(initial_samples_df.to_dict(orient='records'))

            for i in range(bo_config.num_iterations):
                logger.info(f"Bayesian Optimization iteration {i+1}/{bo_config.num_iterations}...")
                new_points = optimizer.propose_next_points(current_data, iteration=i+1)
                
                # For this sprint, we simulate the 'observed_metric' for new points
                for point in new_points:
                    point_df = pd.DataFrame([point])
                    point_df['observed_metric'] = point_df.apply(lambda row: optimizer.objective_function(row.to_dict()), axis=1)
                    current_data = pd.concat([current_data, point_df], ignore_index=True)
                
                proposed_parameters_list.append(new_points)
                update_job_status_in_db(job_id, "RUNNING", int(((i+1)/bo_config.num_iterations)*100), f"BO Iteration {i+1} complete.")
            
            proposed_df = pd.DataFrame([item for sublist in proposed_parameters_list for item in sublist])

            # Save proposed parameters and optimization history
            output_object_name = f"bo_parameters/{job_id}/{active_exp_config.output_name}_bo_params.h5"
            proposed_parameters_path = await save_proposed_parameters_to_minio(output_object_name, proposed_df, dms_token)
            logger.info(f"BO proposed parameters saved to: {proposed_parameters_path}")

            history_object_name = f"bo_history/{job_id}/{active_exp_config.output_name}_bo_history.json"
            optimization_history_path = await save_optimization_history_to_minio(history_object_name, optimizer.get_optimization_history(), dms_token)
            logger.info(f"BO optimization history saved to: {optimization_history_path}")

        else:
            raise ValueError(f"Unsupported experiment design method: {active_exp_config.experiment_design_method}")

        full_logs = log_capture.getvalue()
        logs_path = await save_logs_to_minio(full_logs, job_id, active_exp_config.output_name, dms_token)
        logger.info(f"Logs saved to: {logs_path}")

        end_time = time.time()
        duration = end_time - start_time

        # Update Active Experiment Result in its own DB
        db_active_exp = next(get_active_exp_db())
        crud.update_active_experiment_result(
            db_active_exp,
            active_exp_result_db.id,
            proposed_parameters_path=proposed_parameters_path,
            optimization_history_path=optimization_history_path,
            status="COMPLETED"
        )
        db_active_exp.close()

        update_job_status_in_db(job_id, "COMPLETED", 100, "Active experiment design completed successfully.",
                                active_experiment_results_path=proposed_parameters_path, logs_path=logs_path, completed_at=datetime.now(),
                                optimization_history_path=optimization_history_path)
        logger.info(f"Job {job_id} completed. Proposed parameters path: {proposed_parameters_path}")

    except Exception as e:
        error_msg = f"Active experiment design job {job_id} failed: {e}"
        logger.exception(error_msg)
        full_logs = log_capture.getvalue()
        output_name_for_error = active_exp_config.output_name if 'active_exp_config' in locals() else f"job_{job_id}"
        logs_path = await save_logs_to_minio(full_logs, job_id, output_name_for_error + "_error", dms_token if 'dms_token' in locals() else None)
        update_job_status_in_db(job_id, "FAILED", 0, error_msg, error_message=str(e), logs_path=logs_path, completed_at=datetime.now(),
                                active_experiment_results_path=None, optimization_history_path=None)
    finally:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        logger.info(f"Worker finished processing job: {job_id}")
