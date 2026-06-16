from __future__ import annotations
import asyncio
import json
import logging
import os
import time
from datetime import date
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


# ── Daily Drivers ─────────────────────────────────────────────────────────────

_DRIVERS_CACHE: Optional[dict] = None
_DRIVERS_CACHE_TS: float = 0.0
_DRIVERS_CACHE_TTL = 1800  # 30 minutes

# Major tickers to check for same-day earnings reports
_EARNINGS_WATCHLIST = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO",
    "JPM", "UNH", "XOM", "LLY", "V", "MA", "JNJ", "PG", "HD", "MRK",
    "COST", "ABBV", "BAC", "CVX", "AMD", "NFLX", "ORCL", "CRM", "ADBE",
    "WMT", "DIS", "KO", "PEP", "GS", "MS", "INTC", "QCOM", "TXN", "MU",
]


def _get_todays_earnings() -> list[str]:
    """Return tickers reporting earnings today."""
    today = date.today().isoformat()
    reporting = []
    for ticker in _EARNINGS_WATCHLIST:
        try:
            cal = yf.Ticker(ticker).calendar
            if cal is None:
                continue
            # calendar is a dict with 'Earnings Date' as a list of Timestamps
            dates = cal.get("Earnings Date") or []
            for d in dates:
                try:
                    if str(d)[:10] == today:
                        reporting.append(ticker)
                        break
                except Exception:
                    pass
        except Exception:
            pass
    return reporting


def _get_market_snapshot() -> dict:
    """Collect VIX, SPY, QQQ, 10Y yield for context."""
    snapshot = {}
    for label, sym in [("spy", "SPY"), ("qqq", "QQQ"), ("vix", "^VIX"), ("yield10y", "^TNX")]:
        try:
            price, chg = _fast_info_quote(sym)
            snapshot[label] = {"price": price, "chg": chg}
        except Exception:
            snapshot[label] = {}
    return snapshot


def _get_top_headlines(n: int = 8) -> list[str]:
    """Pull top market-moving headlines from the news cache."""
    try:
        from api.routes.news import _get_cached
        items = _get_cached()
        movers = [i for i in items if i.get("market_mover")][:n]
        if len(movers) < n:
            movers += [i for i in items if not i.get("market_mover")][:n - len(movers)]
        return [f"[{i.get('source','')}] {i.get('title','')}" for i in movers[:n]]
    except Exception:
        return []


def _call_llm_for_drivers(snapshot: dict, headlines: list[str], earnings_today: list[str]) -> list[dict]:
    """Ask Claude (or Groq fallback) to identify the top 3 market-moving events."""
    spy = snapshot.get("spy", {})
    vix = snapshot.get("vix", {})
    qqq = snapshot.get("qqq", {})
    y10 = snapshot.get("yield10y", {})

    context_lines = []
    def _chg(v: dict) -> str:
        c = v.get("chg")
        return f"{c:+.2f}%" if c is not None else "n/a"

    if spy.get("price"):
        context_lines.append(f"SPY: ${spy['price']} ({_chg(spy)})")
    if qqq.get("price"):
        context_lines.append(f"QQQ: ${qqq['price']} ({_chg(qqq)})")
    if vix.get("price"):
        fear = "elevated fear" if (vix["price"] or 0) > 20 else "calm"
        context_lines.append(f"VIX: {vix['price']} ({_chg(vix)}) — {fear}")
    if y10.get("price"):
        context_lines.append(f"10Y Yield: {y10['price']:.2f}%")
    if earnings_today:
        context_lines.append(f"Earnings today: {', '.join(earnings_today)}")
    if headlines:
        context_lines.append("\nTop market headlines:")
        for h in headlines:
            context_lines.append(f"  • {h}")

    prompt = f"""Today's market data:
{chr(10).join(context_lines)}

Identify the TOP 3 single most influential events/factors that will drive market direction today.
Rank them by impact. Each event must be distinct (no duplicates across earnings/macro/technical).

Respond with ONLY valid JSON — an array of exactly 3 objects:
[
  {{
    "rank": 1,
    "type": "earnings|macro|fed|rates|geopolitical|technical|sentiment",
    "title": "concise event title (max 12 words)",
    "direction": "bullish|bearish|neutral",
    "impact": "HIGH|MEDIUM",
    "why": "one sentence: why this moves markets today",
    "ticker": "TICKER or null"
  }},
  ...
]"""

    try:
        if os.getenv("ANTHROPIC_API_KEY"):
            import anthropic as ant
            client = ant.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=512,
                system="You are a senior market analyst. Respond only with valid JSON.",
                messages=[{"role": "user", "content": prompt}],
            )
            raw = msg.content[0].text.strip()
        elif os.getenv("GROQ_API_KEY"):
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a senior market analyst. Respond only with valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=512,
            )
            raw = resp.choices[0].message.content.strip()
        else:
            return []

        # Extract JSON array from response (handle markdown code fences)
        if "```" in raw:
            raw = raw.split("```")[1].lstrip("json").strip()
        return json.loads(raw)
    except Exception as e:
        logger.warning("Daily drivers LLM call failed: %s", e)
        return []


class DailyDriver(BaseModel):
    rank: int
    type: str
    title: str
    direction: str
    impact: str
    why: str
    ticker: Optional[str] = None


class DailyDriversResponse(BaseModel):
    drivers: list[DailyDriver]
    as_of: str


@router.get("/daily-drivers", response_model=DailyDriversResponse)
async def get_daily_drivers(_: str = Depends(verify_token)):
    global _DRIVERS_CACHE, _DRIVERS_CACHE_TS
    if _DRIVERS_CACHE is not None and (time.time() - _DRIVERS_CACHE_TS) < _DRIVERS_CACHE_TTL:
        return _DRIVERS_CACHE

    loop = asyncio.get_event_loop()
    snapshot, earnings, headlines = await asyncio.gather(
        loop.run_in_executor(None, _get_market_snapshot),
        loop.run_in_executor(None, _get_todays_earnings),
        loop.run_in_executor(None, _get_top_headlines, 8),
    )

    drivers_raw = await loop.run_in_executor(None, _call_llm_for_drivers, snapshot, headlines, earnings)

    drivers = []
    for d in drivers_raw[:3]:
        try:
            drivers.append(DailyDriver(
                rank=d["rank"],
                type=d.get("type", "macro"),
                title=d["title"],
                direction=d.get("direction", "neutral"),
                impact=d.get("impact", "MEDIUM"),
                why=d.get("why", ""),
                ticker=d.get("ticker") or None,
            ))
        except Exception:
            pass

    result = {"drivers": [d.model_dump() for d in drivers], "as_of": date.today().isoformat()}

    if drivers:
        _DRIVERS_CACHE = result
        _DRIVERS_CACHE_TS = time.time()

    return result
