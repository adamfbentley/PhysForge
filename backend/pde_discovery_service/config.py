from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_SECURE: bool = True
    MINIO_BUCKET_NAME: str = "pde-discovery-results"

    # Job Orchestration Service Database URL for status updates
    JOB_ORCHESTRATION_DATABASE_URL: str

    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
