"""
In-memory sliding-window rate limiter for expensive endpoints.
"""
import time
from collections import defaultdict
from typing import Dict, List
from fastapi import Request, HTTPException, status
from app.config import settings

_request_history: Dict[str, List[float]] = defaultdict(list)


def check_rate_limit(request: Request) -> None:
    """
    Checks if client IP has exceeded the allowed requests per minute.
    Raises HTTPException 429 if limit is exceeded.
    """
    # Extract client IP
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()
    window = 60.0  # 1 minute sliding window

    history = _request_history[client_ip]
    # Prune timestamps older than 60 seconds
    _request_history[client_ip] = [t for t in history if now - t < window]

    if len(_request_history[client_ip]) >= settings.RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {settings.RATE_LIMIT_PER_MINUTE} requests per minute."
        )

    _request_history[client_ip].append(now)


def reset_rate_limits() -> None:
    """Clear in-memory rate limiting state (useful for tests)."""
    _request_history.clear()
