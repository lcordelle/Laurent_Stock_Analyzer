from __future__ import annotations
import asyncio
import logging
from typing import Optional
import yfinance as yf
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from api.auth import verify_token

router = APIRouter(tags=["market_pulse"])
logger = logging.getLogger(__name__)

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


def _fetch_quote(label: str, symbol: str) -> IndexQuote:
    try:
        hist = yf.Ticker(symbol).history(period="5d")
        if hist is None or len(hist) < 2:
            return IndexQuote(label=label, symbol=symbol)
        price = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2])
        chg = round((price - prev) / prev * 100, 2) if prev > 0 else 0.0
        return IndexQuote(label=label, symbol=symbol, price=round(price, 2), change_pct=chg, up=chg >= 0)
    except Exception as e:
        logger.warning("Quote failed for %s: %s", symbol, e)
        return IndexQuote(label=label, symbol=symbol)


def _fetch_sector(sector: str, symbol: str) -> SectorPerf:
    try:
        hist = yf.Ticker(symbol).history(period="5d")
        if hist is None or len(hist) < 2:
            return SectorPerf(sector=sector)
        price = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2])
        chg = round((price - prev) / prev * 100, 2) if prev > 0 else 0.0
        return SectorPerf(sector=sector, change_pct=chg, up=chg >= 0)
    except Exception as e:
        logger.warning("Sector quote failed for %s: %s", symbol, e)
        return SectorPerf(sector=sector)


@router.get("/market-pulse", response_model=MarketPulseResponse)
async def get_market_pulse(_: str = Depends(verify_token)):
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

    # Breadth: % of sectors positive
    valid_sectors = [s for s in sectors if s.change_pct is not None]
    if valid_sectors:
        up_count = sum(1 for s in valid_sectors if s.up)
        breadth_pct = up_count / len(valid_sectors)
        breadth = "Broad Advance" if breadth_pct >= 0.75 else \
                  "Mixed" if breadth_pct >= 0.4 else "Broad Decline"
    else:
        breadth = None

    return MarketPulseResponse(indices=indices, sectors=sectors, market_breadth=breadth)
