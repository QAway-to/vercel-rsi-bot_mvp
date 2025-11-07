"""
Secure SQLite data access layer for the RSI trading bot.

This module provides basic persistence for trade history, balance management,
sequence tracking, and duplicate detection. In production, replace with a
managed database (PostgreSQL, MySQL, etc.).
"""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from loguru import logger

# Use /tmp directory for serverless environments (Vercel, AWS Lambda, etc.)
# This is the only writable directory in many serverless functions
DB_PATH = Path("/tmp/trades.db") if os.environ.get("VERCEL") or os.environ.get("LAMBDA_TASK_ROOT") else Path("trades.db")

_DB_INITIALIZED: bool = False


@contextmanager
def get_connection() -> sqlite3.Connection:
    """Context manager that yields a SQLite connection with row factory enabled."""
    ensure_initialized()
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def ensure_initialized() -> None:
    """Initialize database schema if it hasn't been created yet."""
    global _DB_INITIALIZED
    if _DB_INITIALIZED:
        return

    logger.debug(f"Initializing SQLite database at {DB_PATH}.")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()

    # Enable Write-Ahead Logging for better concurrency (best effort)
    try:
        cursor.execute("PRAGMA journal_mode=WAL;")
    except sqlite3.DatabaseError:
        logger.warning("Unable to enable WAL mode; continuing with default journal mode.")

    # Check if we're migrating from the old schema; if columns are missing, recreate tables
    cursor.execute("PRAGMA table_info(trades);")
    columns = {row[1] for row in cursor.fetchall()}
    if columns and {"transaction_id", "request_hash", "sequence_number"} - columns:
        logger.warning("Existing trades table uses legacy schema; recreating schema for security features.")
        cursor.execute("DROP TABLE IF EXISTS trades;")

    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT NOT NULL UNIQUE,
            sequence_number INTEGER NOT NULL,
            request_hash TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            pair TEXT NOT NULL,
            action TEXT NOT NULL,
            rsi REAL NOT NULL,
            price REAL,
            quantity REAL,
            status TEXT NOT NULL,
            metadata TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_trades_request_hash ON trades (request_hash);
        CREATE INDEX IF NOT EXISTS idx_trades_pair_action ON trades (pair, action);

        CREATE TABLE IF NOT EXISTS balances (
            asset TEXT PRIMARY KEY,
            balance REAL NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sequence_tracker (
            pair TEXT NOT NULL,
            action TEXT NOT NULL,
            last_sequence INTEGER NOT NULL,
            PRIMARY KEY (pair, action)
        );
        """
    )

    conn.commit()
    conn.close()
    _DB_INITIALIZED = True


def record_trade(
    *,
    transaction_id: str,
    sequence_number: int,
    request_hash: str,
    pair: str,
    action: str,
    rsi: float,
    price: Optional[float],
    quantity: Optional[float],
    status: str,
    metadata: Optional[Dict] = None,
) -> int:
    """Persist a trade and update sequence tracker."""
    timestamp = datetime.utcnow().isoformat()
    metadata_json = json.dumps(metadata or {}, ensure_ascii=False)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO trades (
                transaction_id, sequence_number, request_hash, timestamp,
                pair, action, rsi, price, quantity, status, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transaction_id,
                sequence_number,
                request_hash,
                timestamp,
                pair,
                action,
                rsi,
                price,
                quantity,
                status,
                metadata_json,
            ),
        )
        trade_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO sequence_tracker (pair, action, last_sequence)
            VALUES (?, ?, ?)
            ON CONFLICT(pair, action) DO UPDATE SET last_sequence=excluded.last_sequence
            """,
            (pair, action, sequence_number),
        )

    return trade_id


def trade_exists(*, transaction_id: Optional[str] = None, request_hash: Optional[str] = None) -> bool:
    """Check whether a trade already exists by transaction ID or request hash."""
    if not transaction_id and not request_hash:
        raise ValueError("Either transaction_id or request_hash must be provided")

    query = "SELECT 1 FROM trades WHERE "
    params: Tuple = ()
    clauses = []
    if transaction_id:
        clauses.append("transaction_id = ?")
        params += (transaction_id,)
    if request_hash:
        clauses.append("request_hash = ?")
        params += (request_hash,)
    query += " OR ".join(clauses) + " LIMIT 1"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
    return result is not None


def fetch_trade_by_request_hash(request_hash: str) -> Optional[Dict]:
    """Retrieve an existing trade by request hash if available."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trades WHERE request_hash = ? LIMIT 1", (request_hash,))
        row = cursor.fetchone()
        if not row:
            return None
        return _row_to_dict(row)


def _row_to_dict(row: sqlite3.Row) -> Dict:
    data = dict(row)
    if data.get("metadata"):
        try:
            data["metadata"] = json.loads(data["metadata"])
        except json.JSONDecodeError:
            data["metadata"] = {}
    else:
        data["metadata"] = {}
    return data


def get_recent_trades(limit: int = 10) -> List[Dict]:
    """Retrieve recent trades."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM trades
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
    return [_row_to_dict(row) for row in rows]


def get_trade_summary() -> Dict:
    """Get aggregated trade statistics."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM trades")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM trades WHERE action = 'BUY'")
        buy = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM trades WHERE action = 'SELL'")
        sell = cursor.fetchone()[0]

    return {
        "total_trades": total,
        "buy_trades": buy,
        "sell_trades": sell,
    }


def get_last_sequence(pair: str, action: str) -> int:
    """Return the last recorded sequence number for the pair/action combo."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT last_sequence FROM sequence_tracker WHERE pair = ? AND action = ?",
            (pair, action),
        )
        row = cursor.fetchone()
    return row[0] if row else 0


def get_next_sequence(pair: str, action: str) -> int:
    """Compute the next expected sequence number for a pair/action."""
    return get_last_sequence(pair, action) + 1


def get_balances() -> Dict[str, float]:
    """Return all tracked balances as a dictionary."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT asset, balance FROM balances")
        rows = cursor.fetchall()
    return {row[0]: row[1] for row in rows}


def get_balance(asset: str) -> float:
    """Return the balance for a specific asset (defaults to 0)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM balances WHERE asset = ?", (asset,))
        row = cursor.fetchone()
    return row[0] if row else 0.0


def set_balance(asset: str, balance: float) -> None:
    """Set the exact balance for an asset."""
    timestamp = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO balances (asset, balance, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(asset) DO UPDATE SET balance = excluded.balance, updated_at = excluded.updated_at
            """,
            (asset, balance, timestamp),
        )


def adjust_balance(asset: str, delta: float) -> float:
    """Adjust an asset balance by delta and return the new balance."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM balances WHERE asset = ?", (asset,))
        row = cursor.fetchone()
        current = row[0] if row else 0.0
        new_balance = current + delta
        timestamp = datetime.utcnow().isoformat()
        cursor.execute(
            """
            INSERT INTO balances (asset, balance, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(asset) DO UPDATE SET balance = excluded.balance, updated_at = excluded.updated_at
            """,
            (asset, new_balance, timestamp),
        )
    return new_balance


def ensure_initial_balance(asset: str, amount: float) -> None:
    """Ensure a minimum balance exists for an asset."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM balances WHERE asset = ?", (asset,))
        row = cursor.fetchone()
        if row is None:
            timestamp = datetime.utcnow().isoformat()
            cursor.execute(
                "INSERT INTO balances (asset, balance, updated_at) VALUES (?, ?, ?)",
                (asset, amount, timestamp),
            )


def get_balance_snapshot() -> Dict[str, float]:
    """Return current balances snapshot for inclusion in audit trail."""
    return get_balances()

