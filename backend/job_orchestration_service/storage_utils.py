from minio import Minio
from minio.error import S3Error
from .config import settings
import logging
import io

logger = logging.getLogger(__name__)

minio_client = None
try:
    minio_client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE
    )
    # The bucket is primarily managed by the PINN Training Service.
    # Here, we just ensure the client is initialized for reading.
    if not minio_client.bucket_exists(settings.MINIO_BUCKET_NAME):
        logger.warning(f"MinIO bucket '{settings.MINIO_BUCKET_NAME}' does not exist. It should be created by the PINN Training Service.")
    else:
        logger.info(f"MinIO bucket '{settings.MINIO_BUCKET_NAME}' exists.")
except S3Error as e:
    logger.error(f"Error initializing MinIO client for Job Orchestration Service: {e}")
    minio_client = None

async def get_object_content_from_minio(object_name: str) -> str:
    """Fetches the content of an object from MinIO/S3 and returns it as a string."""
    if not minio_client:
        raise S3Error("MinIO client not initialized.", "", "", "")
    try:
        response = minio_client.get_object(settings.MINIO_BUCKET_NAME, object_name)
        content = response.read().decode('utf-8')
        response.close()
        response.release_conn()
        logger.info(f"Successfully fetched content for {object_name} from MinIO.")
        return content
    except S3Error as e:
        logger.error(f"Error fetching object {object_name} from MinIO: {e}")
        raise
