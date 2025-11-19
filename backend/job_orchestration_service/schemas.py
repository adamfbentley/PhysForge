from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class JobBase(BaseModel):
    owner_id: int

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[int] = None
    message: Optional[str] = None
    results_path: Optional[str] = None
    logs_path: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    feature_library_path: Optional[str] = None
    canonical_equation: Optional[str] = None
    equation_metrics: Optional[Dict[str, Any]] = Field(None, description="Metrics for the discovered equation (RMSE, AIC/BIC, etc.)")
    uncertainty_metrics: Optional[Dict[str, Any]] = None
    sensitivity_analysis_results_path: Optional[str] = None
    model_ranking_score: Optional[float] = None

class JobResponse(JobBase):
    id: int
    job_type: str
    config: Dict[str, Any]
    status: str
    progress: int
    message: Optional[str] = None
    results_path: Optional[str] = None
    logs_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    feature_library_path: Optional[str] = None
    canonical_equation: Optional[str] = None
    equation_metrics: Optional[Dict[str, Any]] = Field(None, description="Metrics for the discovered equation (RMSE, AIC/BIC, etc.)")
    uncertainty_metrics: Optional[Dict[str, Any]] = None
    sensitivity_analysis_results_path: Optional[str] = None
    model_ranking_score: Optional[float] = None

    class Config:
        from_attributes = True

class JobStatusUpdate(BaseModel):
    status: str
    progress: int
    message: str
    results_path: Optional[str] = None
    logs_path: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    feature_library_path: Optional[str] = None
    canonical_equation: Optional[str] = None
    equation_metrics: Optional[Dict[str, Any]] = Field(None, description="Metrics for the discovered equation (RMSE, AIC/BIC, etc.)")
    uncertainty_metrics: Optional[Dict[str, Any]] = None
    sensitivity_analysis_results_path: Optional[str] = None
    model_ranking_score: Optional[float] = None


# Job creation schemas for different job types
class PinnTrainingJobCreate(BaseModel):
    job_type: str = "pinn_training"
    config: Dict[str, Any]  # PINN training configuration

class DerivativeComputationJobCreate(BaseModel):
    job_type: str = "derivatives"
    config: Dict[str, Any]  # Derivative computation configuration

class PDEDiscoveryJobCreate(BaseModel):
    job_type: str = "pde_discovery"
    config: Dict[str, Any]  # PDE discovery configuration

class ActiveExperimentJobCreate(BaseModel):
    job_type: str = "active_experiment"
    config: Dict[str, Any]  # Active experiment configuration


# User schema for authentication (simplified version from auth service)
class User(BaseModel):
    id: int
    email: str
    is_active: bool = True
    token: Optional[str] = None  # JWT token for inter-service communication

    class Config:
        from_attributes = True
