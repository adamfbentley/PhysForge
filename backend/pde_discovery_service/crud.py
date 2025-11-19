from sqlalchemy.orm import Session
from . import models, schemas
from typing import List, Optional, Dict, Any
from datetime import datetime

def create_pde_discovery_result(db: Session, job_id: int, owner_id: int, config: schemas.PDEDiscoveryConfig) -> models.PdeDiscoveryResult:
    db_result = models.PdeDiscoveryResult(
        job_id=job_id,
        owner_id=owner_id,
        discovery_algorithm=config.discovery_algorithm,
        target_variable=config.target_variable,
        candidate_features_path=config.derivative_results_path, # Path to the HDF5 with features
        # Other fields will be updated after computation
    )
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result

def get_pde_discovery_result_by_job_id(db: Session, job_id: int) -> Optional[models.PdeDiscoveryResult]:
    return db.query(models.PdeDiscoveryResult).filter(models.PdeDiscoveryResult.job_id == job_id).first()

def update_pde_discovery_result(db: Session, result_id: int,
                                    discovered_equation: Optional[str] = None,
                                    equation_metrics: Optional[Dict[str, Any]] = None,
                                    results_path: Optional[str] = None,
                                    logs_path: Optional[str] = None) -> Optional[models.PdeDiscoveryResult]:
    db_result = db.query(models.PdeDiscoveryResult).filter(models.PdeDiscoveryResult.id == result_id).first()
    if not db_result:
        return None
    
    if discovered_equation is not None:
        db_result.discovered_equation = discovered_equation
    if equation_metrics is not None:
        db_result.equation_metrics = equation_metrics
    if results_path is not None:
        db_result.results_path = results_path
    if logs_path is not None:
        db_result.logs_path = logs_path
    db_result.updated_at = datetime.now()

    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result
