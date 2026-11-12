from __future__ import annotations

import logging
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger("dragon.rate_limiter")

# Initialize slowapi Limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"]
)

def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Custom response handler for rate limit exceeded errors."""
    logger.warning("Rate limit exceeded for IP: %s on path: %s", get_remote_address(request), request.url.path)
    return JSONResponse(
        status_code=429,
        content={
            "error": "too_many_requests",
            "message": "Too many requests. Please try again later.",
            "detail": exc.detail if hasattr(exc, "detail") else "Rate limit exceeded"
        }
    )
