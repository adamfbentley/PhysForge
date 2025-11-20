from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from . import models, schemas

def create_training_job(db: Session, job_data: schemas.PinnTrainingJobCreate) -> models.PinnTrainingJob:
    """Create a new PINN training job."""
    db_job = models.PinnTrainingJob(
        job_id=job_data.job_id,
        user_id=job_data.user_id,
        dataset_id=job_data.dataset_id,
        status="queued",
        config=job_data.config,
        network_architecture=job_data.network_architecture,
        training_parameters=job_data.training_parameters,
        physics_loss_config=job_data.physics_loss_config
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

def get_training_job(db: Session, job_id: str) -> Optional[models.PinnTrainingJob]:
    """Get a training job by job_id."""
    return db.query(models.PinnTrainingJob).filter(models.PinnTrainingJob.job_id == job_id).first()

def get_training_jobs_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[models.PinnTrainingJob]:
    """Get all training jobs for a user."""
    return db.query(models.PinnTrainingJob).filter(
        models.PinnTrainingJob.user_id == user_id
    ).offset(skip).limit(limit).all()

def update_training_job_status(
    db: Session,
    job_id: str,
    status: str,
    progress: Optional[int] = None,
    current_epoch: Optional[int] = None,
    current_loss: Optional[float] = None,
    error_message: Optional[str] = None
) -> Optional[models.PinnTrainingJob]:
    """Update training job status and progress."""
    db_job = get_training_job(db, job_id)
    if db_job:
        db_job.status = status
        if progress is not None:
            db_job.progress = progress
        if current_epoch is not None:
            db_job.current_epoch = current_epoch
        if current_loss is not None:
            db_job.current_loss = current_loss
        if error_message is not None:
            db_job.error_message = error_message
        
        if status == "running" and not db_job.started_at:
            db_job.started_at = datetime.utcnow()
        elif status in ["completed", "failed", "cancelled"]:
            db_job.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_job)
    return db_job

def update_training_job_results(
    db: Session,
    job_id: str,
    model_path: str,
    final_loss: float,
    data_loss: float,
    pde_loss: float,
    bc_loss: float,
    ic_loss: float,
    regularization_loss: float,
    epochs_run: int,
    training_duration_seconds: float,
    logs_path: Optional[str] = None
) -> Optional[models.PinnTrainingJob]:
    """Update training job with final results."""
    db_job = get_training_job(db, job_id)
    if db_job:
        db_job.model_path = model_path
        db_job.final_loss = final_loss
        db_job.data_loss = data_loss
        db_job.pde_loss = pde_loss
        db_job.bc_loss = bc_loss
        db_job.ic_loss = ic_loss
        db_job.regularization_loss = regularization_loss
        db_job.epochs_run = epochs_run
        db_job.training_duration_seconds = training_duration_seconds
        db_job.logs_path = logs_path
        db.commit()
        db.refresh(db_job)
    return db_job

def create_model_checkpoint(db: Session, checkpoint_data: schemas.ModelCheckpointCreate) -> models.ModelCheckpoint:
    """Create a model checkpoint record."""
    db_checkpoint = models.ModelCheckpoint(
        model_id=checkpoint_data.model_id,
        job_id=checkpoint_data.job_id,
        model_path=checkpoint_data.model_path,
        input_dim=checkpoint_data.input_dim,
        output_dim=checkpoint_data.output_dim,
        network_type=checkpoint_data.network_type,
        architecture=checkpoint_data.architecture,
        final_loss=checkpoint_data.final_loss,
        metadata=checkpoint_data.metadata
    )
    db.add(db_checkpoint)
    db.commit()
    db.refresh(db_checkpoint)
    return db_checkpoint

def get_model_checkpoint(db: Session, model_id: str) -> Optional[models.ModelCheckpoint]:
    """Get a model checkpoint by model_id."""
    return db.query(models.ModelCheckpoint).filter(models.ModelCheckpoint.model_id == model_id).first()

def delete_training_job(db: Session, job_id: str) -> bool:
    """Delete a training job."""
    db_job = get_training_job(db, job_id)
    if db_job:
        db.delete(db_job)
        db.commit()
        return True
    return False
