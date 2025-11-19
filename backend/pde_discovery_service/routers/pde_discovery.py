from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas, models
from ..database import get_pde_db # CQ-PDE-001: Changed from get_db
from backend.job_orchestration_service.security import get_current_user # CQ-PDE-003

router = APIRouter()

@router.post("/results", response_model=schemas.PdeDiscoveryResultResponse, status_code=status.HTTP_201_CREATED)
def create_pde_result_entry(
    job_id: int,
    owner_id: int,
    config: schemas.PDEDiscoveryConfig,
    db: Session = Depends(get_pde_db) # CQ-PDE-001: Changed from get_db
):
    # This endpoint is primarily for internal use by the worker to create an initial entry
    # The worker_task will then update it with discovered equation, metrics, etc.
    db_result = crud.create_pde_discovery_result(db, job_id, owner_id, config)
    return db_result

@router.get("/results/{job_id}", response_model=schemas.PdeDiscoveryResultResponse)
def get_pde_result(
    job_id: int,
    db: Session = Depends(get_pde_db) # CQ-PDE-001: Changed from get_db
):
    db_result = crud.get_pde_discovery_result_by_job_id(db, job_id)
    if db_result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDE Discovery Result not found")
    return db_result

# CQ-PDE-003: Secured list_pde_results endpoint
@router.get("/results", response_model=List[schemas.PdeDiscoveryResultResponse])
def list_pde_results(
    current_user: schemas.User = Depends(get_current_user), # Get owner_id from authenticated user
    db: Session = Depends(get_pde_db),
    skip: int = 0,
    limit: int = 100
):
    results = db.query(models.PdeDiscoveryResult).filter(models.PdeDiscoveryResult.owner_id == current_user.id).offset(skip).limit(limit).all()
    return results
