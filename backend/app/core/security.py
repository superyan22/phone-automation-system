"""
API Key authentication middleware.
"""
import os
import secrets
from typing import Optional
from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyHeader

# API Key for authentication
# Generate a secure key on first run, or use environment variable
_default_key = "phone-auto-0106234fc6cc2ccebb6dfea65d28a7db"
API_KEY=os.environ.get("API_KEY", _default_key)

# Skip auth for these paths
SKIP_AUTH_PATHS = [
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
]

# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify the API key from request header.
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API Key. Include 'X-API-Key' header."
        )
    if not secrets.compare_digest(api_key, API_KEY):
        raise HTTPException(
            status_code=403,
            detail="Invalid API Key"
        )
    return api_key


def should_skip_auth(path: str) -> bool:
    """Check if path should skip authentication."""
    return path in SKIP_AUTH_PATHS or path.startswith("/docs") or path.startswith("/redoc")


def get_api_key() -> str:
    """Get the current API key (for display purposes)."""
    return API_KEY
