from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.core.config import settings


def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    """Validate the API key. Production: replace with OAuth2 / JWT."""
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


def get_requested_by(
    x_requested_by: str | None = Header(default=None, alias="X-Requested-By"),
) -> str:
    """
    Identify who is making the request (employee ID, service name, etc.).
    Production: extract from JWT claims instead.
    """
    if not x_requested_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Requested-By header is required",
        )
    return x_requested_by
