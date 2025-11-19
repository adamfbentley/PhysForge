from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT settings (must match Auth Service for token validation)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    # MinIO/S3 Configuration for storing job results/logs
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_SECURE: bool = True # SEC-CFG-001: Changed default to True for security
    MINIO_BUCKET_NAME: str = "job-results"

    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
