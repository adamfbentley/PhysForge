from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_SECURE: bool = True
    MINIO_BUCKET_NAME: str = "active-experiment-results"

    # Job Orchestration Service Database URL for status updates
    JOB_ORCHESTRATION_DATABASE_URL: str

    # PDE Discovery Service URL (for fetching PDE results if needed, though MinIO paths are used)
    PDE_DISCOVERY_SERVICE_URL: str = "http://localhost:8004"

    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
