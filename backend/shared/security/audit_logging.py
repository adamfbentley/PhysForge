"""
Audit logging for security events and user actions.
Provides comprehensive logging of security-relevant events.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
import hashlib
from fastapi import Request, Response


class AuditEventType(Enum):
    """Types of audit events."""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTER = "user_register"
    PASSWORD_CHANGE = "password_change"
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    FILE_DELETE = "file_delete"
    JOB_SUBMIT = "job_submit"
    JOB_CANCEL = "job_cancel"
    ADMIN_ACTION = "admin_action"
    AUTH_FAILURE = "auth_failure"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


class AuditLogger:
    """Audit logger for security events."""

    def __init__(self, service_name: str, log_file: str = None):
        self.service_name = service_name
        self.logger = logging.getLogger(f"audit.{service_name}")
        self.logger.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def log_event(self, event_type: AuditEventType, user_id: Optional[int],
                  details: Dict[str, Any], request: Request = None,
                  ip_address: str = None, user_agent: str = None) -> None:
        """
        Log an audit event.

        Args:
            event_type: Type of audit event
            user_id: ID of the user performing the action (None for anonymous)
            details: Additional details about the event
            request: FastAPI request object
            ip_address: IP address of the client
            user_agent: User agent string
        """
        # Extract request information
        if request:
            ip_address = ip_address or self._get_client_ip(request)
            user_agent = user_agent or request.headers.get("User-Agent", "")
            path = str(request.url.path)
            method = request.method
        else:
            path = details.get("path", "")
            method = details.get("method", "")

        # Create audit log entry
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.service_name,
            "event_type": event_type.value,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "path": path,
            "method": method,
            "details": details,
            "severity": self._get_event_severity(event_type)
        }

        # Add request ID for correlation
        if request and hasattr(request.state, 'request_id'):
            audit_entry["request_id"] = request.state.request_id

        # Log the event
        log_message = json.dumps(audit_entry, default=str)
        self.logger.info(log_message)

    def log_security_event(self, event_type: AuditEventType, details: Dict[str, Any],
                          request: Request = None) -> None:
        """Log a security-related event with higher priority."""
        user_id = getattr(request.state, 'user_id', None) if request else None
        self.log_event(event_type, user_id, details, request)
        # Could also send to security monitoring system here

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in case of multiple
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct client
        return request.client.host if request.client else "unknown"

    def _get_event_severity(self, event_type: AuditEventType) -> str:
        """Determine severity level for audit event."""
        high_severity_events = [
            AuditEventType.AUTH_FAILURE,
            AuditEventType.SUSPICIOUS_ACTIVITY,
            AuditEventType.ADMIN_ACTION
        ]

        if event_type in high_severity_events:
            return "HIGH"
        elif event_type in [AuditEventType.USER_LOGIN, AuditEventType.USER_LOGOUT]:
            return "MEDIUM"
        else:
            return "LOW"


# Global audit logger instance
audit_logger: Optional[AuditLogger] = None


def init_audit_logger(service_name: str, log_file: str = None) -> AuditLogger:
    """Initialize global audit logger."""
    global audit_logger
    audit_logger = AuditLogger(service_name, log_file)
    return audit_logger


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    if audit_logger is None:
        raise RuntimeError("Audit logger not initialized. Call init_audit_logger() first.")
    return audit_logger


# Convenience functions for common audit events
def log_user_login(user_id: int, request: Request) -> None:
    """Log successful user login."""
    get_audit_logger().log_event(
        AuditEventType.USER_LOGIN,
        user_id,
        {"action": "login_successful"},
        request
    )

def log_user_logout(user_id: int, request: Request) -> None:
    """Log user logout."""
    get_audit_logger().log_event(
        AuditEventType.USER_LOGOUT,
        user_id,
        {"action": "logout"},
        request
    )

def log_auth_failure(username: str, request: Request) -> None:
    """Log authentication failure."""
    get_audit_logger().log_security_event(
        AuditEventType.AUTH_FAILURE,
        {"username": username, "action": "login_failed"},
        request
    )

def log_file_upload(user_id: int, filename: str, file_size: int, request: Request) -> None:
    """Log file upload event."""
    get_audit_logger().log_event(
        AuditEventType.FILE_UPLOAD,
        user_id,
        {
            "filename": filename,
            "file_size": file_size,
            "action": "file_upload"
        },
        request
    )

def log_job_submission(user_id: int, job_type: str, job_id: int, request: Request) -> None:
    """Log job submission event."""
    get_audit_logger().log_event(
        AuditEventType.JOB_SUBMIT,
        user_id,
        {
            "job_type": job_type,
            "job_id": job_id,
            "action": "job_submitted"
        },
        request
    )


class AuditMiddleware:
    """Middleware to add audit logging to requests."""

    def __init__(self, app, service_name: str):
        self.app = app
        self.service_name = service_name

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract request information
        method = scope["method"]
        path = scope["path"]
        headers = dict(scope.get("headers", []))

        # Generate request ID for correlation
        import uuid
        request_id = str(uuid.uuid4())

        # Add request ID to scope for downstream use
        scope["request_id"] = request_id

        # Log the request (you might want to filter certain endpoints)
        if audit_logger and not path.startswith("/metrics"):  # Don't log metrics requests
            audit_logger.logger.info(
                json.dumps({
                    "timestamp": datetime.utcnow().isoformat(),
                    "service": self.service_name,
                    "event_type": "http_request",
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "user_agent": headers.get(b"user-agent", b"").decode("utf-8", errors="ignore"),
                    "severity": "INFO"
                })
            )

        await self.app(scope, receive, send)