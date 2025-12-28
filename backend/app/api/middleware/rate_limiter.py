"""
Rate limiting middleware using slowapi.
"""
from slowapi import Limiter
from fastapi import Request


def get_api_key_or_ip(request: Request) -> str:
    """
    Use API key as rate limit identifier if present,
    otherwise fall back to IP address.

    Args:
        request: FastAPI request object

    Returns:
        Identifier string for rate limiting
    """
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"key:{api_key}"
    return request.client.host if request.client else "unknown"


# Initialize limiter with custom key function
limiter = Limiter(
    key_func=get_api_key_or_ip,
    default_limits=["10000/minute"],  # Global limit
    storage_uri="memory://",  # In-memory storage (no Redis needed)
)
