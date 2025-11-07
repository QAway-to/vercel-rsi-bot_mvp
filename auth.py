"""Authentication utilities for protecting API endpoints."""
from typing import Optional, Set, Tuple
from fastapi import Header, HTTPException, status
import os

from loguru import logger

from security import KeyManager, mask_secret


KeyRecord = Tuple[str, bool]  # (value, is_hashed)


def _parse_key_records() -> Set[KeyRecord]:
    """Load API keys from env, supporting plain or hashed values.

    Prefix hashed keys with ``hash:`` and provide the HMAC/SHA-256 digest.
    """
    keys_raw = os.getenv("API_KEYS", "")
    records: Set[KeyRecord] = set()
    for raw_key in keys_raw.split(","):
        key = raw_key.strip()
        if not key:
            continue
        if key.startswith("hash:"):
            records.add((key.split("hash:", 1)[1], True))
        else:
            records.add((key, False))
    return records


KEY_MANAGER = KeyManager()
KEY_RECORDS: Set[KeyRecord] = _parse_key_records()


def api_keys_configured() -> bool:
    """Check whether API keys have been configured."""
    return bool(KEY_RECORDS)


def _is_valid_api_key(provided: str) -> bool:
    plain_keys = {value for value, is_hashed in KEY_RECORDS if not is_hashed}
    if provided in plain_keys:
        return True

    hashed_keys = [value for value, is_hashed in KEY_RECORDS if is_hashed]
    for stored_hash in hashed_keys:
        if KEY_MANAGER.verify_hash(provided, stored_hash):
            return True
    return False


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> None:
    """FastAPI dependency to enforce API key authentication."""
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

    if not _is_valid_api_key(x_api_key):
        logger.warning("Invalid API key provided.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "API key"},
        )

    logger.debug("API key validated successfully.")
