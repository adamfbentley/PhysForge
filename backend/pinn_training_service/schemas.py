from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class TrainingStatus(str, Enum):
    """Status of a PINN training job."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# Job creation schemas
class PinnTrainingJobCreate(BaseModel):
    """Schema for creating a new PINN training job."""
    job_id: str
    user_id: int
    dataset_id: Optional[int] = None
    config: Dict[str, Any]
    network_architecture: Dict[str, Any]
    training_parameters: Dict[str, Any]
    physics_loss_config: Optional[Dict[str, Any]] = None

class PinnTrainingJobUpdate(BaseModel):
    """Schema for updating job status."""
    status: Optional[str] = None
    progress: Optional[int] = None
    current_epoch: Optional[int] = None
    current_loss: Optional[float] = None
    error_message: Optional[str] = None

class PinnTrainingJobResponse(BaseModel):
    """Response schema for training job."""
    id: int
    job_id: str
    user_id: int
    dataset_id: Optional[int]
    status: str
    progress: int
    config: Dict[str, Any]
    model_path: Optional[str]
    final_loss: Optional[float]
    epochs_run: Optional[int]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Model checkpoint schemas
class ModelCheckpointCreate(BaseModel):
    """Schema for creating a model checkpoint."""
    model_id: str
    job_id: str
    model_path: str
    input_dim: int
    output_dim: int
    network_type: str
    architecture: Dict[str, Any]
    final_loss: float
    metadata: Dict[str, Any] = {}

class ModelCheckpointResponse(BaseModel):
    """Response schema for model checkpoint."""
    id: int
    model_id: str
    job_id: str
    model_path: str
    input_dim: int
    output_dim: int
    network_type: str
    architecture: Dict[str, Any]
    final_loss: float
    metadata: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True

# API request/response schemas
class PinnTrainingRequest(BaseModel):
    """Request to submit a PINN training job."""
    dataset_id: int = Field(..., description="ID of the dataset to train on")
    network_architecture: Dict[str, Any] = Field(..., description="Network architecture configuration")
    training_parameters: Dict[str, Any] = Field(..., description="Training parameters")
    physics_loss_config: Optional[Dict[str, Any]] = Field(None, description="Physics loss configuration")
    
    class Config:
        schema_extra = {
            "example": {
                "dataset_id": 1,
                "network_architecture": {
                    "network_type": "MLP",
                    "output_dim": 1,
                    "layers": [20, 20],
                    "activation": "tanh"
                },
                "training_parameters": {
                    "epochs": 1000,
                    "learning_rate": 0.001,
                    "optimizer": "Adam",
                    "loss_weights": {
                        "data": 1.0,
                        "pde": 1.0
                    }
                },
                "physics_loss_config": {
                    "pde_equation": "u_t - 0.01*u_xx",
                    "independent_variables": ["x", "t"],
                    "dependent_variables": ["u"]
                }
            }
        }

class PinnTrainingSubmitResponse(BaseModel):
    """Response after submitting a training job."""
    job_id: str = Field(..., description="Unique identifier for the training job")
    status: str = Field(..., description="Current status of the job")
    message: str = Field(..., description="Human-readable message")

class PinnTrainingStatusResponse(BaseModel):
    """Detailed status of a training job."""
    job_id: str
    status: TrainingStatus
    progress: int = Field(0, ge=0, le=100)
    current_epoch: Optional[int] = None
    current_loss: Optional[float] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

class PinnTrainingResultResponse(BaseModel):
    """Final results of a completed training job."""
    job_id: str
    model_id: str
    model_path: str
    final_loss: float
    data_loss: float
    pde_loss: float
    bc_loss: float
    ic_loss: float
    regularization_loss: float
    epochs_run: int
    training_duration_seconds: float
    logs_path: Optional[str]
    
    class Config:
        from_attributes = True
