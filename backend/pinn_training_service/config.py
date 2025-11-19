from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # MinIO/S3 Configuration for storing PINN models, checkpoints, and logs
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_SECURE: bool = True # SEC-CFG-001: Changed default to True for security
    MINIO_BUCKET_NAME: str = "pinn-training-results"

    # Data Management Service URL to fetch datasets
    DATA_MANAGEMENT_SERVICE_URL: str = "http://localhost:8002"
    # SEC-PTS-001: Removed DMS_SECRET_KEY and DMS_ALGORITHM as worker no longer generates tokens

    # Job Orchestration Service Database URL for status updates
    JOB_ORCHESTRATION_DATABASE_URL: str

    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
