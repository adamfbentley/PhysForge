from sqlalchemy.orm import Session
from sqlalchemy import desc
from . import models, schemas
from typing import List, Optional, Dict, Any

def create_dataset(db: Session, dataset: schemas.DatasetCreate, owner_id: int):
    db_dataset = models.Dataset(
        name=dataset.name,
        description=dataset.description,
        owner_id=owner_id
    )
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)
    return db_dataset

def get_dataset_by_id(db: Session, dataset_id: int):
    return db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()

def get_datasets_by_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Dataset).filter(models.Dataset.owner_id == owner_id).offset(skip).limit(limit).all()

def get_dataset_by_name_and_owner(db: Session, name: str, owner_id: int):
    return db.query(models.Dataset).filter(models.Dataset.name == name, models.Dataset.owner_id == owner_id).first()

def create_dataset_version(
    db: Session,
    dataset_id: int,
    storage_path: str,
    metadata: Optional[Dict[str, Any]],
    uploader_id: int
):
    # Set all existing versions of this dataset to not be the latest
    db.query(models.DatasetVersion).filter(models.DatasetVersion.dataset_id == dataset_id).update({"is_latest": False})

    # Determine the next version number
    latest_version = db.query(models.DatasetVersion).filter(models.DatasetVersion.dataset_id == dataset_id)
    latest_version = latest_version.order_by(desc(models.DatasetVersion.version_number)).first()
    version_number = (latest_version.version_number + 1) if latest_version else 1

    db_dataset_version = models.DatasetVersion(
        dataset_id=dataset_id,
        version_number=version_number,
        storage_path=storage_path,
        metadata=metadata,
        uploader_id=uploader_id,
        is_latest=True
    )
    db.add(db_dataset_version)
    db.commit()
    db.refresh(db_dataset_version)
    return db_dataset_version

def get_latest_dataset_version(db: Session, dataset_id: int):
    return db.query(models.DatasetVersion).filter(models.DatasetVersion.dataset_id == dataset_id, models.DatasetVersion.is_latest == True).first()

def get_dataset_version_by_id(db: Session, version_id: int):
    return db.query(models.DatasetVersion).filter(models.DatasetVersion.id == version_id).first()
