import h5py
import numpy as np
import io
from minio import Minio
from minio.error import S3Error
from .config import settings
import logging
from typing import Dict, Any, BinaryIO
import json

logger = logging.getLogger(__name__)

def _get_minio_client_with_token(dms_token: str) -> Minio:
    """
    Initializes a MinIO client using worker's static credentials and the dms_token.
    The `dms_token` (a JWT) is passed as a `session_token` to the MinIO client.
    This function requires a valid `dms_token` to be provided.
    Worker's static keys are used as primary credentials, and the `session_token`
    is intended for user-specific authorization enforcement via MinIO bucket policies.
    A full Security Token Service (STS) integration for dynamically issued, scoped credentials
    remains a future enhancement.
    """
    if not dms_token:
        raise ValueError("dms_token is required for MinIO client initialization.")

    client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
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
    client = _get_minio_client_with_token(dms_token)
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

async def load_pde_discovery_result_from_minio(pde_discovery_result_path: str, dms_token: str) -> Dict[str, Any]:
    """Loads PDE discovery result (JSON) from MinIO."""
    path_parts = pde_discovery_result_path.split('/')
    if len(path_parts) < 3:
        raise ValueError(f"Invalid pde_discovery_result_path format: {pde_discovery_result_path}. Expected /bucket_name/object_name.")
    
    source_bucket_name = path_parts[1]
    object_name = '/'.join(path_parts[2:])

    content_bytes = await get_object_content_from_minio(object_name, source_bucket_name, dms_token)
    return json.loads(content_bytes.decode('utf-8'))

async def save_proposed_parameters_to_minio(object_name: str, parameters_df: 'pd.DataFrame', dms_token: str) -> str:
    """Saves proposed parameters to an HDF5 file in MinIO."""
    h5_buffer = io.BytesIO()
    parameters_df.to_hdf(h5_buffer, key='proposed_parameters', mode='w', format='table')
    h5_buffer.seek(0)
    h5_size = h5_buffer.getbuffer().nbytes

    storage_path = await upload_file_to_minio(object_name, h5_buffer, h5_size, "application/x-hdf5", dms_token)
    return storage_path

async def save_optimization_history_to_minio(object_name: str, history: List[Dict[str, Any]], dms_token: str) -> str:
    """Saves optimization history to a JSON file in MinIO."""
    history_json_str = json.dumps(history, indent=2)
    history_buffer = io.BytesIO(history_json_str.encode('utf-8'))
    history_buffer.seek(0)
    history_size = history_buffer.getbuffer().nbytes

    storage_path = await upload_file_to_minio(object_name, history_buffer, history_size, "application/json", dms_token)
    return storage_path

async def save_logs_to_minio(logs_content: str, job_id: int, output_name: str, dms_token: str) -> str:
    """Saves logs to MinIO and returns its storage path."""
    logs_buffer = io.BytesIO(logs_content.encode('utf-8'))
    logs_buffer.seek(0)
    logs_size = logs_buffer.getbuffer().nbytes

    object_name = f"logs/{job_id}/{output_name}_logs.txt"
    storage_path = await upload_file_to_minio(object_name, logs_buffer, logs_size, "text/plain", dms_token)
    return storage_path

async def get_object_content_from_minio(object_name: str, source_bucket_name: Optional[str] = None, dms_token: str = None) -> bytes:
    """Fetches the content of an object from MinIO/S3 and returns it as bytes."""
    client = _get_minio_client_with_token(dms_token)
    
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
