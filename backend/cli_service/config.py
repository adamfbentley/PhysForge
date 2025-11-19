import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class CLISettings(BaseSettings):
    AUTH_SERVICE_URL: str = "http://localhost:8000"
    DATA_MANAGEMENT_SERVICE_URL: str = "http://localhost:8002"
    JOB_ORCHESTRATION_SERVICE_URL: str = "http://localhost:8003"
    
    # Path to store the JWT token and other CLI configurations
    CLI_CONFIG_DIR: Path = Path.home() / ".config" / "pinn_cli"
    CLI_TOKEN_FILE: Path = CLI_CONFIG_DIR / "token.yaml"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = CLISettings()

def get_token_file_path() -> Path:
    settings.CLI_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return settings.CLI_TOKEN_FILE

def save_token(token: str):
    token_file = get_token_file_path()
    try:
        with open(token_file, 'w') as f:
            yaml.dump({"access_token": token}, f)
        logger.info(f"Token saved to {token_file}")
    except Exception as e:
        logger.error(f"Failed to save token to {token_file}: {e}")
        raise

def load_token() -> Optional[str]:
    token_file = get_token_file_path()
    if not token_file.exists():
        return None
    try:
        with open(token_file, 'r') as f:
            config_data = yaml.safe_load(f)
            return config_data.get("access_token")
    except Exception as e:
        logger.warning(f"Failed to load token from {token_file}: {e}")
        return None

def delete_token():
    token_file = get_token_file_path()
    if token_file.exists():
        try:
            os.remove(token_file)
            logger.info(f"Token file {token_file} deleted.")
        except Exception as e:
            logger.error(f"Failed to delete token file {token_file}: {e}")
            raise
