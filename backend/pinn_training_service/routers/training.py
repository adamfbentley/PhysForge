from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import uuid
import logging

from .. import crud, models, schemas
from ..database import get_db
from ..security import get_current_user, User
from ..worker_task import enqueue_pinn_training_job

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=schemas.PinnTrainingSubmitResponse, status_code=status.HTTP_201_CREATED)
async def submit_training_job(
    request: schemas.PinnTrainingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> schemas.PinnTrainingSubmitResponse:
    """
    Submit a new PINN training job.
    
    The job will be queued and processed by a worker.
    """
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Create job record in database
        job_create = schemas.PinnTrainingJobCreate(
            job_id=job_id,
            user_id=current_user.id,
            dataset_id=request.dataset_id,
            config={
                "network_architecture": request.network_architecture,
                "training_parameters": request.training_parameters,
                "physics_loss_config": request.physics_loss_config
            },
            network_architecture=request.network_architecture,
            training_parameters=request.training_parameters,
            physics_loss_config=request.physics_loss_config
        )
        
        db_job = crud.create_training_job(db, job_create)
        
        # Enqueue job for processing
        enqueue_pinn_training_job(job_id, request.dataset_id, request.dict())
        
        logger.info(f"PINN training job {job_id} submitted by user {current_user.id}")
        
        return schemas.PinnTrainingSubmitResponse(
            job_id=job_id,
            status="queued",
            message="Training job submitted successfully and queued for processing"
        )
        
    except Exception as e:
        logger.error(f"Error submitting training job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit training job: {str(e)}"
        )

@router.get("/{job_id}", response_model=schemas.PinnTrainingJobResponse)
async def get_training_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> schemas.PinnTrainingJobResponse:
    """Get details of a specific training job."""
    db_job = crud.get_training_job(db, job_id)
    
    if not db_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training job {job_id} not found"
        )
    
    # Check authorization
    if db_job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this training job"
        )
    
    return db_job

@router.get("/{job_id}/status", response_model=schemas.PinnTrainingStatusResponse)
async def get_training_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> schemas.PinnTrainingStatusResponse:
    """Get the current status of a training job."""
    db_job = crud.get_training_job(db, job_id)
    
    if not db_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training job {job_id} not found"
        )
    
    # Check authorization
    if db_job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this training job"
        )
    
    return schemas.PinnTrainingStatusResponse(
        job_id=db_job.job_id,
        status=db_job.status,
        progress=db_job.progress,
        current_epoch=db_job.current_epoch,
        current_loss=db_job.current_loss,
        created_at=db_job.created_at,
        started_at=db_job.started_at,
        completed_at=db_job.completed_at,
        error_message=db_job.error_message
    )

@router.get("/{job_id}/result", response_model=schemas.PinnTrainingResultResponse)
async def get_training_result(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> schemas.PinnTrainingResultResponse:
    """Get the final result of a completed training job."""
    db_job = crud.get_training_job(db, job_id)
    
    if not db_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training job {job_id} not found"
        )
    
    # Check authorization
    if db_job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this training job"
        )
    
    if db_job.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Training job {job_id} is not completed. Current status: {db_job.status}"
        )
    
    # Get model checkpoint
    model_checkpoint = crud.get_model_checkpoint(db, f"pinn_model_{job_id}")
    
    return schemas.PinnTrainingResultResponse(
        job_id=db_job.job_id,
        model_id=model_checkpoint.model_id if model_checkpoint else f"pinn_model_{job_id}",
        model_path=db_job.model_path,
        final_loss=db_job.final_loss,
        data_loss=db_job.data_loss,
        pde_loss=db_job.pde_loss,
        bc_loss=db_job.bc_loss,
        ic_loss=db_job.ic_loss,
        regularization_loss=db_job.regularization_loss,
        epochs_run=db_job.epochs_run,
        training_duration_seconds=db_job.training_duration_seconds,
        logs_path=db_job.logs_path
    )

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_training_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a running training job."""
    db_job = crud.get_training_job(db, job_id)
    
    if not db_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training job {job_id} not found"
        )
    
    # Check authorization
    if db_job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this training job"
        )
    
    if db_job.status in ["completed", "failed", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job with status: {db_job.status}"
        )
    
    # Update status to cancelled
    crud.update_training_job_status(db, job_id, "cancelled", error_message="Cancelled by user")
    
    logger.info(f"Training job {job_id} cancelled by user {current_user.id}")

@router.get("/", response_model=List[schemas.PinnTrainingJobResponse])
async def list_training_jobs(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[schemas.PinnTrainingJobResponse]:
    """List all training jobs for the current user."""
    db_jobs = crud.get_training_jobs_by_user(db, current_user.id, skip=skip, limit=limit)
    return db_jobs
