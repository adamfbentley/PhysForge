"""
Input validation and sanitization utilities.
Provides comprehensive validation for user inputs, file uploads, and API data.
"""

import re
import os
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import magic
from fastapi import UploadFile, HTTPException, status


class InputValidator:
    """Comprehensive input validation and sanitization."""

    # File type restrictions
    ALLOWED_EXTENSIONS = {
        'dataset': ['.csv', '.h5', '.hdf5', '.json', '.txt', '.npy', '.npz'],
        'config': ['.json', '.yaml', '.yml'],
        'image': ['.png', '.jpg', '.jpeg', '.gif', '.svg'],
        'document': ['.pdf', '.md', '.txt']
    }

    # MIME type mappings
    ALLOWED_MIME_TYPES = {
        'text/csv': ['.csv'],
        'application/json': ['.json'],
        'application/x-hdf5': ['.h5', '.hdf5'],
        'text/plain': ['.txt', '.md'],
        'application/x-numpy': ['.npy', '.npz'],
        'application/pdf': ['.pdf'],
        'image/png': ['.png'],
        'image/jpeg': ['.jpg', '.jpeg'],
        'image/gif': ['.gif'],
        'image/svg+xml': ['.svg']
    }

    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB default
    MAX_FILENAME_LENGTH = 255

    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 1000) -> str:
        """
        Sanitize string input by removing potentially dangerous characters.

        Args:
            input_str: Input string to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized string
        """
        if not isinstance(input_str, str):
            raise ValueError("Input must be a string")

        # Remove null bytes and other control characters
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', input_str)

        # Trim whitespace
        sanitized = sanitized.strip()

        # Check length
        if len(sanitized) > max_length:
            raise ValueError(f"Input exceeds maximum length of {max_length} characters")

        return sanitized

    @staticmethod
    def validate_email(email: str) -> str:
        """Validate and sanitize email address."""
        email = InputValidator.sanitize_string(email, 254)  # RFC 5321 limit

        # Basic email regex (not perfect but covers most cases)
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")

        return email

    @staticmethod
    def validate_filename(filename: str, allowed_extensions: List[str] = None) -> str:
        """Validate filename for security and allowed extensions."""
        filename = InputValidator.sanitize_string(filename, InputValidator.MAX_FILENAME_LENGTH)

        # Remove path separators
        filename = os.path.basename(filename)

        # Check for dangerous characters
        if any(char in filename for char in ['<', '>', ':', '"', '|', '?', '*']):
            raise ValueError("Filename contains invalid characters")

        # Check extension
        if allowed_extensions:
            file_ext = Path(filename).suffix.lower()
            if file_ext not in [ext.lower() for ext in allowed_extensions]:
                raise ValueError(f"File extension '{file_ext}' not allowed. Allowed: {allowed_extensions}")

        return filename

    @staticmethod
    def validate_file_content(file: UploadFile, allowed_types: List[str] = None,
                           max_size: int = None) -> Dict[str, Any]:
        """
        Validate uploaded file content using magic numbers.

        Args:
            file: FastAPI UploadFile object
            allowed_types: List of allowed file types/categories
            max_size: Maximum file size in bytes

        Returns:
            Dict with validation results
        """
        max_size = max_size or InputValidator.MAX_FILE_SIZE

        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {max_size} bytes"
            )

        # Read first 1024 bytes for MIME detection
        file_header = file.file.read(1024)
        file.file.seek(0)  # Reset

        try:
            mime_type = magic.from_buffer(file_header, mime=True)
        except Exception:
            mime_type = "application/octet-stream"

        # Validate MIME type
        if allowed_types:
            allowed_mimes = []
            for file_type in allowed_types:
                if file_type in InputValidator.ALLOWED_EXTENSIONS:
                    for ext in InputValidator.ALLOWED_EXTENSIONS[file_type]:
                        if ext in InputValidator.ALLOWED_MIME_TYPES:
                            allowed_mimes.extend(InputValidator.ALLOWED_MIME_TYPES[ext])

            if mime_type not in allowed_mimes:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type '{mime_type}' not allowed. Allowed types: {allowed_mimes}"
                )

        return {
            "filename": file.filename,
            "size": file_size,
            "mime_type": mime_type,
            "valid": True
        }

    @staticmethod
    def validate_json_config(config: Dict[str, Any], schema: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Validate JSON configuration against a schema.

        Args:
            config: Configuration dictionary
            schema: JSON schema for validation (optional)

        Returns:
            Validated configuration
        """
        if not isinstance(config, dict):
            raise ValueError("Configuration must be a dictionary")

        # Basic validation - check for required fields based on job type
        if 'job_type' in config:
            job_type = config['job_type']
            if job_type == 'pinn_training':
                required_fields = ['model_config', 'training_config', 'data_config']
            elif job_type == 'pde_discovery':
                required_fields = ['algorithm', 'data_path', 'feature_library']
            elif job_type == 'derivatives':
                required_fields = ['data_path', 'derivative_order']
            elif job_type == 'active_experiment':
                required_fields = ['experiment_config', 'data_path']
            else:
                required_fields = []

            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required field '{field}' for job type '{job_type}'")

        # Sanitize string values
        sanitized_config = {}
        for key, value in config.items():
            if isinstance(value, str):
                sanitized_config[key] = InputValidator.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized_config[key] = InputValidator.validate_json_config(value)
            elif isinstance(value, list):
                sanitized_config[key] = [
                    InputValidator.validate_json_config(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized_config[key] = value

        return sanitized_config

    @staticmethod
    def validate_numeric_range(value: Union[int, float], min_val: float = None,
                             max_val: float = None, field_name: str = "value") -> Union[int, float]:
        """Validate numeric value is within acceptable range."""
        if min_val is not None and value < min_val:
            raise ValueError(f"{field_name} must be >= {min_val}")
        if max_val is not None and value > max_val:
            raise ValueError(f"{field_name} must be <= {max_val}")
        return value


# Convenience functions for common validations
def validate_dataset_upload(file: UploadFile) -> Dict[str, Any]:
    """Validate dataset file upload."""
    return InputValidator.validate_file_content(
        file,
        allowed_types=['dataset'],
        max_size=100 * 1024 * 1024  # 100MB for datasets
    )

def validate_config_upload(file: UploadFile) -> Dict[str, Any]:
    """Validate configuration file upload."""
    return InputValidator.validate_file_content(
        file,
        allowed_types=['config'],
        max_size=1 * 1024 * 1024  # 1MB for configs
    )

def validate_job_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate job configuration."""
    return InputValidator.validate_json_config(config)