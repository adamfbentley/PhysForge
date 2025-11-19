from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class TrainingMetrics(BaseModel):
    final_loss: float
    data_loss: float
    pde_loss: float
    bc_loss: float
    ic_loss: float
    regularization_loss: float = Field(0.0, description="Value of the regularization loss at the end of training.") # STORY-205
    epochs_run: int = Field(..., description="Number of epochs the training ran for.")
    training_duration_seconds: float = Field(..., description="Total duration of the training in seconds.")

class PinnTrainingResult(BaseModel):
    job_id: int = Field(..., description="ID of the job that produced this result.")
    model_path: str = Field(..., description="Path to the saved trained model in object storage.")
    metrics: TrainingMetrics = Field(..., description="Key metrics from the training process.")
    logs_path: Optional[str] = Field(None, description="Path to the training logs in object storage.")
    config_used: Dict[str, Any] = Field(..., description="The full configuration used for this training run.")
    generated_at: datetime = Field(default_factory=datetime.now, description="Timestamp when the result was generated.")
