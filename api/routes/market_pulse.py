from __future__ import annotations
import asyncio
import logging
import time
from typing import Optional
import yfinance as yf
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from api.auth import verify_token
from utils.market_breadth import get_market_regime

router = APIRouter(tags=["market_pulse"])
logger = logging.getLogger(__name__)

_PULSE_CACHE_TTL = 120  # 2 minutes

INDICES = [
    ("S&P 500",      "^GSPC"),
    ("NASDAQ",       "^IXIC"),
    ("DOW",          "^DJI"),
    ("Russell 2000", "^RUT"),
    ("VIX",          "^VIX"),
    ("Gold",         "GLD"),
    ("Bonds 10Y",    "TLT"),
    ("Bitcoin",      "BTC-USD"),
]

SECTOR_ETFS = [
    ("Technology",  "XLK"),
    ("Healthcare",  "XLV"),
    ("Financials",  "XLF"),
    ("Energy",      "XLE"),
    ("Utilities",   "XLU"),
    ("Industrials", "XLI"),
    ("Cons. Disc.",  "XLY"),
    ("Materials",   "XLB"),
]


class IndexQuote(BaseModel):
    label: str
    symbol: str
    price: Optional[float] = None
    change_pct: Optional[float] = None
    up: bool = True


class SectorPerf(BaseModel):
    sector: str
    change_pct: Optional[float] = None
    up: bool = True


class MarketPulseResponse(BaseModel):
    indices: list[IndexQuote]
    sectors: list[SectorPerf]
    market_breadth: Optional[str] = None


_pulse_cache: Optional[MarketPulseResponse] = None
_pulse_cache_ts: float = 0.0


def _fast_info_quote(symbol: str) -> tuple[float | None, float | None]:
    """Return (price, change_pct) using fast_info — works after market close."""
    info = yf.Ticker(symbol).fast_info
    price = info.get("lastPrice") or info.get("regularMarketPrice")
    prev = info.get("regularMarketPreviousClose") or info.get("previousClose")
    if price is None:
        return None, None
    price = float(price)
    chg = round((price - float(prev)) / float(prev) * 100, 2) if prev and float(prev) > 0 else None
    return round(price, 2), chg


def _fetch_quote(label: str, symbol: str) -> IndexQuote:
    try:
        price, chg = _fast_info_quote(symbol)
        if price is None:
            return IndexQuote(label=label, symbol=symbol)
        return IndexQuote(label=label, symbol=symbol, price=price, change_pct=chg, up=(chg or 0) >= 0)
    except Exception as e:
        logger.warning("Quote failed for %s: %s", symbol, e)
        return IndexQuote(label=label, symbol=symbol)


def _fetch_sector(sector: str, symbol: str) -> SectorPerf:
    try:
        _, chg = _fast_info_quote(symbol)
        if chg is None:
            return SectorPerf(sector=sector)
        return SectorPerf(sector=sector, change_pct=chg, up=chg >= 0)
    except Exception as e:
        logger.warning("Sector quote failed for %s: %s", symbol, e)
        return SectorPerf(sector=sector)


@router.get("/market-pulse", response_model=MarketPulseResponse)
async def get_market_pulse(_: str = Depends(verify_token)):
    global _pulse_cache, _pulse_cache_ts
    if _pulse_cache is not None and (time.time() - _pulse_cache_ts) < _PULSE_CACHE_TTL:
        return _pulse_cache

    loop = asyncio.get_event_loop()

    index_tasks = [loop.run_in_executor(None, _fetch_quote, lbl, sym) for lbl, sym in INDICES]
    sector_tasks = [loop.run_in_executor(None, _fetch_sector, sec, sym) for sec, sym in SECTOR_ETFS]

    indices_raw, sectors_raw = await asyncio.gather(
        asyncio.gather(*index_tasks, return_exceptions=True),
        asyncio.gather(*sector_tasks, return_exceptions=True),
    )

    indices: list[IndexQuote] = []
    for r in indices_raw:
        if isinstance(r, IndexQuote):
            indices.append(r)

    sectors: list[SectorPerf] = []
    for r in sectors_raw:
        if isinstance(r, SectorPerf):
            sectors.append(r)

    valid_sectors = [s for s in sectors if s.change_pct is not None]
    if valid_sectors:
        up_count = sum(1 for s in valid_sectors if s.up)
        breadth_pct = up_count / len(valid_sectors)
        breadth = "Broad Advance" if breadth_pct >= 0.75 else \
                  "Mixed" if breadth_pct >= 0.4 else "Broad Decline"
    else:
        breadth = None

    result = MarketPulseResponse(indices=indices, sectors=sectors, market_breadth=breadth)
    if any(i.price is not None for i in indices):
        _pulse_cache = result
        _pulse_cache_ts = time.time()
    return result


@router.get("/market-breadth")
async def market_breadth(_: str = Depends(verify_token)):
    return get_market_regime()
