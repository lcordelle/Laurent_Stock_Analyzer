"""
Trade Journal — SQLite-backed personal trading log.
Stores entries at ~/.cache/stock_analyzer/journal.db
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime

import yfinance as yf

logger = logging.getLogger(__name__)

_DB_PATH = Path.home() / '.cache' / 'stock_analyzer' / 'journal.db'


def _connect() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker      TEXT    NOT NULL,
                direction   TEXT    NOT NULL DEFAULT 'LONG',
                entry_date  TEXT    NOT NULL,
                entry_price REAL    NOT NULL,
                exit_date   TEXT,
                exit_price  REAL,
                shares      REAL    NOT NULL,
                notes       TEXT    DEFAULT '',
                tags        TEXT    DEFAULT '',
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.commit()


# Initialize DB on module load
init_db()


def add_trade(ticker: str, direction: str, entry_date: str,
              entry_price: float, shares: float,
              notes: str = '', tags: str = '') -> int:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO trades (ticker, direction, entry_date, entry_price, shares, notes, tags) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ticker.upper(), direction.upper(), entry_date, entry_price, shares, notes, tags)
        )
        conn.commit()
        return cur.lastrowid


def close_trade(trade_id: int, exit_date: str, exit_price: float) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE trades SET exit_date=?, exit_price=? WHERE id=?",
            (exit_date, exit_price, trade_id)
        )
        conn.commit()


def delete_trade(trade_id: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM trades WHERE id=?", (trade_id,))
        conn.commit()


def get_open_trades() -> list:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM trades WHERE exit_date IS NULL ORDER BY entry_date DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_closed_trades() -> list:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM trades WHERE exit_date IS NOT NULL ORDER BY exit_date DESC"
        ).fetchall()
    trades = [dict(r) for r in rows]
    for t in trades:
        t['pnl_pct'] = _calc_pnl_pct(t)
        t['pnl_dollars'] = _calc_pnl_dollars(t)
    return trades


def _calc_pnl_pct(trade: dict) -> float:
    if not trade.get('exit_price') or not trade.get('entry_price'):
        return 0.0
    raw = (trade['exit_price'] - trade['entry_price']) / trade['entry_price'] * 100
    return round(raw if trade['direction'] == 'LONG' else -raw, 2)


def _calc_pnl_dollars(trade: dict) -> float:
    if not trade.get('exit_price') or not trade.get('entry_price'):
        return 0.0
    raw = (trade['exit_price'] - trade['entry_price']) * trade['shares']
    return round(raw if trade['direction'] == 'LONG' else -raw, 2)


def get_pnl_summary() -> dict:
    trades = get_closed_trades()
    if not trades:
        return {'total_trades': 0, 'wins': 0, 'losses': 0, 'win_rate': 0,
                'total_pnl': 0, 'avg_pnl_pct': 0, 'best_trade': 0, 'worst_trade': 0}
    pnls = [t['pnl_pct'] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    return {
        'total_trades': len(trades),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': round(len(wins) / len(trades) * 100, 1),
        'total_pnl': round(sum(t['pnl_dollars'] for t in trades), 2),
        'avg_pnl_pct': round(sum(pnls) / len(pnls), 2),
        'best_trade': round(max(pnls), 2),
        'worst_trade': round(min(pnls), 2),
    }


def get_spy_return(start_date: str, end_date: str) -> float:
    """Fetch SPY return for a given period (for benchmark comparison)."""
    try:
        spy = yf.Ticker('SPY').history(start=start_date, end=end_date)
        if len(spy) < 2:
            return 0.0
        return round((spy['Close'].iloc[-1] - spy['Close'].iloc[0]) / spy['Close'].iloc[0] * 100, 2)
    except Exception:
        return 0.0
