"""
FastAPI application for RSI-based trading bot simulation.
Designed for deployment on Vercel.
"""
from datetime import datetime
from pathlib import Path
import sys

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from auth import verify_api_key
from config import config
from db import get_recent_trades
from notifier import format_trade_notification, send_telegram_notification
from schemas import StatusResponse, TradeRequest, TradeResponse
from trader import execute_buy, execute_sell, get_trading_status

# Configure Loguru
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO",
)

# Initialize FastAPI app
app = FastAPI(
    title="RSI Trading Bot Demo",
    description="Simulated RSI-based trading bot for Bybit futures (testing only)",
    version="1.1.0",
)

# Initialize database lazily (not on startup for serverless)
# Database will be initialized on first use

# Mount static files directory
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/")
async def root():
    """Serve the web interface."""
    index_path = static_path / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {
        "name": "RSI Trading Bot Demo",
        "version": app.version,
        "description": "Simulated RSI-based trading bot for testing",
        "endpoints": {
            "health": "/health",
            "status": "/status",
            "buy": "/buy (POST)",
            "sell": "/sell (POST)",
            "notify": "/notify (POST)",
            "trades": "/trades (GET)",
        },
    }


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "name": "RSI Trading Bot Demo",
        "version": app.version,
        "description": "Simulated RSI-based trading bot for testing",
        "endpoints": {
            "health": "/health",
            "status": "/status",
            "buy": "/buy (POST)",
            "sell": "/sell (POST)",
            "notify": "/notify (POST)",
            "trades": "/trades (GET)",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "rsi-trading-bot",
    }


@app.get("/status", response_model=StatusResponse)
async def status_endpoint() -> StatusResponse:
    """Get current trading status including RSI, price, balances, and trade summary."""
    try:
        return await get_trading_status()
    except Exception as exc:  # pragma: no cover - defensive programming
        logger.exception("Error getting status")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {exc}") from exc


@app.post("/buy", response_model=TradeResponse, dependencies=[Depends(verify_api_key)])
async def buy(trade_request: TradeRequest) -> TradeResponse:
    """Simulate a BUY trade with security checks."""
    try:
        result = await execute_buy(trade_request)
        if result.status == "executed":
            message = format_trade_notification(
                pair=result.pair,
                action=result.action,
                rsi=result.rsi,
                price=result.price,
            )
            send_telegram_notification(message)
        return result
    except ValueError as exc:
        logger.warning(f"BUY validation error: {exc}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive programming
        logger.exception("Unexpected error executing BUY")
        raise HTTPException(status_code=500, detail=f"Failed to execute BUY: {exc}") from exc


@app.post("/sell", response_model=TradeResponse, dependencies=[Depends(verify_api_key)])
async def sell(trade_request: TradeRequest) -> TradeResponse:
    """Simulate a SELL trade with security checks."""
    try:
        result = await execute_sell(trade_request)
        if result.status == "executed":
            message = format_trade_notification(
                pair=result.pair,
                action=result.action,
                rsi=result.rsi,
                price=result.price,
            )
            send_telegram_notification(message)
        return result
    except ValueError as exc:
        logger.warning(f"SELL validation error: {exc}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive programming
        logger.exception("Unexpected error executing SELL")
        raise HTTPException(status_code=500, detail=f"Failed to execute SELL: {exc}") from exc


@app.post("/notify", dependencies=[Depends(verify_api_key)])
async def notify():
    """Send a test notification to Telegram."""
    try:
        test_message = (
            "🧪 Test notification from RSI Trading Bot Demo\n\nThis is a test message to verify Telegram integration."
        )
        result = send_telegram_notification(test_message)
        return result
    except Exception as exc:  # pragma: no cover - defensive programming
        logger.exception("Error sending notification")
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {exc}") from exc


@app.get("/trades")
async def get_trades(limit: int = 10):
    """Get recent trade history."""
    try:
        trades = get_recent_trades(limit=limit)
        return {"trades": trades, "count": len(trades)}
    except Exception as exc:  # pragma: no cover - defensive programming
        logger.exception("Error retrieving trades")
        raise HTTPException(status_code=500, detail=f"Failed to get trades: {exc}") from exc


# Vercel serverless function handler
# For Vercel, we export the app directly as ASGI application
# Vercel's @vercel/python automatically handles FastAPI apps

