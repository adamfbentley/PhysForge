from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # SEC-002: Removed insecure default database credentials.
    # DATABASE_URL should be provided via .env or environment variables.
    # For local development, a default like "postgresql+psycopg2://user:password@localhost:5432/auth_db"
    # can be used in .env.example, but not hardcoded here as a fallback.
    DATABASE_URL: str

    # SEC-001: Removed hardcoded insecure SECRET_KEY.
    # SECRET_KEY must be provided via .env or environment variables.
    SECRET_KEY: str

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CQ-001: Added environment setting for conditional logic (e.g., migrations)
    ENVIRONMENT: str = "development" # Can be 'development', 'testing', 'production'

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
