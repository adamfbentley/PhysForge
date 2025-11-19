import logging
import json
import io
import sys
import os
import time
from datetime import datetime
from typing import Optional, Dict, Any, List

import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to allow importing backend.job_orchestration_service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.job_orchestration_service.models import Base as JobBase, Job, JobStatusLog
from backend.job_orchestration_service.schemas import JobStatusUpdate

from .config import settings
from .schemas import PDEDiscoveryConfig, PdeDiscoveryResultResponse, SindyConfig # Import SindyConfig for dummy object
from .storage_utils import load_derivative_data_from_minio, save_pde_discovery_results_to_minio, save_logs_to_minio, save_sensitivity_results_to_minio
from .sindy_discovery import SindyDiscoverer
from .pysr_discovery import PySRDiscoverer
from . import crud # Import crud for PdeDiscoveryResult
from .database import get_pde_db # CQ-PDE-001: Import the correct session getter for PDE DB
from .symbolic_utils import canonicalize_equation # STORY-503
from .model_ranking import rank_models # STORY-502
from .sensitivity_analysis import perform_sensitivity_analysis # STORY-504
from .metrics_utils import calculate_pysr_aic_bic # CQ-PDE-004

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
                            feature_library_path: Optional[str] = None, # Added for consistency with JOS Job model
                            canonical_equation: Optional[str] = None, # STORY-503
                            equation_metrics: Optional[Dict[str, Any]] = None, # BP-DISC-001
                            uncertainty_metrics: Optional[Dict[str, Any]] = None, # STORY-405
                            sensitivity_analysis_results_path: Optional[str] = None, # STORY-504
                            model_ranking_score: Optional[float] = None, # STORY-502
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
            if canonical_equation: db_job.canonical_equation = canonical_equation # STORY-503
            if equation_metrics: db_job.equation_metrics = equation_metrics # BP-DISC-001
            if uncertainty_metrics: db_job.uncertainty_metrics = uncertainty_metrics # STORY-405
            if sensitivity_analysis_results_path: db_job.sensitivity_analysis_results_path = sensitivity_analysis_results_path # STORY-504
            if model_ranking_score is not None: db_job.model_ranking_score = model_ranking_score # STORY-502

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

async def run_pde_discovery_job(job_id: int, pde_discovery_config_dict: dict, owner_id: int, dms_token: str):
    """Main function executed by the RQ worker for PDE discovery (STORY-401, STORY-402, STORY-403, STORY-404, STORY-405, STORY-501, STORY-502, STORY-503, STORY-504)."""
    logger.info(f"Worker received PDE discovery job: {job_id}")
    log_capture = LogCapture()
    sys.stdout = log_capture
    sys.stderr = log_capture

    start_time = time.time()

    discovered_equation = None
    canonical_equation = None
    equation_metrics = None
    uncertainty_metrics = None
    sensitivity_analysis_results_path = None
    model_ranking_score = None
    results_path = None
    logs_path = None

    try:
        pde_discovery_config = PDEDiscoveryConfig(**pde_discovery_config_dict)
        update_job_status_in_db(job_id, "RUNNING", 0, "Initializing PDE discovery...", started_at=datetime.now())

        # 1. Load derivative data and features from MinIO
        logger.info(f"Loading derivative data from {pde_discovery_config.derivative_results_path}...")
        loaded_data = await load_derivative_data_from_minio(pde_discovery_config.derivative_results_path, dms_token) # SEC-PDE-001
        logger.info(f"Derivative data loaded. Keys: {loaded_data.keys()}")

        # Prepare feature matrix and target derivative
        feature_matrix_list = []
        feature_names = []
        for feature_name in pde_discovery_config.candidate_features:
            if feature_name in loaded_data:
                feature_matrix_list.append(loaded_data[feature_name].flatten())
                feature_names.append(feature_name)
            else:
                raise ValueError(f"Candidate feature '{feature_name}' not found in loaded derivative data.")
        
        if not feature_matrix_list:
            raise ValueError("No valid candidate features found for PDE discovery.")

        feature_matrix = np.vstack(feature_matrix_list).T # Shape (num_samples, num_features)
        
        if pde_discovery_config.target_variable not in loaded_data:
            raise ValueError(f"Target variable '{pde_discovery_config.target_variable}' not found in loaded derivative data.")
        target_derivative = loaded_data[pde_discovery_config.target_variable].flatten()

        discovery_results = {}
        if pde_discovery_config.discovery_algorithm == "SINDy":
            if not pde_discovery_config.sindy_config:
                raise ValueError("SINDy configuration is required for SINDy algorithm.")
            sindy_discoverer = SindyDiscoverer(
                pde_discovery_config.sindy_config,
                pde_discovery_config.independent_variables,
                pde_discovery_config.dependent_variable
            )
            discovery_results = sindy_discoverer.discover_pde(
                feature_matrix=feature_matrix,
                feature_names=feature_names,
                target_derivative=target_derivative,
                canonicalize_equation_flag=pde_discovery_config.canonicalize_equation # STORY-503
            )
        elif pde_discovery_config.discovery_algorithm == "PySR":
            if not pde_discovery_config.pysr_config:
                raise ValueError("PySR configuration is required for PySR algorithm.")
            pysr_discoverer = PySRDiscoverer(
                pde_discovery_config.pysr_config,
                pde_discovery_config.independent_variables,
                pde_discovery_config.dependent_variable
            )
            discovery_results = pysr_discoverer.discover_pde(
                feature_matrix=feature_matrix,
                feature_names=feature_names,
                target_derivative=target_derivative,
                canonicalize_equation_flag=pde_discovery_config.canonicalize_equation # STORY-503
            )
        else:
            raise ValueError(f"Unsupported PDE discovery algorithm: {pde_discovery_config.discovery_algorithm}")

        discovered_equation = discovery_results.get("discovered_equation")
        canonical_equation = discovery_results.get("canonical_equation")
        equation_metrics = discovery_results.get("equation_metrics")
        uncertainty_metrics = discovery_results.get("uncertainty_metrics")
        all_pysr_equations = discovery_results.get("all_pysr_equations", []) # For PySR ranking

        # STORY-502: Model Ranking
        if pde_discovery_config.ranking_criteria and (pde_discovery_config.discovery_algorithm == "PySR" and all_pysr_equations):
            logger.info("Performing model ranking...")
            # For PySR, we rank all discovered equations. For SINDy, typically one best equation is returned.
            # We need to ensure each entry in all_pysr_equations has 'equation_metrics'
            models_to_rank = []
            for eq_data in all_pysr_equations:
                model_metrics = {
                    "rmse": np.sqrt(eq_data.get('loss', np.inf)),
                    "complexity": eq_data.get('complexity', np.inf),
                    "r_squared": eq_data.get('r2', -np.inf)
                }
                # Calculate AIC/BIC for each PySR equation (CQ-PDE-004)
                n_samples = feature_matrix.shape[0]
                aic_bic = calculate_pysr_aic_bic(
                    n_samples=n_samples,
                    rss=eq_data.get('loss', np.inf) * n_samples,
                    k_params=eq_data.get('complexity', np.inf)
                ) 
                model_metrics.update(aic_bic)
                
                models_to_rank.append({
                    "discovered_equation": eq_data.get('equation'),
                    "equation_metrics": model_metrics
                })
            
            ranked_models = rank_models(models_to_rank, pde_discovery_config.ranking_criteria)
            if ranked_models:
                # The top-ranked model becomes the primary discovered equation
                top_model = ranked_models[0]
                discovered_equation = top_model.get("discovered_equation")
                equation_metrics = top_model.get("equation_metrics")
                model_ranking_score = top_model.get("model_ranking_score")
                if pde_discovery_config.canonicalize_equation:
                    canonical_equation = canonicalize_equation(discovered_equation, pde_discovery_config.independent_variables, pde_discovery_config.dependent_variable)
                logger.info(f"Top ranked equation: {discovered_equation} with score {model_ranking_score}")
        elif pde_discovery_config.ranking_criteria and pde_discovery_config.discovery_algorithm == "SINDy":
            # For SINDy, if ranking is requested, we can assign a score to the single best model
            # based on its metrics. For simplicity, we'll just use the first criterion.
            if equation_metrics and pde_discovery_config.ranking_criteria:
                first_criterion = pde_discovery_config.ranking_criteria[0]
                is_descending = False
                if first_criterion.startswith('-'):
                    is_descending = True
                    first_criterion = first_criterion[1:]
                
                score_value = equation_metrics.get(first_criterion)
                if score_value is not None:
                    model_ranking_score = -score_value if is_descending else score_value
                    logger.info(f"SINDy model assigned ranking score {model_ranking_score} based on '{first_criterion}'.")


        # 2. Save results and logs
        output_object_name = f"pde_equations/{job_id}/{pde_discovery_config.output_name}.json"
        results_path = await save_pde_discovery_results_to_minio(output_object_name, discovery_results, job_id, pde_discovery_config.output_name, dms_token) # SEC-PDE-001
        logger.info(f"PDE discovery results saved to: {results_path}")

        full_logs = log_capture.getvalue()
        logs_path = await save_logs_to_minio(full_logs, job_id, pde_discovery_config.output_name, dms_token) # SEC-PDE-001
        logger.info(f"Logs saved to: {logs_path}")

        # STORY-504: Sensitivity Analysis
        if pde_discovery_config.perform_sensitivity_analysis and discovered_equation:
            logger.info("Performing sensitivity analysis...")
            sensitivity_results = perform_sensitivity_analysis(
                discovered_equation,
                pde_discovery_config.independent_variables,
                pde_discovery_config.dependent_variable,
                loaded_data, # Pass all loaded data for numerical perturbation
                pde_discovery_config.sensitivity_analysis_config
            )
            sensitivity_object_name = f"sensitivity/{job_id}/{pde_discovery_config.output_name}_sensitivity.json"
            sensitivity_analysis_results_path = await save_sensitivity_results_to_minio(
                sensitivity_object_name, sensitivity_results, job_id, pde_discovery_config.output_name + "_sensitivity", dms_token # SEC-PDE-001
            )
            logger.info(f"Sensitivity analysis results saved to: {sensitivity_analysis_results_path}")


        end_time = time.time()
        duration = end_time - start_time

        # Update PDE Discovery Result in its own DB
        db = next(get_pde_db()) # CQ-PDE-001: Use the PDE Discovery Service's DB session
        pde_result_db = crud.create_pde_discovery_result(db, job_id, owner_id, pde_discovery_config)
        crud.update_pde_discovery_result(
            db,
            pde_result_db.id,
            discovered_equation=discovered_equation,
            canonical_equation=canonical_equation, # STORY-503
            equation_metrics=equation_metrics, # STORY-501, BP-DISC-001
            uncertainty_metrics=uncertainty_metrics, # STORY-405
            sensitivity_analysis_results_path=sensitivity_analysis_results_path, # STORY-504
            model_ranking_score=model_ranking_score, # STORY-502
            results_path=results_path,
            logs_path=logs_path
        )
        db.close()

        update_job_status_in_db(job_id, "COMPLETED", 100, "PDE discovery completed successfully.",
                                results_path=results_path, logs_path=logs_path, completed_at=datetime.now(),
                                feature_library_path=pde_discovery_config.derivative_results_path, # Store path to features used
                                canonical_equation=canonical_equation,
                                equation_metrics=equation_metrics, # BP-DISC-001
                                uncertainty_metrics=uncertainty_metrics,
                                sensitivity_analysis_results_path=sensitivity_analysis_results_path,
                                model_ranking_score=model_ranking_score)
        logger.info(f"Job {job_id} completed. Discovered equation: {discovered_equation}")

    except Exception as e:
        error_msg = f"PDE discovery job {job_id} failed: {e}"
        logger.exception(error_msg)
        full_logs = log_capture.getvalue()
        output_name_for_error = pde_discovery_config.output_name if 'pde_discovery_config' in locals() else f"job_{job_id}"
        logs_path = await save_logs_to_minio(full_logs, job_id, output_name_for_error + "_error", dms_token if 'dms_token' in locals() else None) # SEC-PDE-001
        update_job_status_in_db(job_id, "FAILED", 0, error_msg, error_message=str(e), logs_path=logs_path, completed_at=datetime.now(),
                                feature_library_path=pde_discovery_config.derivative_results_path if 'pde_discovery_config' in locals() else None,
                                canonical_equation=None, equation_metrics=None, uncertainty_metrics=None, sensitivity_analysis_results_path=None, model_ranking_score=None)
    finally:
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        logger.info(f"Worker finished processing job: {job_id}")
