from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_SECURE: bool = True
    MINIO_BUCKET_NAME: str = "discovery-reports"

    # Job Orchestration Service URL to fetch job details
    JOB_ORCHESTRATION_SERVICE_URL: str = "http://localhost:8003"

    # JWT settings (must match Auth Service for token validation)
    # SECURITY VULNERABILITY: Shared Secret Key.
    # Consider implementing asymmetric cryptography (e.g., RSA) where the Auth Service
    # signs tokens with a private key, and other services (like Reporting Service)
    # verify them using the Auth Service's public key.
    # Alternatively, if symmetric keys are preferred, implement a robust key rotation
    # strategy and ensure the shared secret is managed with extreme care, potentially
    # via a dedicated secrets management service.
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
