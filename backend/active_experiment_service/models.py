from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class ActiveExperimentResult(Base):
    __tablename__ = "active_experiment_results"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, index=True, nullable=False) # Link to Job Orchestration Service's Job ID
    owner_id = Column(Integer, index=True, nullable=False) # Link to Auth Service's User ID
    pde_discovery_result_path = Column(String, nullable=True) # Path to PDE discovery result JSON in MinIO
    experiment_design_method = Column(String, nullable=False) # "LHS", "BayesianOptimization"
    initial_parameters = Column(JSON, nullable=True) # JSON of initial parameter space definition
    proposed_parameters_path = Column(String, nullable=True) # Path to HDF5/JSON of proposed parameters
    optimization_history_path = Column(String, nullable=True) # Path to JSON of optimization steps/metrics
    status = Column(String, default="PENDING", nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ActiveExperimentResult(id={self.id}, job_id={self.job_id}, method='{self.experiment_design_method}')>"
