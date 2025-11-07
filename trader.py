"""Secure trading logic with duplicate prevention and balance management."""
from __future__ import annotations

import random
from typing import Dict, Optional

from loguru import logger

from config import config
from db import (
    adjust_balance,
    ensure_initial_balance,
    fetch_trade_by_request_hash,
    get_balance,
    get_balance_snapshot,
    get_balances,
    get_next_sequence,
    get_trade_summary,
    record_trade,
    trade_exists,
)
from schemas import TradeRequest, TradeResponse, StatusResponse
from security import (
    generate_transaction_id,
    hash_request_payload,
    parse_pair,
)


def calculate_mock_rsi() -> float:
    """Generate a mock RSI value for demonstration purposes."""
    return round(random.uniform(10, 90), 2)


def get_mock_price(pair: Optional[str] = None) -> float:
    """Generate a mock price for the trading pair."""
    mock_prices = {
        "BTCUSDT": 45000.0,
        "ETHUSDT": 2500.0,
        "BNBUSDT": 300.0,
    }

    pair = (pair or config.TRADING_PAIR).upper()
    base_price = mock_prices.get(pair, 100.0)
    variation = random.uniform(-0.02, 0.02)
    return round(base_price * (1 + variation), 2)


def _prepare_balances(pair: str) -> Dict[str, float]:
    """Ensure balances exist for the trading pair assets."""
    assets = parse_pair(pair)
    ensure_initial_balance(assets["base"], config.DEFAULT_BASE_BALANCE)
    ensure_initial_balance(assets["quote"], config.DEFAULT_QUOTE_BALANCE)
    return get_balances()


async def get_trading_status() -> StatusResponse:
    """Return current status with RSI, pricing, and balances."""
    pair = config.TRADING_PAIR
    rsi = calculate_mock_rsi()
    price = get_mock_price(pair)
    balances = _prepare_balances(pair)
    summary = get_trade_summary()

    return StatusResponse(
        pair=pair,
        rsi=rsi,
        price=price,
        rsi_oversold=config.RSI_OVERSOLD,
        rsi_overbought=config.RSI_OVERBOUGHT,
        trades=summary,
        balances=balances,
    )


def _validate_sequence(pair: str, action: str, sequence_number: Optional[int]) -> int:
    """Ensure provided sequence number is valid and return final value."""
    expected_next = get_next_sequence(pair, action)
    if sequence_number is None:
        return expected_next

    if sequence_number < expected_next:
        raise ValueError(
            f"Sequence number {sequence_number} is stale. Next allowed sequence is {expected_next}."
        )

    if sequence_number > expected_next:
        raise ValueError(
            f"Sequence number {sequence_number} skipped expected {expected_next}."
        )

    return sequence_number


def _check_rsi_conditions(action: str, rsi: float, force: bool) -> Optional[str]:
    if force:
        return None

    if action == "BUY" and rsi >= config.RSI_OVERSOLD:
        return f"RSI ({rsi}) is not below oversold threshold ({config.RSI_OVERSOLD})."
    if action == "SELL" and rsi <= config.RSI_OVERBOUGHT:
        return f"RSI ({rsi}) is not above overbought threshold ({config.RSI_OVERBOUGHT})."
    return None


def _validate_balances(action: str, pair: str, quantity: float, price: float) -> Optional[str]:
    assets = parse_pair(pair)
    base_asset = assets["base"]
    quote_asset = assets["quote"]

    if action == "BUY":
        cost = price * quantity
        available_quote = get_balance(quote_asset)
        if available_quote < cost:
            return (
                f"Insufficient {quote_asset} balance. Needed {cost:.2f}, available {available_quote:.2f}."
            )
    else:  # SELL
        available_base = get_balance(base_asset)
        if available_base < quantity:
            return (
                f"Insufficient {base_asset} balance. Needed {quantity:.6f}, available {available_base:.6f}."
            )
    return None


def _apply_balance_updates(action: str, pair: str, quantity: float, price: float) -> Dict[str, float]:
    assets = parse_pair(pair)
    base_asset = assets["base"]
    quote_asset = assets["quote"]

    if action == "BUY":
        cost = price * quantity
        adjust_balance(quote_asset, -cost)
        adjust_balance(base_asset, quantity)
    else:
        proceeds = price * quantity
        adjust_balance(base_asset, -quantity)
        adjust_balance(quote_asset, proceeds)

    return get_balance_snapshot()


def _build_trade_response(
    *,
    pair: str,
    action: str,
    rsi: float,
    price: Optional[float],
    quantity: Optional[float],
    status: str,
    trade_id: Optional[int],
    transaction_id: Optional[str],
    sequence_number: Optional[int],
    request_id: str,
    request_hash: str,
    balances: Dict[str, float],
    message: Optional[str] = None,
) -> TradeResponse:
    return TradeResponse(
        pair=pair,
        action=action,
        rsi=rsi,
        price=price,
        quantity=quantity,
        status=status,
        trade_id=trade_id,
        transaction_id=transaction_id,
        sequence_number=sequence_number,
        request_id=request_id,
        request_hash=request_hash,
        balances=balances,
        message=message,
    )


async def execute_buy(request: TradeRequest) -> TradeResponse:
    return await _execute_trade(action="BUY", request=request)


async def execute_sell(request: TradeRequest) -> TradeResponse:
    return await _execute_trade(action="SELL", request=request)


async def _execute_trade(action: str, request: TradeRequest) -> TradeResponse:
    pair = (request.pair or config.TRADING_PAIR).upper()
    quantity = request.quantity or config.DEFAULT_ORDER_QUANTITY
    quantity = round(quantity, 6)

    balances = _prepare_balances(pair)

    rsi = calculate_mock_rsi()
    price = get_mock_price(pair)

    request_hash = hash_request_payload(
        {
            "pair": pair,
            "action": action,
            "quantity": quantity,
            "request_id": request.request_id,
            "client_ref": request.client_ref or "",
        }
    )

    if trade_exists(request_hash=request_hash):
        logger.warning("Duplicate trade request detected (request_hash match). Returning existing record.")
        existing = fetch_trade_by_request_hash(request_hash)
        if existing:
            return _build_trade_response(
                pair=existing["pair"],
                action=existing["action"],
                rsi=existing["rsi"],
                price=existing.get("price"),
                quantity=existing.get("quantity"),
                status=existing.get("status", "executed"),
                trade_id=existing.get("id"),
                transaction_id=existing.get("transaction_id"),
                sequence_number=existing.get("sequence_number"),
                request_id=request.request_id,
                request_hash=request_hash,
                balances=existing.get("metadata", {}).get("balances", balances),
                message="Duplicate request ignored.",
            )

    sequence_number = _validate_sequence(pair, action, request.sequence_number)

    rsi_violation = _check_rsi_conditions(action, rsi, request.force)
    if rsi_violation:
        logger.warning(rsi_violation)
        return _build_trade_response(
            pair=pair,
            action=action,
            rsi=rsi,
            price=price,
            quantity=quantity,
            status="rejected",
            trade_id=None,
            transaction_id=None,
            sequence_number=sequence_number,
            request_id=request.request_id,
            request_hash=request_hash,
            balances=balances,
            message=rsi_violation,
        )

    balance_error = _validate_balances(action, pair, quantity, price)
    if balance_error:
        logger.warning(balance_error)
        return _build_trade_response(
            pair=pair,
            action=action,
            rsi=rsi,
            price=price,
            quantity=quantity,
            status="rejected",
            trade_id=None,
            transaction_id=None,
            sequence_number=sequence_number,
            request_id=request.request_id,
            request_hash=request_hash,
            balances=balances,
            message=balance_error,
        )

    transaction_id = generate_transaction_id()
    if trade_exists(transaction_id=transaction_id):
        logger.warning("Generated transaction ID already exists; regenerating.")
        transaction_id = generate_transaction_id()

    updated_balances = _apply_balance_updates(action, pair, quantity, price)

    metadata = {
        "balances": updated_balances,
        "request_id": request.request_id,
        "client_ref": request.client_ref,
    }

    trade_id = record_trade(
        transaction_id=transaction_id,
        sequence_number=sequence_number,
        request_hash=request_hash,
        pair=pair,
        action=action,
        rsi=rsi,
        price=price,
        quantity=quantity,
        status="executed",
        metadata=metadata,
    )

    logger.info(
        f"{action} trade executed: pair={pair} price={price:.2f} quantity={quantity:.6f} "
        f"transaction_id={transaction_id} sequence={sequence_number}"
    )

    return _build_trade_response(
        pair=pair,
        action=action,
        rsi=rsi,
        price=price,
        quantity=quantity,
        status="executed",
        trade_id=trade_id,
        transaction_id=transaction_id,
        sequence_number=sequence_number,
        request_id=request.request_id,
        request_hash=request_hash,
        balances=updated_balances,
        message="Trade executed successfully.",
    )

