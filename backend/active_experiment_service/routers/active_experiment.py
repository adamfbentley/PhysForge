from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas, models
from ..database import get_active_exp_db
from backend.auth_service.utils import get_current_user

router = APIRouter()

@router.post("/results", response_model=schemas.ActiveExperimentResultResponse, status_code=status.HTTP_201_CREATED)
def create_active_experiment_result_entry(
    job_id: int,
    owner_id: int,
    config: schemas.ActiveExperimentConfig,
    db: Session = Depends(get_active_exp_db)
):
    # This endpoint is primarily for internal use by the worker to create an initial entry
    # The worker_task will then update it with proposed parameters, history, etc.
    db_result = crud.create_active_experiment_result(db, job_id, owner_id, config)
    return db_result

@router.get("/results/{job_id}", response_model=schemas.ActiveExperimentResultResponse)
def get_active_experiment_result(
    job_id: int,
    current_user: schemas.User = Depends(get_current_user),
    db: Session = Depends(get_active_exp_db)
):
    db_result = crud.get_active_experiment_result_by_job_id(db, job_id)
    if db_result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active Experiment Result not found")
    if db_result.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this result")
    return db_result

@router.get("/results", response_model=List[schemas.ActiveExperimentResultResponse])
def list_active_experiment_results(
    current_user: schemas.User = Depends(get_current_user),
    db: Session = Depends(get_active_exp_db),
    skip: int = 0,
    limit: int = 100
):
    owner_id = current_user.id
    results = db.query(models.ActiveExperimentResult).filter(models.ActiveExperimentResult.owner_id == owner_id).offset(skip).limit(limit).all()
    return results
