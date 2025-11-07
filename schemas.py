from __future__ import annotations

import uuid
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, validator


class TradeRequest(BaseModel):
    """Client request payload for executing a trade."""

    pair: Optional[str] = Field(default=None, description="Trading pair, e.g., BTCUSDT")
    quantity: Optional[float] = Field(default=None, gt=0, description="Quantity to trade")
    request_id: Optional[str] = Field(default=None, description="Client-provided request identifier")
    sequence_number: Optional[int] = Field(default=None, ge=1, description="Monotonic sequence number to prevent replays")
    client_ref: Optional[str] = Field(default=None, max_length=64, description="Custom client correlation reference")
    force: bool = Field(default=False, description="Force execution even if RSI thresholds aren't met (for testing)")

    @validator("request_id", pre=True, always=True)
    def ensure_request_id(cls, value: Optional[str]) -> str:
        """Ensure every request has a request_id for deduplication."""
        return value or str(uuid.uuid4())


class BalanceSnapshot(BaseModel):
    """Representation of account balances after a trade."""

    asset: str
    balance: float


class TradeResponse(BaseModel):
    """Response returned after executing a trade."""

    pair: str
    action: str
    rsi: float
    price: Optional[float]
    quantity: Optional[float]
    status: str
    trade_id: Optional[int]
    transaction_id: Optional[str]
    sequence_number: Optional[int]
    request_id: str
    request_hash: str
    balances: Dict[str, float]
    message: Optional[str]


class StatusResponse(BaseModel):
    """Status payload for the /status endpoint."""

    pair: str
    rsi: float
    price: float
    rsi_oversold: float
    rsi_overbought: float
    trades: Dict[str, Any]
    balances: Dict[str, float]
