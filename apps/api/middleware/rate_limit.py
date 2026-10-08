"""
Rate limiting middleware using slowapi + Redis.

Implements both IP-based and user-based rate limiting to prevent abuse.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from starlette.responses import JSONResponse

from config import Settings


def get_request_identifier(request: Request) -> str:
    """
    Get unique identifier for rate limiting.
    Uses user_id if authenticated, otherwise IP address.
    """
    # Try to get user from JWT if available
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        # Extract user_id from JWT (simplified - actual implementation in auth.py)
        # For now, use IP + optional user hint
        user_hint = request.headers.get("x-user-id", "")
        if user_hint:
            return f"user:{user_hint}"
    
    # Fall back to IP-based limiting
    return f"ip:{get_remote_address(request)}"


# Initialize limiter with Redis backend
limiter = Limiter(
    key_func=get_request_identifier,
    storage_uri="redis://localhost:6379/1",  # Use DB 1 for rate limiting
    strategy="fixed-window",  # Fixed window algorithm
    headers_enabled=True,  # Add X-RateLimit-* headers
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler for rate limit exceeded errors.
    Returns clear error message with retry information.
    """
    retry_after = exc.detail.split("Retry after ")[1].split(" ")[0] if "Retry after" in exc.detail else "60"
    
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": f"Too many requests. Please try again in {retry_after} seconds.",
            "retry_after": int(retry_after),
        },
        headers={
            "Retry-After": retry_after,
            "X-RateLimit-Limit": str(exc.detail.split("/")[0] if "/" in exc.detail else "60"),
        }
    )


# Rate limit decorators for different endpoint types

# High cost operations (uploads, exports, AI)
HIGH_COST_LIMIT = "5/minute"

# Medium cost operations (analysis, matching)
MEDIUM_COST_LIMIT = "15/minute"

# Low cost operations (reads)
LOW_COST_LIMIT = "100/minute"

# Default for all other endpoints
DEFAULT_LIMIT = "60/minute"
