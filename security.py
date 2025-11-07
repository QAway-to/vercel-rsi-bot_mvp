"""Security utilities for the RSI trading bot."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import uuid
from typing import Dict, Optional

from loguru import logger


def generate_request_id() -> str:
    """Generate a unique request identifier."""
    return str(uuid.uuid4())


def generate_transaction_id() -> str:
    """Generate a unique transaction identifier."""
    # Use URL-safe token for readability and logging
    return secrets.token_urlsafe(20)


def hash_request_payload(payload: Dict[str, str]) -> str:
    """Create a deterministic hash for a trade request payload.

    The payload keys are sorted to ensure consistent hashing. Values are
    stringified and encoded as UTF-8 before hashing with SHA-256.
    """
    sorted_items = sorted(payload.items())
    normalized = "|".join(f"{key}:{value}" for key, value in sorted_items)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return digest


def mask_secret(secret: Optional[str]) -> str:
    """Return a masked representation of a secret for logging."""
    if not secret:
        return "<not-set>"

    if len(secret) <= 4:
        return "*" * len(secret)

    return f"{secret[:2]}***{secret[-2:]}"


class KeyManager:
    """Handle loading and optional hashing of sensitive keys."""

    def __init__(self, pepper_env: str = "KEY_HASH_PEPPER") -> None:
        self._pepper = os.getenv(pepper_env, "")

    def _peppered_hash(self, value: str) -> str:
        """Hash a value with an optional pepper for comparison."""
        if not self._pepper:
            return hashlib.sha256(value.encode("utf-8")).hexdigest()
        return hmac.new(
            key=self._pepper.encode("utf-8"),
            msg=value.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()

    def verify_hash(self, plaintext: str, hashed: str) -> bool:
        """Verify a plaintext value against a stored hash."""
        computed = self._peppered_hash(plaintext)
        return hmac.compare_digest(computed, hashed)

    def hash_value(self, plaintext: str) -> str:
        """Hash a plaintext value for storage in configuration."""
        return self._peppered_hash(plaintext)

    def load_and_mask(self, env_key: str) -> str:
        """Load a secret from environment and return its masked form."""
        value = os.getenv(env_key)
        masked = mask_secret(value)
        logger.debug(f"Loaded secret {env_key}: {masked}")
        return value or ""


def derive_sequence_key(pair: str, action: str) -> str:
    """Derive a stable key for sequence tracking."""
    return f"{pair.upper()}::{action.upper()}"


def parse_pair(pair: str) -> Dict[str, str]:
    """Split a trading pair string into base and quote assets.

    Currently supports standard formats like BTCUSDT. If unable to parse,
    defaults to entire pair as base and USDT as quote.
    """
    pair = pair.upper()
    candidates = ["USDT", "USD", "USDC", "EUR"]
    for candidate in candidates:
        if pair.endswith(candidate):
            base = pair[:-len(candidate)]
            quote = candidate
            if base:
                return {"base": base, "quote": quote}
    # Fallback
    return {"base": pair, "quote": "USDT"}
