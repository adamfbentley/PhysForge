from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class PinnTrainingJob(Base):
    """Model for PINN training jobs."""
    __tablename__ = "pinn_training_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, index=True, nullable=False)
    dataset_id = Column(Integer, index=True, nullable=True)
    
    status = Column(String, default="queued", nullable=False)  # queued, running, completed, failed, cancelled
    progress = Column(Integer, default=0)
    
    # Configuration
    config = Column(JSON, nullable=False)
    network_architecture = Column(JSON, nullable=False)
    training_parameters = Column(JSON, nullable=False)
    physics_loss_config = Column(JSON, nullable=True)
    
    # Results
    model_path = Column(String, nullable=True)
    final_loss = Column(Float, nullable=True)
    data_loss = Column(Float, nullable=True)
    pde_loss = Column(Float, nullable=True)
    bc_loss = Column(Float, nullable=True)
    ic_loss = Column(Float, nullable=True)
    regularization_loss = Column(Float, nullable=True)
    epochs_run = Column(Integer, nullable=True)
    training_duration_seconds = Column(Float, nullable=True)
    
    # Metadata
    error_message = Column(Text, nullable=True)
    logs_path = Column(String, nullable=True)
    current_epoch = Column(Integer, default=0)
    current_loss = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<PinnTrainingJob(job_id={self.job_id}, status={self.status})>"

class ModelCheckpoint(Base):
    """Model for saved PINN checkpoints."""
    __tablename__ = "model_checkpoints"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String, unique=True, index=True, nullable=False)
    job_id = Column(String, ForeignKey("pinn_training_jobs.job_id"), nullable=False)
    
    # Model info
    model_path = Column(String, nullable=False)
    input_dim = Column(Integer, nullable=False)
    output_dim = Column(Integer, nullable=False)
    network_type = Column(String, nullable=False)
    architecture = Column(JSON, nullable=False)
    
    # Metrics
    final_loss = Column(Float, nullable=False)
    metadata = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<ModelCheckpoint(model_id={self.model_id}, job_id={self.job_id})>"
