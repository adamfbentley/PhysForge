from minio import Minio
from minio.error import S3Error
from .config import settings
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

# Initialize Minio client
try:
    minio_client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE
    )
    # Ensure the bucket exists
    if not minio_client.bucket_exists(settings.MINIO_BUCKET_NAME):
        minio_client.make_bucket(settings.MINIO_BUCKET_NAME)
        logger.info(f"MinIO bucket '{settings.MINIO_BUCKET_NAME}' created.")
    else:
        logger.info(f"MinIO bucket '{settings.MINIO_BUCKET_NAME}' already exists.")
except S3Error as e:
    logger.error(f"Error initializing Minio client or checking/creating bucket: {e}")
    minio_client = None # Indicate that client is not available

async def upload_file_to_minio(object_name: str, file_data, file_size: int, content_type: str) -> str:
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

async def get_presigned_download_url(object_name: str, expires_in_seconds: int = 3600) -> str:
    if not minio_client:
        raise S3Error("MinIO client not initialized.", "", "", "")
    try:
        url = minio_client.presigned_get_object(
            settings.MINIO_BUCKET_NAME,
            object_name,
            expires=timedelta(seconds=expires_in_seconds)
        )
        logger.info(f"Generated presigned URL for {object_name}.")
        return url
    except S3Error as e:
        logger.error(f"Error generating presigned URL for {object_name}: {e}")
        raise
