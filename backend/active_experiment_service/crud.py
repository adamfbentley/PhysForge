from sqlalchemy.orm import Session
from . import models, schemas
from typing import List, Optional, Dict, Any
from datetime import datetime

def create_active_experiment_result(db: Session, job_id: int, owner_id: int, config: schemas.ActiveExperimentConfig) -> models.ActiveExperimentResult:
    db_result = models.ActiveExperimentResult(
        job_id=job_id,
        owner_id=owner_id,
        pde_discovery_result_path=config.bayesian_optimization_config.pde_discovery_job_id if config.experiment_design_method == "BayesianOptimization" else None,
        experiment_design_method=config.experiment_design_method,
        initial_parameters=config.lhs_config.parameter_space.model_dump(mode='json') if config.lhs_config else config.bayesian_optimization_config.parameter_space.model_dump(mode='json'),
        status="PENDING"
    )
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result

def get_active_experiment_result_by_job_id(db: Session, job_id: int) -> Optional[models.ActiveExperimentResult]:
    return db.query(models.ActiveExperimentResult).filter(models.ActiveExperimentResult.job_id == job_id).first()

def update_active_experiment_result(db: Session, result_id: int,
                                    proposed_parameters_path: Optional[str] = None,
                                    optimization_history_path: Optional[str] = None,
                                    status: Optional[str] = None,
                                    error_message: Optional[str] = None) -> Optional[models.ActiveExperimentResult]:
    db_result = db.query(models.ActiveExperimentResult).filter(models.ActiveExperimentResult.id == result_id).first()
    if not db_result:
        return None
    
    if proposed_parameters_path is not None:
        db_result.proposed_parameters_path = proposed_parameters_path
    if optimization_history_path is not None:
        db_result.optimization_history_path = optimization_history_path
    if status is not None:
        db_result.status = status
    if error_message is not None:
        db_result.error_message = error_message
    db_result.updated_at = datetime.now()

    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result
