from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Path
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from .. import crud, schemas, models
from ..database import get_db
from ..security import get_current_active_user
from ..object_storage import upload_file_to_minio, get_presigned_download_url
from ..metadata_extractor import extract_metadata
from ..config import settings

router = APIRouter()

@router.post("/", response_model=schemas.DatasetResponse, status_code=status.HTTP_201_CREATED,
             summary="Upload a new dataset and extract metadata")
async def upload_dataset(
    file: UploadFile = File(..., description="The scientific dataset file (e.g., HDF5, CSV, NetCDF)"),
    name: str = Form(..., description="A unique name for the dataset"),
    description: Optional[str] = Form(None, description="Optional description for the dataset"),
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Check for existing dataset with the same name for this owner
    existing_dataset = crud.get_dataset_by_name_and_owner(db, name=name, owner_id=current_user.id)
    if existing_dataset:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dataset with this name already exists for this user. Consider uploading a new version.")

    # 1. Create dataset entry in PostgreSQL
    dataset_create = schemas.DatasetCreate(name=name, description=description)
    db_dataset = crud.create_dataset(db=db, dataset=dataset_create, owner_id=current_user.id)

    # 2. Upload file to MinIO/S3
    # Generate a unique object name for storage
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
    object_name = f"{current_user.id}/{db_dataset.id}/{uuid.uuid4()}.{file_extension}"
    
    # Ensure file pointer is at the beginning before reading for upload
    await file.seek(0)
    file_content_for_upload = await file.read()
    await file.seek(0) # Reset again for metadata extraction if needed

    try:
        storage_path = await upload_file_to_minio(
            object_name=object_name,
            file_data=file_content_for_upload,
            file_size=file.size,
            content_type=file.content_type
        )
    except Exception as e:
        # Rollback dataset creation if MinIO upload fails
        db.delete(db_dataset)
        db.commit()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to upload file to object storage: {e}")

    # 3. Extract metadata (STORY-102)
    extracted_metadata = await extract_metadata(file)

    # 4. Create dataset version entry in PostgreSQL
    db_dataset_version = crud.create_dataset_version(
        db=db,
        dataset_id=db_dataset.id,
        storage_path=storage_path,
        metadata=extracted_metadata,
        uploader_id=current_user.id
    )

    # Refresh dataset to include the latest version relationship
    db.refresh(db_dataset)
    db_dataset.latest_version = db_dataset_version

    return db_dataset

@router.get("/", response_model=List[schemas.DatasetResponse],
            summary="Retrieve a list of all datasets owned by the current user")
async def list_datasets(
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    datasets = crud.get_datasets_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
    # Manually attach latest version for each dataset
    for dataset in datasets:
        dataset.latest_version = crud.get_latest_dataset_version(db, dataset.id)
    return datasets

@router.get("/{dataset_id}", response_model=schemas.DatasetResponse,
            summary="Retrieve metadata for a specific dataset")
async def get_dataset(
    dataset_id: int = Path(..., description="The ID of the dataset to retrieve"),
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_dataset = crud.get_dataset_by_id(db, dataset_id=dataset_id)
    if not db_dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    if db_dataset.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this dataset")

    db_dataset.latest_version = crud.get_latest_dataset_version(db, db_dataset.id)
    return db_dataset

@router.get("/{dataset_id}/download_link", summary="Generate a presigned URL to download the latest version of a dataset")
async def get_dataset_download_link(
    dataset_id: int = Path(..., description="The ID of the dataset to generate a download link for"),
    current_user: schemas.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    db_dataset = crud.get_dataset_by_id(db, dataset_id=dataset_id)
    if not db_dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    if db_dataset.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this dataset")

    latest_version = crud.get_latest_dataset_version(db, db_dataset.id)
    if not latest_version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No versions found for this dataset")

    # The storage_path stores the object_name in MinIO
    object_name_in_minio = latest_version.storage_path.split(f"/{settings.MINIO_BUCKET_NAME}/")[-1]
    try:
        download_url = await get_presigned_download_url(object_name=object_name_in_minio)
        return {"download_url": download_url, "expires_in_seconds": 3600}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate download link: {e}")
