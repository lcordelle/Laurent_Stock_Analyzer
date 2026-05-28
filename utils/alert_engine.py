"""
Price and Signal Alert Engine
Stores alert rules as JSON; sends Telegram notifications when triggered.

Environment variables required for Telegram:
  TELEGRAM_BOT_TOKEN  — bot token from @BotFather
  TELEGRAM_CHAT_ID    — your personal chat ID
"""

import json
import logging
import os
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

import requests
import yfinance as yf

logger = logging.getLogger(__name__)

_ALERTS_PATH = Path.home() / '.cache' / 'stock_analyzer' / 'alerts.json'
_POLL_INTERVAL = 60  # seconds between checks
_started = False
_lock = threading.Lock()

CONDITION_LABELS = {
    'price_above': 'Price Above',
    'price_below': 'Price Below',
    'rsi_above': 'RSI Above',
    'rsi_below': 'RSI Below',
}


# ── Persistence ────────────────────────────────────────────────────────────────

def _load() -> list:
    _ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not _ALERTS_PATH.exists():
        return []
    try:
        return json.loads(_ALERTS_PATH.read_text())
    except Exception:
        return []


def _save(alerts: list) -> None:
    _ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _ALERTS_PATH.write_text(json.dumps(alerts, indent=2))


# ── Public API ─────────────────────────────────────────────────────────────────

def get_alerts() -> list:
    return _load()


def add_alert(ticker: str, condition: str, threshold: float) -> str:
    alerts = _load()
    alert_id = str(uuid.uuid4())[:8]
    alerts.append({
        'id': alert_id,
        'ticker': ticker.upper(),
        'condition': condition,
        'threshold': threshold,
        'created': datetime.now().isoformat(),
        'fired': False,
        'fired_at': None,
    })
    _save(alerts)
    return alert_id


def delete_alert(alert_id: str) -> None:
    alerts = [a for a in _load() if a['id'] != alert_id]
    _save(alerts)


def reset_alert(alert_id: str) -> None:
    alerts = _load()
    for a in alerts:
        if a['id'] == alert_id:
            a['fired'] = False
            a['fired_at'] = None
    _save(alerts)


# ── Check logic ────────────────────────────────────────────────────────────────

def _get_current_price(ticker: str):
    try:
        info = yf.Ticker(ticker).fast_info
        return float(info.get('lastPrice') or info.get('regularMarketPrice') or 0) or None
    except Exception:
        return None


def _get_rsi(ticker: str, period: int = 14):
    try:
        import pandas as pd
        hist = yf.Ticker(ticker).history(period='3mo')
        if len(hist) < period + 1:
            return None
        delta = hist['Close'].diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = (-delta.clip(upper=0)).rolling(period).mean()
        rs = gain / loss.replace(0, float('nan'))
        rsi = 100 - (100 / (1 + rs))
        return round(float(rsi.iloc[-1]), 1)
    except Exception:
        return None


def _check_alert(alert: dict) -> bool:
    condition = alert['condition']
    threshold = alert['threshold']
    ticker = alert['ticker']

    if condition in ('price_above', 'price_below'):
        price = _get_current_price(ticker)
        if price is None:
            return False
        return price > threshold if condition == 'price_above' else price < threshold

    if condition in ('rsi_above', 'rsi_below'):
        rsi = _get_rsi(ticker)
        if rsi is None:
            return False
        return rsi > threshold if condition == 'rsi_above' else rsi < threshold

    return False


# ── Notification ───────────────────────────────────────────────────────────────

def _send_telegram(message: str) -> None:
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        logger.info("Telegram not configured — alert not sent: %s", message)
        return
    try:
        url = f'https://api.telegram.org/bot{token}/sendMessage'
        requests.post(url, json={'chat_id': chat_id, 'text': message}, timeout=5)
    except Exception as e:
        logger.warning("Telegram send failed: %s", e)


def _format_message(alert: dict) -> str:
    label = CONDITION_LABELS.get(alert['condition'], alert['condition'])
    return (
        f"🔔 Stock Alert Triggered!\n"
        f"Ticker: {alert['ticker']}\n"
        f"Condition: {label} {alert['threshold']}\n"
        f"Fired at: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )


# ── Background thread ──────────────────────────────────────────────────────────

def _poll_loop() -> None:
    while True:
        try:
            with _lock:
                alerts = _load()
                changed = False
                for alert in alerts:
                    if alert.get('fired'):
                        continue
                    try:
                        if _check_alert(alert):
                            alert['fired'] = True
                            alert['fired_at'] = datetime.now().isoformat()
                            _send_telegram(_format_message(alert))
                            logger.info("Alert fired: %s", alert)
                            changed = True
                    except Exception as e:
                        logger.warning("Alert check failed %s: %s", alert.get('id'), e)
                if changed:
                    _save(alerts)
        except Exception as e:
            logger.error("Alert poll error: %s", e)
        time.sleep(_POLL_INTERVAL)


def start_alert_engine() -> None:
    global _started
    if _started:
        return
    _started = True
    threading.Thread(target=_poll_loop, daemon=True, name='alert-engine').start()
    logger.info("Alert engine started (polling every %ds)", _POLL_INTERVAL)
