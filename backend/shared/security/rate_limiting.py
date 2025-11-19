"""
Rate limiting middleware for FastAPI applications.
Implements per-user and per-IP rate limiting using Redis.
"""

import time
from typing import Callable, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import redis


class RateLimiter:
    def __init__(self, redis_client: redis.Redis, prefix: str = "rate_limit"):
        self.redis = redis_client
        self.prefix = prefix

    def _get_key(self, identifier: str, window: str) -> str:
        """Generate Redis key for rate limiting."""
        return f"{self.prefix}:{identifier}:{window}"

    def is_allowed(self, identifier: str, limit: int, window_seconds: int) -> bool:
        """
        Check if the identifier is within rate limits.

        Args:
            identifier: User ID, IP address, or other identifier
            limit: Maximum requests allowed in the window
            window_seconds: Time window in seconds

        Returns:
            True if request is allowed, False if rate limited
        """
        key = self._get_key(identifier, f"{window_seconds}s")
        current_time = int(time.time())

        # Use Redis sorted set to track requests
        # Remove old entries outside the window
        self.redis.zremrangebyscore(key, 0, current_time - window_seconds)

        # Count current requests in window
        request_count = self.redis.zcard(key)

        if request_count >= limit:
            return False

        # Add current request timestamp
        self.redis.zadd(key, {str(current_time): current_time})

        # Set expiration on the key
        self.redis.expire(key, window_seconds)

        return True

    def get_remaining_requests(self, identifier: str, limit: int, window_seconds: int) -> int:
        """Get remaining requests allowed in current window."""
        key = self._get_key(identifier, f"{window_seconds}s")
        current_time = int(time.time())

        # Clean old entries
        self.redis.zremrangebyscore(key, 0, current_time - window_seconds)

        request_count = self.redis.zcard(key)
        return max(0, limit - request_count)

    def get_reset_time(self, identifier: str, window_seconds: int) -> int:
        """Get time when rate limit resets (Unix timestamp)."""
        key = self._get_key(identifier, f"{window_seconds}s")
        current_time = int(time.time())

        # Get oldest timestamp in current window
        oldest_timestamps = self.redis.zrange(key, 0, 0, withscores=True)
        if oldest_timestamps:
            oldest_time = int(oldest_timestamps[0][1])
            return oldest_time + window_seconds

        return current_time + window_seconds


# Global rate limiter instance
rate_limiter: Optional[RateLimiter] = None


def init_rate_limiter(redis_url: str = "redis://redis:6379/0") -> RateLimiter:
    """Initialize global rate limiter."""
    global rate_limiter
    redis_client = redis.from_url(redis_url)
    rate_limiter = RateLimiter(redis_client)
    return rate_limiter


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    if rate_limiter is None:
        raise RuntimeError("Rate limiter not initialized. Call init_rate_limiter() first.")
    return rate_limiter


# Rate limit configurations
RATE_LIMITS = {
    "auth": {"limit": 10, "window": 60},  # 10 requests per minute for auth
    "api": {"limit": 100, "window": 60},  # 100 requests per minute for general API
    "file_upload": {"limit": 5, "window": 300},  # 5 uploads per 5 minutes
}


async def rate_limit_middleware(request: Request, call_next: Callable):
    """
    FastAPI middleware for rate limiting.
    Should be added to app.middleware("http") in main.py
    """
    if rate_limiter is None:
        # Skip rate limiting if not configured
        return await call_next(request)

    # Get user ID from request state (set by auth middleware)
    user_id = getattr(request.state, 'user_id', None)
    client_ip = request.client.host if request.client else "unknown"

    # Use user ID if authenticated, otherwise IP
    identifier = f"user_{user_id}" if user_id else f"ip_{client_ip}"

    # Determine rate limit based on endpoint
    path = request.url.path
    if path.startswith("/auth/"):
        limits = RATE_LIMITS["auth"]
    elif any(path.startswith(prefix) for prefix in ["/datasets/", "/jobs/", "/reports/"]):
        limits = RATE_LIMITS["api"]
    else:
        limits = RATE_LIMITS["api"]  # Default limits

    # Check rate limit
    if not rate_limiter.is_allowed(identifier, limits["limit"], limits["window"]):
        # Rate limited - return 429
        reset_time = rate_limiter.get_reset_time(identifier, limits["window"])
        reset_in = max(0, reset_time - int(time.time()))

        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Try again in {reset_in} seconds.",
                "retry_after": reset_in
            },
            headers={"Retry-After": str(reset_in)}
        )

    # Proceed with request
    response = await call_next(request)
    return response