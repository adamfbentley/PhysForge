"""
Security headers middleware for FastAPI applications.
Adds security headers to all responses for better protection.
"""

from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    def __init__(self, app, csp_policy: str = None):
        super().__init__(app)
        self.csp_policy = csp_policy or self._get_default_csp()

    def _get_default_csp(self) -> str:
        """Get default Content Security Policy."""
        return (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "media-src 'self'; "
            "object-src 'none'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to the response."""
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = self.csp_policy

        # HSTS (HTTP Strict Transport Security) - only for HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


class CORSMiddleware:
    """CORS middleware with secure defaults."""

    def __init__(self, app, allow_origins: list = None, allow_credentials: bool = True):
        self.app = app
        self.allow_origins = allow_origins or ["http://localhost:3000", "http://localhost:80"]
        self.allow_credentials = allow_credentials
        self.allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = [
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With"
        ]
        self.max_age = 86400  # 24 hours

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Handle preflight requests
        if scope["method"] == "OPTIONS":
            await self._handle_preflight(scope, receive, send)
            return

        await self.app(scope, receive, send)

    async def _handle_preflight(self, scope, receive, send):
        """Handle CORS preflight requests."""
        headers = {}
        origin = None

        # Check Origin header
        for header_name, header_value in scope.get("headers", []):
            if header_name == b"origin":
                origin = header_value.decode("utf-8")
                break

        # Validate origin
        if origin and origin in self.allow_origins:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true" if self.allow_credentials else "false"
            headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
            headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
            headers["Access-Control-Max-Age"] = str(self.max_age)

        # Send preflight response
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [[k.encode(), v.encode()] for k, v in headers.items()],
        })
        await send({
            "type": "http.response.body",
            "body": b"",
        })


def add_security_headers(response: Response) -> Response:
    """
    Utility function to add security headers to a response.
    Useful for individual endpoints that need custom headers.
    """
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    return response