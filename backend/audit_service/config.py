"""
Configuration for Audit Service
"""

import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://physforge:physforge_password@postgres:5432/physforge_audit"

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Auth Service URL for token verification
    auth_service_url: str = "http://auth_service:8000"

    # Audit settings
    audit_log_file: str = "/var/log/physforge/audit.log"
    max_audit_log_size: int = 100 * 1024 * 1024  # 100MB
    audit_log_backups: int = 5

    # Retention settings (in days)
    default_retention_days: int = 2555  # 7 years

    class Config:
        env_file = ".env"


settings = Settings()