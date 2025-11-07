"""
Simple SQLite database for storing simulated trade history.
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

# Use /tmp directory for serverless environments (Vercel, AWS Lambda, etc.)
# This is the only writable directory in serverless functions
# For local development, use current directory
if os.environ.get("VERCEL") or os.environ.get("LAMBDA_TASK_ROOT"):
    # Serverless environment - use /tmp
    DB_PATH = Path("/tmp/trades.db")
else:
    # Local development
    DB_PATH = Path("trades.db")


def init_db() -> None:
    """Initialize the SQLite database and create trades table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            pair TEXT NOT NULL,
            action TEXT NOT NULL,
            rsi REAL NOT NULL,
            price REAL,
            quantity REAL,
            status TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()


def save_trade(
    pair: str,
    action: str,
    rsi: float,
    price: Optional[float] = None,
    quantity: Optional[float] = None,
    status: str = "executed"
) -> int:
    """
    Save a simulated trade to the database.
    
    Args:
        pair: Trading pair (e.g., "BTCUSDT")
        action: Trade action ("BUY" or "SELL")
        rsi: RSI value at the time of trade
        price: Simulated price (optional)
        quantity: Simulated quantity (optional)
        status: Trade status (default: "executed")
    
    Returns:
        Trade ID
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    timestamp = datetime.utcnow().isoformat()
    
    cursor.execute("""
        INSERT INTO trades (timestamp, pair, action, rsi, price, quantity, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, pair, action, rsi, price, quantity, status))
    
    trade_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return trade_id


def get_recent_trades(limit: int = 10) -> List[Dict]:
    """
    Retrieve recent trades from the database.
    
    Args:
        limit: Maximum number of trades to retrieve
    
    Returns:
        List of trade dictionaries
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, timestamp, pair, action, rsi, price, quantity, status
        FROM trades
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    trades = []
    for row in rows:
        trades.append({
            "id": row[0],
            "timestamp": row[1],
            "pair": row[2],
            "action": row[3],
            "rsi": row[4],
            "price": row[5],
            "quantity": row[6],
            "status": row[7]
        })
    
    return trades


def get_trade_summary() -> Dict:
    """
    Get summary statistics of trades.
    
    Returns:
        Dictionary with trade statistics
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM trades")
    total_trades = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM trades WHERE action = 'BUY'")
    buy_trades = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM trades WHERE action = 'SELL'")
    sell_trades = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_trades": total_trades,
        "buy_trades": buy_trades,
        "sell_trades": sell_trades
    }

