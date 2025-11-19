from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, index=True, nullable=False) # Link to Job Orchestration Service's Job ID
    owner_id = Column(Integer, index=True, nullable=False) # Link to Auth Service's User ID
    report_type = Column(String, nullable=False) # e.g., "json_summary", "jupyter_notebook"
    report_path = Column(String, nullable=False) # Path to the generated report in MinIO/S3
    status = Column(String, default="PENDING", nullable=False) # PENDING, GENERATED, FAILED
    metadata = Column(JSON, nullable=True) # Additional report-specific metadata
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Report(id={self.id}, job_id={self.job_id}, type='{self.report_type}')>"
