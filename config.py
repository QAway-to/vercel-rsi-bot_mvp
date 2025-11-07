"""
Configuration module for loading environment variables.
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""
    
    # Bybit API credentials (demo/mock)
    BYBIT_API_KEY: str = os.getenv("BYBIT_API_KEY", "demo_key")
    BYBIT_API_SECRET: str = os.getenv("BYBIT_API_SECRET", "demo_secret")
    
    # Telegram notification settings
    TELEGRAM_TOKEN: Optional[str] = os.getenv("TELEGRAM_TOKEN")
    TELEGRAM_CHAT_ID: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")
    
    # Trading pair
    TRADING_PAIR: str = os.getenv("TRADING_PAIR", "BTCUSDT")
    
    # RSI thresholds
    RSI_OVERSOLD: float = float(os.getenv("RSI_OVERSOLD", "20"))
    RSI_OVERBOUGHT: float = float(os.getenv("RSI_OVERBOUGHT", "80"))


# Global config instance
config = Config()

