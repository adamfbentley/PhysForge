from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # MinIO/S3 Configuration for storing derivative results
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_SECURE: bool = True # Default to True for security
    MINIO_BUCKET_NAME: str = "derivative-results"

    # Job Orchestration Service Database URL for status updates
    JOB_ORCHESTRATION_DATABASE_URL: str

    # Data Management Service URL (for fetching PINN models if needed, though PINN Training Service saves to MinIO)
    # Not directly used for fetching models, but good to have consistent config
    DATA_MANAGEMENT_SERVICE_URL: str = "http://localhost:8002"

    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
