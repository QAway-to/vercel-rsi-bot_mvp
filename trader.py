"""
Simulated RSI-based trading logic.
"""
import random
from typing import Dict, Optional
from loguru import logger
from config import config
from db import save_trade, get_trade_summary


def calculate_mock_rsi() -> float:
    """
    Generate a mock RSI value for demonstration.
    In production, this would calculate RSI from real market data.
    
    Returns:
        Random RSI value between 10 and 90
    """
    return round(random.uniform(10, 90), 2)


def get_mock_price(pair: str = None) -> float:
    """
    Generate a mock price for the trading pair.
    In production, this would fetch real price from Bybit API.
    
    Args:
        pair: Trading pair (optional, uses config default)
    
    Returns:
        Simulated price
    """
    # Mock prices for common pairs
    mock_prices = {
        "BTCUSDT": 45000.0,
        "ETHUSDT": 2500.0,
        "BNBUSDT": 300.0
    }
    
    pair = pair or config.TRADING_PAIR
    base_price = mock_prices.get(pair, 100.0)
    
    # Add some random variation (±2%)
    variation = random.uniform(-0.02, 0.02)
    return round(base_price * (1 + variation), 2)


async def get_trading_status() -> Dict:
    """
    Get current trading status including RSI and trade summary.
    
    Returns:
        Dictionary with status information
    """
    rsi = calculate_mock_rsi()
    price = get_mock_price()
    summary = get_trade_summary()
    
    return {
        "pair": config.TRADING_PAIR,
        "rsi": rsi,
        "price": price,
        "rsi_oversold": config.RSI_OVERSOLD,
        "rsi_overbought": config.RSI_OVERBOUGHT,
        "trades": summary
    }


async def execute_buy() -> Dict:
    """
    Simulate a BUY trade if RSI is below oversold threshold.
    
    Returns:
        Dictionary with trade execution details
    """
    rsi = calculate_mock_rsi()
    price = get_mock_price()
    pair = config.TRADING_PAIR
    
    # Check if RSI is in oversold territory
    if rsi < config.RSI_OVERSOLD:
        # Simulate trade execution
        quantity = round(random.uniform(0.001, 0.01), 6)
        
        trade_id = save_trade(
            pair=pair,
            action="BUY",
            rsi=rsi,
            price=price,
            quantity=quantity,
            status="executed"
        )
        
        logger.info(f"BUY trade executed: {pair} @ ${price} (RSI: {rsi})")
        
        return {
            "pair": pair,
            "action": "BUY",
            "rsi": rsi,
            "price": price,
            "quantity": quantity,
            "status": "executed",
            "trade_id": trade_id
        }
    else:
        logger.warning(f"BUY signal ignored: RSI ({rsi}) is not below oversold threshold ({config.RSI_OVERSOLD})")
        
        return {
            "pair": pair,
            "action": "BUY",
            "rsi": rsi,
            "status": "rejected",
            "reason": f"RSI ({rsi}) is not below oversold threshold ({config.RSI_OVERSOLD})"
        }


async def execute_sell() -> Dict:
    """
    Simulate a SELL trade if RSI is above overbought threshold.
    
    Returns:
        Dictionary with trade execution details
    """
    rsi = calculate_mock_rsi()
    price = get_mock_price()
    pair = config.TRADING_PAIR
    
    # Check if RSI is in overbought territory
    if rsi > config.RSI_OVERBOUGHT:
        # Simulate trade execution
        quantity = round(random.uniform(0.001, 0.01), 6)
        
        trade_id = save_trade(
            pair=pair,
            action="SELL",
            rsi=rsi,
            price=price,
            quantity=quantity,
            status="executed"
        )
        
        logger.info(f"SELL trade executed: {pair} @ ${price} (RSI: {rsi})")
        
        return {
            "pair": pair,
            "action": "SELL",
            "rsi": rsi,
            "price": price,
            "quantity": quantity,
            "status": "executed",
            "trade_id": trade_id
        }
    else:
        logger.warning(f"SELL signal ignored: RSI ({rsi}) is not above overbought threshold ({config.RSI_OVERBOUGHT})")
        
        return {
            "pair": pair,
            "action": "SELL",
            "rsi": rsi,
            "status": "rejected",
            "reason": f"RSI ({rsi}) is not above overbought threshold ({config.RSI_OVERBOUGHT})"
        }

