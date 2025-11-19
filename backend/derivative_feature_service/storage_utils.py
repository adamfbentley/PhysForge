import torch
import torch.nn as nn
from minio import Minio
from minio.error import S3Error
from .config import settings
import logging
from datetime import timedelta
from typing import BinaryIO, Dict, Any, Optional
import io
import h5py
import numpy as np

# Import necessary components from pinn_training_service to reconstruct models
from backend.pinn_training_service.pinn_model import MLP, FourierFeatureMLP, DeepONet, build_model
from backend.pinn_training_service.pinn_config import NetworkArchitecture as PinnNetworkArchitecture

logger = logging.getLogger(__name__)

minio_client = None
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
    logger.error(f"Error initializing MinIO client for Derivative & Feature Service: {e}")
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

async def get_object_content_from_minio(object_name: str) -> bytes:
    """Fetches the content of an object from MinIO/S3 and returns it as bytes."""
    if not minio_client:
        raise S3Error("MinIO client not initialized.", "", "", "")
    try:
        response = minio_client.get_object(settings.MINIO_BUCKET_NAME, object_name)
        content = response.read()
        response.close()
        response.release_conn()
        logger.info(f"Successfully fetched content for {object_name} from MinIO.")
        return content
    except S3Error as e:
        logger.error(f"Error fetching object {object_name} from MinIO: {e}")
        raise

async def load_model_from_minio(model: torch.nn.Module, model_path: str):
    """Loads a PyTorch model's state_dict from MinIO into the provided model instance."""
    if not minio_client:
        raise S3Error("MinIO client not initialized.", "", "", "")
    
    # model_path is expected to be in the format /bucket_name/path/to/model.pth
    path_parts = model_path.split('/')
    # The model path comes from pinn_training_service, which uses its own bucket name.
    # We need to extract the bucket name from the path, not assume settings.MINIO_BUCKET_NAME
    if len(path_parts) < 3:
        raise ValueError(f"Invalid model_path format: {model_path}. Expected /bucket_name/object_name.")
    
    source_bucket_name = path_parts[1]
    object_name = '/'.join(path_parts[2:])

    try:
        response = minio_client.get_object(source_bucket_name, object_name)
        model_buffer = io.BytesIO(response.read())
        response.close()
        response.release_conn()
        
        model.load_state_dict(torch.load(model_buffer, map_location=torch.device('cpu')))
        model.eval() # Set to evaluation mode
        logger.info(f"Successfully loaded model from {model_path}.")
    except S3Error as e:
        logger.error(f"Error loading model from MinIO at {model_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error processing loaded model from {model_path}: {e}")
        raise

async def save_derivatives_to_minio(object_name: str, data: Dict[str, np.ndarray], job_id: int, output_name: str) -> str:
    """Saves computed derivatives to an HDF5 file in MinIO and returns its storage path."""
    h5_buffer = io.BytesIO()
    with h5py.File(h5_buffer, 'w') as f:
        for key, value in data.items():
            f.create_dataset(key, data=value)
    h5_buffer.seek(0)
    h5_size = h5_buffer.getbuffer().nbytes

    storage_path = await upload_file_to_minio(object_name, h5_buffer, h5_size, "application/x-hdf5")
    return storage_path

async def save_logs_to_minio(logs_content: str, job_id: int, output_name: str) -> str:
    """Saves training logs to MinIO and returns its storage path."""
    logs_buffer = io.BytesIO(logs_content.encode('utf-8'))
    logs_buffer.seek(0)
    logs_size = logs_buffer.getbuffer().nbytes

    object_name = f"logs/{job_id}/{output_name}_logs.txt"
    storage_path = await upload_file_to_minio(object_name, logs_buffer, logs_size, "text/plain")
    return storage_path
