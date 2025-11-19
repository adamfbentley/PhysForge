import h5py
import numpy as np
import io
from minio import Minio
from minio.error import S3Error
from .config import settings
import logging
from typing import Dict, Any, BinaryIO, Optional
import json
from datetime import timedelta

logger = logging.getLogger(__name__)

def _get_minio_client() -> Minio:
    """
    Initializes a MinIO client using the service's static credentials.
    NOTE ON SECURITY: This client uses static service-level credentials.
    User-specific authorization for MinIO objects is NOT enforced at the MinIO level
    with this client. Instead, application-level authorization (e.g., checking report ownership
    in the Reporting Service's database) must be performed *before* using this client
    to access or generate presigned URLs for user-specific data.
    A proper Security Token Service (STS) integration would be required to exchange
    a user's JWT for temporary, scoped MinIO credentials for granular, user-specific
    authorization directly at the MinIO level. This is a future enhancement.
    """
    client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE
    )
    try:
        if not client.bucket_exists(settings.MINIO_BUCKET_NAME):
            client.make_bucket(settings.MINIO_BUCKET_NAME)
            logger.info(f"MinIO bucket '{settings.MINIO_BUCKET_NAME}' created by service client.")
        return client
    except S3Error as e:
        logger.error(f"Error checking/creating MinIO bucket with client: {e}")
        raise

async def upload_file_to_minio(object_name: str, file_data: BinaryIO, file_size: int, content_type: str) -> str:
    """Uploads a file to MinIO."""
    client = _get_minio_client()
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

async def get_object_content_from_minio(object_name: str, source_bucket_name: Optional[str] = None) -> bytes:
    """Fetches the content of an object from MinIO/S3 and returns it as bytes."""
    client = _get_minio_client()
    
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

async def get_presigned_download_url(object_name: str, expires_in_seconds: int = 3600) -> str:
    """
    Generates a presigned download URL for an object in MinIO.
    """
    client = _get_minio_client()
    try:
        url = client.presigned_get_object(
            settings.MINIO_BUCKET_NAME,
            object_name,
            expires=timedelta(seconds=expires_in_seconds)
        )
        logger.info(f"Generated presigned URL for {object_name}.")
        return url
    except S3Error as e:
        logger.error(f"Error generating presigned URL for {object_name}: {e}")
        raise

async def load_data_from_minio_path(minio_path: str) -> bytes:
    """Loads generic data from a MinIO path (e.g., model, HDF5, JSON)."""
    path_parts = minio_path.split('/')
    if len(path_parts) < 3:
        raise ValueError(f"Invalid MinIO path format: {minio_path}. Expected /bucket_name/object_name.")
    
    source_bucket_name = path_parts[1]
    object_name = '/'.join(path_parts[2:])

    content_bytes = await get_object_content_from_minio(object_name, source_bucket_name)
    logger.info(f"Successfully loaded data from {minio_path}.")
    return content_bytes
