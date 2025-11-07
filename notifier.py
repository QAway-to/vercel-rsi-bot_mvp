"""
Telegram notification sender for trade alerts.
"""
import requests
from typing import Optional
from loguru import logger
from config import config


def send_telegram_notification(message: str) -> dict:
    """
    Send a notification message to Telegram.
    
    Args:
        message: Message text to send
    
    Returns:
        Dictionary with response status
    """
    # Check if Telegram credentials are configured and not placeholders
    token = config.TELEGRAM_TOKEN
    chat_id = config.TELEGRAM_CHAT_ID
    
    if (not token or not chat_id or 
        token == "your_telegram_bot_token_here" or 
        chat_id == "your_telegram_chat_id_here" or
        "your_telegram" in token.lower() or
        "your_telegram" in chat_id.lower()):
        logger.warning("Telegram credentials not configured. Skipping notification.")
        return {
            "status": "skipped",
            "reason": "Telegram credentials not configured"
        }
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # Validate chat_id - should be numeric string or start with @
    try:
        # Try to convert to int if it's numeric
        if chat_id.lstrip('-').isdigit():
            chat_id = int(chat_id)
    except (ValueError, AttributeError):
        pass  # Keep as string if it's a username (starts with @)
    
    # Prepare payload without HTML parse_mode first (to avoid HTML errors)
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        # If 400 error, try to get detailed error message
        if response.status_code == 400:
            error_detail = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            error_description = error_detail.get('description', 'Bad Request')
            logger.error(f"Telegram API error 400: {error_description}")
            logger.debug(f"Full response: {error_detail}")
            
            # Try without HTML parse_mode if it was causing issues
            return {
                "status": "error",
                "error": f"Bad Request: {error_description}",
                "details": error_detail
            }
        
        response.raise_for_status()
        
        logger.info(f"Telegram notification sent successfully to chat {chat_id}")
        return {
            "status": "sent",
            "message": message
        }
    except requests.exceptions.HTTPError as e:
        # Get detailed error from response
        try:
            error_detail = e.response.json() if e.response else {}
            error_description = error_detail.get('description', str(e))
            logger.error(f"Telegram API HTTP error: {error_description}")
        except:
            error_description = str(e)
            logger.error(f"Telegram API HTTP error: {e}")
        
        return {
            "status": "error",
            "error": error_description
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Telegram notification: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


def format_trade_notification(pair: str, action: str, rsi: float, price: Optional[float] = None) -> str:
    """
    Format a trade notification message for Telegram.
    
    Args:
        pair: Trading pair
        action: Trade action ("BUY" or "SELL")
        rsi: RSI value
        price: Trade price (optional)
    
    Returns:
        Formatted message string
    """
    emoji = "🟢" if action == "BUY" else "🔴"
    
    message = f"""{emoji} Trade Executed

Pair: {pair}
Action: {action}
RSI: {rsi:.2f}"""
    
    if price:
        message += f"\nPrice: ${price:,.2f}"
    
    message += "\n\nThis is a simulated trade for testing purposes."
    
    return message

