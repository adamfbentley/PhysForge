from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime
from typing import Optional, Dict, Any

def get_job(db: Session, job_id: int):
    return db.query(models.Job).filter(models.Job.id == job_id).first()

def get_job_by_id(db: Session, job_id: int):
    return get_job(db, job_id)

def get_jobs_by_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Job).filter(models.Job.owner_id == owner_id).offset(skip).limit(limit).all()

def create_job(db: Session, job_type: str, config: dict, owner_id: int):
    db_job = models.Job(
        owner_id=owner_id, 
        job_type=job_type, 
        config=config, 
        status="PENDING", 
        progress=0, 
        message="Job created."
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

def update_job_status(db: Session, job_id: int, status: str, progress: int, message: str,
                        results_path: Optional[str] = None, logs_path: Optional[str] = None,
                        feature_library_path: Optional[str] = None,
                        canonical_equation: Optional[str] = None,
                        equation_metrics: Optional[Dict[str, Any]] = None,
                        uncertainty_metrics: Optional[Dict[str, Any]] = None,
                        sensitivity_analysis_results_path: Optional[str] = None,
                        model_ranking_score: Optional[float] = None,
                        error_message: Optional[str] = None, started_at: Optional[datetime] = None,
                        completed_at: Optional[datetime] = None):
    db_job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not db_job:
        return None

    db_job.status = status
    db_job.progress = progress
    db_job.message = message # Update message in job itself
    db_job.updated_at = datetime.now()
    if results_path is not None: db_job.results_path = results_path
    if logs_path is not None: db_job.logs_path = logs_path
    if error_message is not None: db_job.error_message = error_message
    if started_at is not None: db_job.started_at = started_at
    if completed_at is not None: db_job.completed_at = completed_at
    if feature_library_path is not None: db_job.feature_library_path = feature_library_path
    if canonical_equation is not None: db_job.canonical_equation = canonical_equation
    if equation_metrics is not None: db_job.equation_metrics = equation_metrics
    if uncertainty_metrics is not None: db_job.uncertainty_metrics = uncertainty_metrics
    if sensitivity_analysis_results_path is not None: db_job.sensitivity_analysis_results_path = sensitivity_analysis_results_path
    if model_ranking_score is not None: db_job.model_ranking_score = model_ranking_score

    db_log = models.JobStatusLog(
        job_id=job_id,
        status=status,
        message=message
    )
    db.add(db_job)
    db.add(db_log)
    db.commit()
    db.refresh(db_job)
    return db_job
