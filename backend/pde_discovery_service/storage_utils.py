import h5py
import numpy as np
import io
from minio import Minio
from minio.error import S3Error
from .config import settings
import logging
from typing import Dict, Any, BinaryIO, Optional
import json

logger = logging.getLogger(__name__)

# SEC-PDE-001: Removed global minio_client initialization.
# MinIO client will now be initialized per operation with the dms_token.

def _get_minio_client_with_token(dms_token: Optional[str]) -> Minio:
    """
    Initializes a MinIO client. If a `dms_token` (representing a session token from an STS)
    is provided, it is used as the sole credential for user-scoped access. If no `dms_token`
    is provided, the client falls back to using static worker credentials.

    NOTE: This implementation ensures that when a `dms_token` is present, static worker
    credentials are NOT used, thereby enforcing token-based authorization. A robust Security
    Token Service (STS) should ideally exchange the JWT `dms_token` for temporary, scoped
    MinIO credentials (access_key, secret_key, session_token) which would then be passed here.
    This current approach uses the JWT directly as a `session_token` and relies on MinIO's
    STS configuration to validate it against policies.
    """
    if not dms_token:
        logger.warning("dms_token is missing. Initializing MinIO client with static credentials.")
        client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
    else:
        # When dms_token is provided, we assume it's a session token from an STS
        # or is intended to be the primary authorization mechanism. Therefore, we should NOT
        # pass the static access_key/secret_key, as this would override the session_token's
        # authorization scope and defeat the purpose of user-scoped access.
        logger.info("dms_token provided. Initializing MinIO client with session_token for user-scoped access.")
        client = Minio(
            settings.MINIO_ENDPOINT,
            secure=settings.MINIO_SECURE,
            session_token=dms_token
        )

    try:
        if not client.bucket_exists(settings.MINIO_BUCKET_NAME):
            client.make_bucket(settings.MINIO_BUCKET_NAME)
            logger.info(f"MinIO bucket '{settings.MINIO_BUCKET_NAME}' created by token-aware client.")
        return client
    except S3Error as e:
        logger.error(f"Error checking/creating MinIO bucket with client: {e}")
        raise

async def upload_file_to_minio(object_name: str, file_data: BinaryIO, file_size: int, content_type: str, dms_token: str) -> str:
    client = _get_minio_client_with_token(dms_token) # SEC-PDE-001
    try:
        client.put_object(
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

async def get_object_content_from_minio(object_name: str, source_bucket_name: Optional[str] = None, dms_token: str = None) -> bytes:
    """Fetches the content of an object from MinIO/S3 and returns it as bytes."""
    client = _get_minio_client_with_token(dms_token) # SEC-PDE-001
    
    # If source_bucket_name is not provided, use the default bucket for this service
    bucket_to_use = source_bucket_name if source_bucket_name else settings.MINIO_BUCKET_NAME

    try:
        response = client.get_object(bucket_to_use, object_name)
        content = response.read()
        response.close()
        response.release_conn()
        logger.info(f"Successfully fetched content for {object_name} from MinIO bucket {bucket_to_use}.")
        return content
    except S3Error as e:
        logger.error(f"Error fetching object {object_name} from MinIO bucket {bucket_to_use}: {e}")
        raise

async def load_derivative_data_from_minio(derivative_results_path: str, dms_token: str) -> Dict[str, np.ndarray]:
    """Loads derivative data (and features) from an HDF5 file in MinIO."""
    path_parts = derivative_results_path.split('/')
    if len(path_parts) < 3:
        raise ValueError(f"Invalid derivative_results_path format: {derivative_results_path}. Expected /bucket_name/object_name.")
    
    source_bucket_name = path_parts[1]
    object_name = '/'.join(path_parts[2:])

    content_bytes = await get_object_content_from_minio(object_name, source_bucket_name, dms_token) # SEC-PDE-001
    data_buffer = io.BytesIO(content_bytes)
    
    loaded_data = {}
    with h5py.File(data_buffer, 'r') as f:
        for key in f.keys():
            loaded_data[key] = f[key][:]
    logger.info(f"Successfully loaded derivative data from {derivative_results_path}.")
    return loaded_data

async def save_pde_discovery_results_to_minio(object_name: str, results_dict: Dict[str, Any], job_id: int, output_name: str, dms_token: str) -> str:
    """Saves PDE discovery results (e.g., equations, metrics) to a JSON file in MinIO."""
    results_json_str = json.dumps(results_dict, indent=2)
    results_buffer = io.BytesIO(results_json_str.encode('utf-8'))
    results_buffer.seek(0)
    results_size = results_buffer.getbuffer().nbytes

    storage_path = await upload_file_to_minio(object_name, results_buffer, results_size, "application/json", dms_token) # SEC-PDE-001
    return storage_path

async def save_sensitivity_results_to_minio(object_name: str, results_dict: Dict[str, Any], job_id: int, output_name: str, dms_token: str) -> str:
    """Saves sensitivity analysis results to a JSON file in MinIO (STORY-504)."""
    results_json_str = json.dumps(results_dict, indent=2)
    results_buffer = io.BytesIO(results_json_str.encode('utf-8'))
    results_buffer.seek(0)
    results_size = results_buffer.getbuffer().nbytes

    storage_path = await upload_file_to_minio(object_name, results_buffer, results_size, "application/json", dms_token) # SEC-PDE-001
    return storage_path

async def save_logs_to_minio(logs_content: str, job_id: int, output_name: str, dms_token: str) -> str:
    """Saves training logs to MinIO and returns its storage path."""
    logs_buffer = io.BytesIO(logs_content.encode('utf-8'))
    logs_buffer.seek(0)
    logs_size = logs_buffer.getbuffer().nbytes

    object_name = f"logs/{job_id}/{output_name}_logs.txt"
    storage_path = await upload_file_to_minio(object_name, logs_buffer, logs_size, "text/plain", dms_token) # SEC-PDE-001
    return storage_path
