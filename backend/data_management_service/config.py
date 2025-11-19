from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_SECURE: bool = False # Set to True for HTTPS
    MINIO_BUCKET_NAME: str = "scientific-datasets"

    # JWT settings (must match Auth Service for token validation)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    ENVIRONMENT: str = "development" # Can be 'development', 'testing', 'production'

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
