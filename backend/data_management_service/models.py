from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    owner_id = Column(Integer, index=True, nullable=False) # Link to Auth Service's User ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    versions = relationship("DatasetVersion", back_populates="dataset", cascade="all, delete-orphan", order_by="DatasetVersion.version_number")

    def __repr__(self):
        return f"<Dataset(id={self.id}, name='{self.name}', owner_id={self.owner_id})>"

class DatasetVersion(Base):
    __tablename__ = "dataset_versions"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    storage_path = Column(String, nullable=False) # Path in MinIO/S3 bucket
    metadata = Column(JSON, nullable=True) # Extracted metadata (JSONB in PostgreSQL)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    uploader_id = Column(Integer, nullable=False) # Link to Auth Service's User ID
    is_latest = Column(Boolean, default=True, nullable=False)

    dataset = relationship("Dataset", back_populates="versions")

    def __repr__(self):
        return f"<DatasetVersion(id={self.id}, dataset_id={self.dataset_id}, version={self.version_number})>"
