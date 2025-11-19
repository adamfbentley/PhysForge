import torch
from minio import Minio
from minio.error import S3Error
from .config import settings
import logging
from datetime import timedelta
from typing import BinaryIO, Dict, Any, Optional
import httpx
import json
import io
import h5py # CQ-PTS-002: For HDF5 parsing
import numpy as np # CQ-PTS-002: For HDF5 parsing

logger = logging.getLogger(__name__)

# Initialize Minio client
try:
    minio_client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE
    )
    if not minio_client.bucket_exists(settings.MINIO_BUCKET_NAME):
        minio_client.make_bucket(settings.MINIO_BUCKET_NAME)
        logger.info(f"MinIO bucket '{settings.MINIO_BUCKET_NAME}' created.")
    else:
        logger.info(f"MinIO bucket '{settings.MINIO_BUCKET_NAME}' already exists.")
except S3Error as e:
    logger.error(f"Error initializing MinIO client or checking/creating bucket: {e}")
    minio_client = None

async def upload_file_to_minio(object_name: str, file_data: BinaryIO, file_size: int, content_type: str) -> str:
    if not minio_client:
        raise S3Error("MinIO client not initialized.", "", "", "")
    try:
        minio_client.put_object(
            settings.MINIO_BUCKET_NAME,
            object_name,
            file_data,
            file_size,
            content_type=content_type
        )
        logger.info(f"Successfully uploaded {object_name} to MinIO.")
        return f"/{settings.MINIO_BUCKET_NAME}/{object_name}"
    except S3Error as e:
        logger.error(f"Error uploading file {object_name} to MinIO: {e}")
        raise

async def save_model_to_minio(model: torch.nn.Module, job_id: int, output_name: str) -> str:
    """Saves a PyTorch model to MinIO and returns its storage path."""
    model_buffer = io.BytesIO()
    torch.save(model.state_dict(), model_buffer)
    model_buffer.seek(0)
    model_size = model_buffer.getbuffer().nbytes
    
    object_name = f"models/{job_id}/{output_name}_model.pth"
    storage_path = await upload_file_to_minio(object_name, model_buffer, model_size, "application/octet-stream")
    return storage_path

async def save_logs_to_minio(logs_content: str, job_id: int, output_name: str) -> str:
    """Saves training logs to MinIO and returns its storage path."""
    logs_buffer = io.BytesIO(logs_content.encode('utf-8'))
    logs_buffer.seek(0)
    logs_size = logs_buffer.getbuffer().nbytes

    object_name = f"logs/{job_id}/{output_name}_logs.txt"
    storage_path = await upload_file_to_minio(object_name, logs_buffer, logs_size, "text/plain")
    return storage_path

async def fetch_dataset_from_dms(dataset_id: int, user_id: int, token: str, version_id: Optional[int] = None,
                                 input_dataset_name: str = "x", output_dataset_name: str = "y") -> Dict[str, Any]: # CQ-PTS-002: Added dataset name parameters
    """Fetches a dataset from the Data Management Service using a presigned URL."""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        
        # First, get the download link from DMS
        download_link_endpoint = f"{settings.DATA_MANAGEMENT_SERVICE_URL}/datasets/{dataset_id}/download_link"
        logger.info(f"Requesting download link from DMS: {download_link_endpoint}")
        response = await client.get(download_link_endpoint, headers=headers)
        response.raise_for_status() # Raise an exception for 4xx/5xx responses
        download_info = response.json()
        presigned_url = download_info["download_url"]
        logger.info(f"Received presigned URL from DMS for dataset {dataset_id}.")

        # Then, download the actual data using the presigned URL
        logger.info(f"Downloading dataset from presigned URL...")
        data_response = await client.get(presigned_url)
        data_response.raise_for_status()
        
        # CQ-PTS-002: Use configurable dataset names for HDF5 parsing
        data_buffer = io.BytesIO(data_response.content)
        with h5py.File(data_buffer, 'r') as f:
            if input_dataset_name not in f or output_dataset_name not in f:
                raise ValueError(f"HDF5 file for dataset {dataset_id} must contain '{input_dataset_name}' and '{output_dataset_name}' datasets.")
            x_data = torch.tensor(f[input_dataset_name][:], dtype=torch.float32)
            y_data = torch.tensor(f[output_dataset_name][:], dtype=torch.float32)
            logger.info(f"Successfully downloaded and loaded dataset {dataset_id} with x_shape={x_data.shape}, y_shape={y_data.shape}.")
            return {"x": x_data, "y": y_data}

# SEC-PTS-001: Removed generate_dms_token function as worker should not generate tokens
