"""
FastAPI application for RSI-based trading bot simulation.
Designed for deployment on Vercel.
"""
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger
import sys
from pathlib import Path

from config import config
from trader import get_trading_status, execute_buy, execute_sell
from notifier import send_telegram_notification, format_trade_notification
from db import init_db, get_recent_trades

# Configure Loguru
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)

# Initialize FastAPI app
app = FastAPI(
    title="RSI Trading Bot Demo",
    description="Simulated RSI-based trading bot for Bybit futures (testing only)",
    version="1.0.0"
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
    # Fallback to JSON if static files not available
    return {
        "name": "RSI Trading Bot Demo",
        "version": "1.0.0",
        "description": "Simulated RSI-based trading bot for testing",
        "endpoints": {
            "health": "/health",
            "status": "/status",
            "buy": "/buy (POST)",
            "sell": "/sell (POST)",
            "notify": "/notify (POST)"
        }
    }


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "name": "RSI Trading Bot Demo",
        "version": "1.0.0",
        "description": "Simulated RSI-based trading bot for testing",
        "endpoints": {
            "health": "/health",
            "status": "/status",
            "buy": "/buy (POST)",
            "sell": "/sell (POST)",
            "notify": "/notify (POST)",
            "trades": "/trades (GET)"
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    Returns application status and timestamp.
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "rsi-trading-bot"
    }


@app.get("/status")
async def status():
    """
    Get current trading status including RSI, price, and trade summary.
    """
    try:
        status_data = await get_trading_status()
        return JSONResponse(content=status_data)
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to get status", "message": str(e)}
        )


@app.post("/buy")
async def buy():
    """
    Simulate a BUY trade if RSI is below oversold threshold.
    """
    try:
        result = await execute_buy()
        
        # Send Telegram notification if trade was executed
        if result.get("status") == "executed":
            message = format_trade_notification(
                pair=result["pair"],
                action=result["action"],
                rsi=result["rsi"],
                price=result.get("price")
            )
            send_telegram_notification(message)
        
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error executing BUY: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to execute BUY", "message": str(e)}
        )


@app.post("/sell")
async def sell():
    """
    Simulate a SELL trade if RSI is above overbought threshold.
    """
    try:
        result = await execute_sell()
        
        # Send Telegram notification if trade was executed
        if result.get("status") == "executed":
            message = format_trade_notification(
                pair=result["pair"],
                action=result["action"],
                rsi=result["rsi"],
                price=result.get("price")
            )
            send_telegram_notification(message)
        
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error executing SELL: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to execute SELL", "message": str(e)}
        )


@app.post("/notify")
async def notify():
    """
    Send a test notification to Telegram.
    """
    try:
        test_message = "🧪 Test notification from RSI Trading Bot Demo\n\nThis is a test message to verify Telegram integration."
        result = send_telegram_notification(test_message)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to send notification", "message": str(e)}
        )


@app.get("/trades")
async def get_trades(limit: int = 10):
    """
    Get recent trade history.
    
    Args:
        limit: Maximum number of trades to retrieve (default: 10)
    """
    try:
        trades = get_recent_trades(limit=limit)
        return JSONResponse(content={"trades": trades, "count": len(trades)})
    except Exception as e:
        logger.error(f"Error getting trades: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to get trades", "message": str(e)}
        )


# Vercel serverless function handler
# For Vercel, we export the app directly as ASGI application
# Vercel's @vercel/python automatically handles FastAPI apps

