"""
Advanced Analysis Routes
Options flow, insider transactions, short interest, institutional holdings,
market breadth, and candlestick pattern endpoints.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.auth import verify_token
from utils.advanced_financials import AdvancedFinancials
from utils.options_flow import get_options_flow, sentiment_label
from utils.market_breadth import get_market_regime
from utils.candlestick_patterns import detect_patterns, patterns_to_df
import yfinance as yf

router = APIRouter(tags=["advanced"])
logger = logging.getLogger(__name__)

_af = AdvancedFinancials()


# ── Market Breadth ────────────────────────────────────────────────────────────

@router.get("/market-breadth")
async def market_breadth(_: str = Depends(verify_token)):
    return get_market_regime()


# ── Options Flow ──────────────────────────────────────────────────────────────

@router.get("/advanced/options/{ticker}")
async def options_flow(ticker: str, _: str = Depends(verify_token)):
    data = get_options_flow(ticker.upper())
    summary = data.get("summary", {})
    pc = summary.get("pc_ratio", 0)
    label, color = sentiment_label(pc)
    data["sentiment_label"] = label
    data["sentiment_color"] = color
    return data


# ── Insider Transactions ──────────────────────────────────────────────────────

@router.get("/advanced/insider/{ticker}")
async def insider_transactions(ticker: str, _: str = Depends(verify_token)):
    try:
        df = _af.get_insider_transactions(ticker.upper())
        if df is None or len(df) == 0:
            return {"transactions": [], "cluster_buy": False}
        records = df.head(20).fillna("").to_dict(orient="records")
        # Cluster buy: ≥3 purchase transactions
        buys = [r for r in records if "buy" in str(r.get("Transaction", "")).lower()
                or "purchase" in str(r.get("Transaction", "")).lower()]
        return {"transactions": records, "cluster_buy": len(buys) >= 3, "buy_count": len(buys)}
    except Exception as e:
        logger.warning("Insider error %s: %s", ticker, e)
        return {"transactions": [], "cluster_buy": False, "error": str(e)}


# ── Short Interest ────────────────────────────────────────────────────────────

@router.get("/advanced/short-interest/{ticker}")
async def short_interest(ticker: str, _: str = Depends(verify_token)):
    try:
        data = _af.get_short_interest(ticker.upper())
        if not data:
            return {"available": False}
        short_pct = data.get("short_percent_of_float", 0)
        days = data.get("short_ratio", 0)
        squeeze_risk = "High" if short_pct > 20 and days > 5 else \
                       "Moderate" if short_pct > 10 else "Low"
        return {**data, "available": True, "squeeze_risk": squeeze_risk}
    except Exception as e:
        return {"available": False, "error": str(e)}


# ── Institutional Holdings ────────────────────────────────────────────────────

@router.get("/advanced/institutional/{ticker}")
async def institutional_holdings(ticker: str, _: str = Depends(verify_token)):
    try:
        df = _af.get_institutional_holdings(ticker.upper())
        if df is None or len(df) == 0:
            return {"holders": [], "available": False}
        records = df.head(15).fillna("").to_dict(orient="records")
        return {"holders": records, "available": True}
    except Exception as e:
        return {"holders": [], "available": False, "error": str(e)}


# ── Candlestick Patterns ──────────────────────────────────────────────────────

@router.get("/advanced/patterns/{ticker}")
async def candlestick_patterns(ticker: str, period: str = "3mo",
                                _: str = Depends(verify_token)):
    try:
        hist = yf.Ticker(ticker.upper()).history(period=period)
        if hist.empty:
            return {"patterns": [], "bullish": 0, "bearish": 0, "neutral": 0}
        patterns = detect_patterns(hist)
        bullish = sum(1 for p in patterns if p["direction"] == "bullish")
        bearish = sum(1 for p in patterns if p["direction"] == "bearish")
        neutral = sum(1 for p in patterns if p["direction"] == "neutral")
        # Serialize dates
        for p in patterns:
            if hasattr(p["date"], "strftime"):
                p["date"] = p["date"].strftime("%Y-%m-%d")
            else:
                p["date"] = str(p["date"])[:10]
        return {"patterns": patterns, "bullish": bullish, "bearish": bearish, "neutral": neutral}
    except Exception as e:
        return {"patterns": [], "error": str(e)}
