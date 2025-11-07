"""Authentication utilities for protecting API endpoints."""
from typing import Optional, Set
from fastapi import Header, HTTPException, status
import os
from loguru import logger


def _load_allowed_api_keys() -> Set[str]:
    """Load allowed API keys from environment variable.

    The environment variable `API_KEYS` should contain a comma-separated list of
    allowed API keys. Whitespace around keys is stripped.
    """
    keys_raw = os.getenv("API_KEYS", "")
    keys = {key.strip() for key in keys_raw.split(",") if key.strip()}
    return keys


ALLOWED_API_KEYS: Set[str] = _load_allowed_api_keys()


def api_keys_configured() -> bool:
    """Check whether API keys have been configured."""
    return bool(ALLOWED_API_KEYS)


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> None:
    """FastAPI dependency to enforce API key authentication.

    If no API keys are configured, the dependency allows all requests.
    Otherwise, the request must include an `X-API-Key` header matching one of
    the configured keys.
    """
    if not api_keys_configured():
        logger.debug("API key authentication disabled (no keys configured).")
        return

    if not x_api_key:
        logger.warning("Missing X-API-Key header on protected endpoint.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
            headers={"WWW-Authenticate": "API key"},
        )

    if x_api_key not in ALLOWED_API_KEYS:
        logger.warning("Invalid API key provided.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "API key"},
        )

    logger.debug("API key validated successfully.")
