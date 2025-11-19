from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, index=True, nullable=False)
    job_type = Column(String, nullable=False)  # Type of job (pinn_training, derivatives, pde_discovery, active_experiment)
    config = Column(JSON, nullable=False)  # Job configuration stored as JSON
    rq_job_id = Column(String, nullable=True)  # RQ job ID for tracking
    status = Column(String, default="PENDING", nullable=False)
    progress = Column(Integer, default=0, nullable=False) # 0-100
    message = Column(String, nullable=True)
    results_path = Column(String, nullable=True) # Path to final results in object storage
    logs_path = Column(String, nullable=True) # Path to logs in object storage
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    feature_library_path = Column(String, nullable=True) # Path to the feature library used
    canonical_equation = Column(Text, nullable=True) # STORY-503: Canonicalized form of the equation
    equation_metrics = Column(JSON, nullable=True) # BP-DISC-001: RMSE, AIC/BIC, etc.
    uncertainty_metrics = Column(JSON, nullable=True) # STORY-405: Metrics quantifying uncertainty
    sensitivity_analysis_results_path = Column(String, nullable=True) # STORY-504: Path to sensitivity analysis results
    model_ranking_score = Column(Float, nullable=True) # STORY-502: Overall score for model ranking

    def __repr__(self):
        return f"<Job(id={self.id}, job_type='{self.job_type}', status='{self.status}')>"

class JobStatusLog(Base):
    __tablename__ = "job_status_logs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    status = Column(String, nullable=False)
    message = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
