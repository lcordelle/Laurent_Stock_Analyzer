from __future__ import annotations
import asyncio
import logging
import time
from typing import Optional
import yfinance as yf
from yfinance import EquityQuery
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from api.auth import verify_token
from api.routes.opportunities import _quick_scan
import config

router = APIRouter(tags=["penny-stocks"])
logger = logging.getLogger(__name__)

CACHE_TTL = 30 * 60
_cache: Optional[dict] = None
_cache_ts: float = 0.0

# OTC/pink-sheet exchanges — excluded from scan
_OTC_EXCHANGES = {"PNK", "OQB", "OQX", "OBB", "PINK", "OTC"}

# Static fallback if Yahoo screener is unavailable
_FALLBACK_UNIVERSE = [
    "PLUG", "FCEL", "BLNK", "WKHS", "NKLA", "MVST", "VLCN", "IDEX", "GOEV",
    "BTBT", "HIVE", "CAN", "EBON", "CIFR", "MIGI", "BTCS", "IREN",
    "TLRY", "ACB", "CGC", "SNDL", "OGI", "GRWG", "HITI", "HEXO",
    "VBIV", "MNMD", "SRTS", "NKTR", "ACRX", "ONCT", "CTIC", "LXRX", "MRSN",
    "SOUN", "BBAI", "CXAI", "GFAI", "LIDR", "OUST",
    "GORO", "HYMC", "HL", "EXK", "FSM",
    "GTE", "TELL", "INDO", "REI", "LEXX", "BORR", "SDRL",
    "ESEA", "TOPS", "SINO",
    "CLOV", "HIMS", "BKSY", "ASTR",
]


def _fetch_dynamic_universe() -> list[str]:
    """Pull up to 250 liquid US penny stocks from Yahoo Finance screener."""
    try:
        q = EquityQuery('and', [
            EquityQuery('lt', ['eodprice', config.PENNY_MAX_PRICE]),
            EquityQuery('gt', ['eodprice', config.PENNY_MIN_PRICE]),
            EquityQuery('gt', ['avgdailyvol3m', config.PENNY_MIN_VOLUME]),
            EquityQuery('gt', ['intradaymarketcap', config.PENNY_MIN_MCAP]),
            EquityQuery('eq', ['region', 'us']),
        ])
        result = yf.screen(q, size=250, sortField='avgdailyvol3m', sortAsc=False)
        quotes = result.get('quotes', [])
        tickers = [
            qt['symbol'] for qt in quotes
            if qt.get('exchange', 'PNK') not in _OTC_EXCHANGES
            and '.' not in qt['symbol']
        ]
        if tickers:
            logger.info(f"Dynamic universe: {len(tickers)} tickers from Yahoo screener")
            return tickers
    except Exception as e:
        logger.warning(f"Yahoo screener failed, using fallback: {e}")
    return _FALLBACK_UNIVERSE


_SECTOR_TO_CATEGORY: dict[str, str] = {
    "Healthcare": "Biotech / Pharma",
    "Technology": "Small Cap Tech / AI",
    "Communication Services": "Small Cap Tech / AI",
    "Energy": "Oil & Gas",
    "Basic Materials": "Metals / Mining",
    "Industrials": "Industrials",
    "Consumer Cyclical": "Consumer",
    "Consumer Defensive": "Consumer",
    "Financial Services": "Financial",
    "Real Estate": "Real Estate",
    "Utilities": "Utilities",
}

_TICKER_OVERRIDES: dict[str, str] = {
    "PLUG": "Clean Energy / EV", "FCEL": "Clean Energy / EV", "BLNK": "Clean Energy / EV",
    "WKHS": "Clean Energy / EV", "NKLA": "Clean Energy / EV", "LCID": "Clean Energy / EV",
    "BTBT": "Crypto / Mining", "HIVE": "Crypto / Mining", "CAN": "Crypto / Mining",
    "CIFR": "Crypto / Mining", "MIGI": "Crypto / Mining", "BTCS": "Crypto / Mining", "IREN": "Crypto / Mining",
    "TLRY": "Cannabis", "ACB": "Cannabis", "CGC": "Cannabis", "SNDL": "Cannabis",
    "OGI": "Cannabis", "GRWG": "Cannabis", "HITI": "Cannabis", "HEXO": "Cannabis",
    "ESEA": "Shipping / Transport", "TOPS": "Shipping / Transport", "SINO": "Shipping / Transport",
}


def _categorise(ticker: str, sector: Optional[str] = None) -> str:
    if ticker in _TICKER_OVERRIDES:
        return _TICKER_OVERRIDES[ticker]
    if sector and sector in _SECTOR_TO_CATEGORY:
        return _SECTOR_TO_CATEGORY[sector]
    return "Other"


def _penny_why_now(result: dict) -> str:
    rsi = result.get("rsi") or 50
    macd = result.get("macd_signal") or ""
    signal = result.get("signal") or ""
    trend = result.get("trend") or ""
    upside = result.get("analyst_upside")
    momentum = result.get("week52_momentum")
    rr = result.get("risk_reward")

    if rsi < 30 and macd == "BULLISH":
        return f"Deeply oversold (RSI {rsi:.0f}) with MACD turning bullish — high-risk reversal setup"
    if rsi < 35:
        return f"Oversold at RSI {rsi:.0f} — potential snap-back candidate with defined stop"
    if "STRONG BUY" in signal:
        return "All technical indicators aligned bullish — maximum buy signal strength"
    if trend == "STRONG UPTREND" and macd == "BULLISH":
        return "Price in strong uptrend with MACD confirmation — momentum continuation play"
    if upside is not None and upside > 100:
        return f"Analyst target implies +{upside:.0f}% upside — speculative value setup"
    if upside is not None and upside > 50:
        return f"+{upside:.0f}% to analyst target — significant upside if thesis plays out"
    if momentum is not None and momentum < 30:
        return f"Near 52-week low ({momentum:.0f}% above low) — contrarian entry with catalysts needed"
    if rr is not None and rr > 2.0:
        return f"Risk/reward ratio {rr:.1f}x — favorable asymmetry relative to penny stock risk"
    if macd == "BULLISH" and "BUY" in signal:
        return "MACD bullish with buy signal confirmed — technical setup for near-term move"
    return "BUY signal active — speculative entry with stop-loss discipline essential"


def _is_buy(result: dict) -> bool:
    signal = result.get("signal") or ""
    rsi = result.get("rsi") or 50
    macd = result.get("macd_signal") or ""
    vf = result.get("vf_score") or 0
    if "BUY" in signal:
        return True
    if rsi < 35 and macd == "BULLISH" and vf >= 20:
        return True
    return False


def _penny_scan(ticker: str) -> Optional[dict]:
    result = _quick_scan(ticker)
    if result is None:
        return None
    price = result.get("price") or 999
    mcap = result.get("market_cap") or 0
    if price >= config.PENNY_MAX_PRICE:
        return None
    if mcap < config.PENNY_MIN_MCAP:
        return None
    if not _is_buy(result):
        return None
    result["penny_category"] = _categorise(ticker, result.get("sector"))
    result["why_now"] = _penny_why_now(result)
    return result


async def _run_scan() -> dict:
    global _cache, _cache_ts
    loop = asyncio.get_event_loop()

    universe = await loop.run_in_executor(None, _fetch_dynamic_universe)
    logger.info(f"Scanning {len(universe)} penny stock candidates")

    async def scan_one(t: str):
        return await loop.run_in_executor(None, _penny_scan, t)

    results = await asyncio.gather(*[scan_one(t) for t in universe], return_exceptions=True)
    qualified = [r for r in results if isinstance(r, dict)]
    qualified.sort(key=lambda x: x.get("combined_score", 0), reverse=True)
    top30 = qualified[:30]

    payload = {
        "stocks": top30,
        "total_scanned": len(universe),
        "total_qualified": len(qualified),
        "cached_at": time.time(),
    }
    _cache = payload
    _cache_ts = time.time()
    return payload


class PennyStockItem(BaseModel):
    ticker: str
    name: Optional[str] = None
    penny_category: Optional[str] = None
    sector: Optional[str] = None
    price: Optional[float] = None
    market_cap: Optional[int] = None
    vf_score: Optional[int] = None
    signal: Optional[str] = None
    confidence: Optional[int] = None
    rsi: Optional[float] = None
    rsi_signal: Optional[str] = None
    macd_signal: Optional[str] = None
    trend: Optional[str] = None
    stop_loss: Optional[float] = None
    tp1: Optional[float] = None
    tp2: Optional[float] = None
    tp3: Optional[float] = None
    risk_reward: Optional[float] = None
    analyst_target: Optional[float] = None
    analyst_upside: Optional[float] = None
    week52_momentum: Optional[float] = None
    pe_ratio: Optional[float] = None
    revenue_growth: Optional[float] = None
    combined_score: Optional[float] = None
    why_now: Optional[str] = None


class PennyStocksResponse(BaseModel):
    stocks: list[PennyStockItem]
    total_scanned: int
    total_qualified: int
    cached_at: Optional[float] = None


@router.get("/penny-stocks", response_model=PennyStocksResponse)
async def get_penny_stocks(_: str = Depends(verify_token)):
    global _cache, _cache_ts
    if _cache and (time.time() - _cache_ts) < CACHE_TTL:
        return PennyStocksResponse(**_cache)
    payload = await _run_scan()
    return PennyStocksResponse(**payload)


@router.post("/penny-stocks/refresh", response_model=PennyStocksResponse)
async def refresh_penny_stocks(_: str = Depends(verify_token)):
    global _cache_ts
    _cache_ts = 0.0
    payload = await _run_scan()
    return PennyStocksResponse(**payload)
