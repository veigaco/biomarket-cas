"""
API key authentication dependency.
"""
from fastapi import Header, HTTPException, status
from typing import Optional
import os


# Load valid API keys from environment
VALID_API_KEYS = set(os.getenv("API_KEYS", "").split(","))


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """
    Verify API key from X-API-Key header.

    Args:
        x_api_key: API key from request header

    Returns:
        The API key if valid

    Raises:
        HTTPException: 401 if key is missing or invalid
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header"
        )

    if x_api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    return x_api_key
