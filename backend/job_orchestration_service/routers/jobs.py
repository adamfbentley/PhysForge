from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Path
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from redis import Redis
from rq import Queue

from .. import crud, schemas, models
from ..database import get_db
from ..security import get_current_active_user
from ..config import settings
from ..storage_utils import get_object_content_from_minio

# Import new job creation schemas
from ..schemas import PinnTrainingJobCreate, DerivativeComputationJobCreate, PDEDiscoveryJobCreate, ActiveExperimentJobCreate

# Initialize Redis Queue
redis_conn = Redis.from_url(settings.REDIS_URL)
job_queue = Queue(connection=redis_conn)

router = APIRouter()

@router.post("/pinn-training", response_model=schemas.JobResponse, status_code=status.HTTP_202_ACCEPTED,
             summary="Submit a new PINN training job (Authenticated)")
async def submit_pinn_training_job(
    job_create_data: PinnTrainingJobCreate,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_job = crud.create_job(db=db, job_type=job_create_data.job_type, config=job_create_data.config.model_dump(mode='json'), owner_id=current_user.id)

    rq_job = job_queue.enqueue(
        'backend.pinn_training_service.worker_task.run_pinn_training_job',
        job_id=db_job.id,
        pinn_config_dict=job_create_data.config.model_dump(mode='json'),
        user_id=current_user.id,
        dms_token=current_user.token,
        job_timeout='2h'
    )
    
    db_job.rq_job_id = rq_job.id
    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    return db_job

# New endpoint for derivative computation jobs (STORY-301, STORY-302, STORY-801)
@router.post("/derivatives", response_model=schemas.JobResponse, status_code=status.HTTP_202_ACCEPTED,
             summary="Submit a new derivative computation job (Authenticated)")
async def submit_derivative_job(
    job_create_data: DerivativeComputationJobCreate,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_job = crud.create_job(db=db, job_type=job_create_data.job_type, config=job_create_data.config.model_dump(mode='json'), owner_id=current_user.id)

    rq_job = job_queue.enqueue(
        'backend.derivative_feature_service.worker_task.run_derivative_job',
        job_id=db_job.id,
        derivative_config_dict=job_create_data.config.model_dump(mode='json'),
        user_id=current_user.id,
        dms_token=current_user.token,
        job_timeout='1h'
    )
    
    db_job.rq_job_id = rq_job.id
    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    return db_job

# STORY-401, STORY-801: New endpoint for PDE discovery jobs
@router.post("/pde-discovery", response_model=schemas.JobResponse, status_code=status.HTTP_202_ACCEPTED,
             summary="Submit a new PDE discovery job (Authenticated)")
async def submit_pde_discovery_job(
    job_create_data: PDEDiscoveryJobCreate,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_job = crud.create_job(db=db, job_type=job_create_data.job_type, config=job_create_data.config.model_dump(mode='json'), owner_id=current_user.id)

    rq_job = job_queue.enqueue(
        'backend.pde_discovery_service.worker_task.run_pde_discovery_job',
        job_id=db_job.id,
        pde_discovery_config_dict=job_create_data.config.model_dump(mode='json'),
        owner_id=current_user.id,
        dms_token=current_user.token,
        job_timeout='4h'
    )
    
    db_job.rq_job_id = rq_job.id
    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    return db_job

# STORY-601, STORY-602, STORY-603, STORY-604, STORY-801: New endpoint for Active Experiment Design jobs
@router.post("/active-experiment", response_model=schemas.JobResponse, status_code=status.HTTP_202_ACCEPTED,
             summary="Submit a new active experiment design job (Authenticated)")
async def submit_active_experiment_job(
    job_create_data: ActiveExperimentJobCreate,
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_job = crud.create_job(db=db, job_type=job_create_data.job_type, config=job_create_data.config.model_dump(mode='json'), owner_id=current_user.id)

    rq_job = job_queue.enqueue(
        'backend.active_experiment_service.worker_task.run_active_experiment_job',
        job_id=db_job.id,
        active_experiment_config_dict=job_create_data.config.model_dump(mode='json'),
        owner_id=current_user.id,
        dms_token=current_user.token,
        job_timeout='1h'
    )
    
    db_job.rq_job_id = rq_job.id
    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    return db_job

@router.get("/{job_id}", response_model=schemas.JobResponse,
            summary="Retrieve the status and details of a specific job (Authenticated)")
async def get_job_status(
    job_id: int = Path(..., description="The ID of the job to retrieve"),
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_job = crud.get_job_by_id(db, job_id=job_id)
    if not db_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if db_job.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this job")
    return db_job

@router.get("/", response_model=List[schemas.JobResponse],
            summary="Retrieve a list of all jobs owned by the current user (Authenticated)")
async def list_jobs(
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    jobs = crud.get_jobs_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
    return jobs

@router.get("/{job_id}/logs", summary="Retrieve job logs (Authenticated)")
async def get_job_logs(
    job_id: int = Path(..., description="The ID of the job to retrieve logs for"),
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_job = crud.get_job_by_id(db, job_id=job_id)
    if not db_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if db_job.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this job")
    
    if not db_job.logs_path:
        return {"message": "No logs available yet or logs not stored.", "logs": []}
    
    try:
        logs_content_bytes = await get_object_content_from_minio(db_job.logs_path)
        return {"message": "Logs retrieved successfully.", "logs": logs_content_bytes.decode('utf-8').splitlines()}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve logs from storage: {e}")
