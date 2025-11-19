from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class PdeDiscoveryResult(Base):
    __tablename__ = "pde_discovery_results"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, index=True, nullable=False) # Link to Job Orchestration Service's Job ID
    owner_id = Column(Integer, index=True, nullable=False) # Link to Auth Service's User ID
    discovery_algorithm = Column(String, nullable=False) # "SINDy", "PySR"
    target_variable = Column(String, nullable=False) # e.g., 'du_dt'
    candidate_features_path = Column(String, nullable=False) # Path to feature library HDF5
    discovered_equation = Column(Text, nullable=True)
    canonical_equation = Column(Text, nullable=True) # STORY-503: Canonicalized form of the equation
    equation_metrics = Column(JSON, nullable=True) # RMSE, AIC/BIC, etc. (STORY-501)
    uncertainty_metrics = Column(JSON, nullable=True) # STORY-405: Metrics quantifying uncertainty
    sensitivity_analysis_results_path = Column(String, nullable=True) # STORY-504: Path to sensitivity analysis results
    model_ranking_score = Column(Float, nullable=True) # STORY-502: Overall score for model ranking
    results_path = Column(String, nullable=True) # Path to full results (e.g., JSON/HDF5) in MinIO/S3
    logs_path = Column(String, nullable=True) # Path to logs in MinIO/S3
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<PdeDiscoveryResult(id={self.id}, job_id={self.job_id}, algorithm='{self.discovery_algorithm}')>"
