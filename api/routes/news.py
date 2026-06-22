from __future__ import annotations

import time
import logging
import threading
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

import feedparser
import yfinance as yf
from fastapi import APIRouter, Depends

from api.auth import verify_token

logger = logging.getLogger(__name__)
router = APIRouter(tags=["news"])

_CACHE_TTL = 60  # 1 minute — near real-time
_cache: list = []
_cache_ts: float = 0.0
_lock = threading.Lock()

_POSITIVE_WORDS = {
    "gains", "gain", "rises", "rise", "beats", "beat", "surges", "surge",
    "record", "growth", "upgrade", "upgraded", "rally", "rallies", "profit",
    "buyout", "acquisition", "dividend", "expansion", "outperforms", "bullish",
    "recovery", "rebound", "boost", "soars", "soar", "jumps", "jump",
}
_NEGATIVE_WORDS = {
    "falls", "fall", "drops", "drop", "losses", "loss", "misses", "miss",
    "recession", "layoffs", "layoff", "bankruptcy", "downgrade", "downgraded",
    "crash", "plunges", "plunge", "decline", "declines", "warning", "risk",
    "uncertainty", "inflation", "tariff", "tariffs", "default", "cut",
    "slumps", "slump", "fears", "concern", "concerns", "sell-off", "selloff",
    # geopolitical / world events
    "war", "strike", "strikes", "attack", "attacks", "killed", "dead", "deaths",
    "explosion", "bomb", "missile", "invasion", "conflict", "crisis", "sanctions",
    "shutdown", "collapse", "earthquake", "hurricane", "flood", "disaster",
    "shooting", "coup", "protest", "unrest", "tension", "tensions",
}

_MARKET_MOVER_WORDS = {
    # Fed / monetary policy
    "fed", "federal", "reserve", "fomc", "powell", "rate", "rates",
    "hike", "cut", "pivot", "tapering", "qe", "qt",
    # Inflation / macro data
    "inflation", "cpi", "ppi", "pce", "gdp", "deflation", "stagflation",
    # Labour market
    "jobs", "payroll", "nfp", "unemployment", "jobless", "layoffs", "hiring",
    # Earnings
    "earnings", "eps", "revenue", "beats", "misses", "guidance",
    "outlook", "forecast", "quarterly", "results",
    # Energy / commodities
    "oil", "crude", "opec", "energy", "gas", "gold", "silver", "copper",
    # Macro risks
    "tariff", "tariffs", "trade", "sanctions", "default", "debt",
    "ceiling", "shutdown", "stimulus", "bailout", "downgrade",
    # Central banks (global)
    "ecb", "boj", "pboc", "boe", "rba", "snb", "imf",
    # Corporate events
    "acquisition", "merger", "ipo", "buyout", "takeover", "spinoff",
    "bankruptcy", "restructuring",
    # Market-moving geopolitics
    "war", "invasion", "strike", "strikes", "conflict", "escalation",
    "sanctions", "embargo", "blockade",
    # Tech / sector catalysts
    "fda", "approved", "approval", "chip", "semiconductor",
    "ai", "artificial intelligence", "nvidia", "apple", "microsoft",
    # Rates / bonds
    "yield", "treasury", "bond", "bonds", "spread", "dollar", "dxy",
    # Recession signals
    "recession", "contraction", "slowdown", "growth",
}


_MAX_AGE_HOURS = 48


def _parse_published_at(raw: str) -> datetime | None:
    if not raw:
        return None
    # Unix timestamp (yfinance)
    try:
        ts = float(raw)
        if ts > 1_000_000_000:
            return datetime.fromtimestamp(ts, tz=timezone.utc)
    except ValueError:
        pass
    # RFC 2822 (RSS)
    try:
        return parsedate_to_datetime(raw)
    except Exception:
        pass
    # ISO 8601 fallback
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def _is_recent(raw: str, cutoff: datetime) -> bool:
    dt = _parse_published_at(raw)
    if dt is None:
        return True  # keep items with unparseable dates rather than drop them
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt >= cutoff


def _sort_key(item: dict) -> float:
    dt = _parse_published_at(item.get("published_at", ""))
    if dt is None:
        return 0.0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def _is_market_mover(title: str) -> bool:
    words = set(title.lower().replace(",", " ").replace(".", " ").split())
    return bool(words & _MARKET_MOVER_WORDS)


_RSS_FEEDS = [
    # Markets
    ("MarketWatch", "https://feeds.marketwatch.com/marketwatch/marketpulse/"),
    ("Reuters Biz", "https://feeds.reuters.com/reuters/businessNews"),
    ("CNBC", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
    ("Investopedia", "https://www.investopedia.com/feedbuilder/feed/getfeed?feedName=rss_headline"),
    # World / Geopolitical
    ("BBC World", "http://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Sky News", "https://feeds.skynews.com/feeds/rss/world.xml"),
    ("Guardian", "https://www.theguardian.com/world/rss"),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
]

_YF_TICKERS = ["SPY", "QQQ", "^GSPC", "^DJI", "^VIX"]


def _sentiment(title: str) -> str:
    words = set(title.lower().split())
    if words & _POSITIVE_WORDS:
        return "positive"
    if words & _NEGATIVE_WORDS:
        return "negative"
    return "neutral"


def _parse_rss(source: str, url: str) -> list[dict]:
    items = []
    try:
        feed = feedparser.parse(url, agent="Mozilla/5.0", request_headers={"Accept": "application/rss+xml, text/xml"})
        for entry in feed.entries[:8]:
            title = (entry.get("title") or "").strip()
            if not title:
                continue
            items.append({
                "title": title,
                "source": source,
                "url": entry.get("link") or "",
                "published_at": entry.get("published") or "",
                "sentiment": _sentiment(title),
                "market_mover": _is_market_mover(title),
            })
    except Exception as e:
        logger.debug("RSS fetch failed %s: %s", source, e)
    return items


def _fetch_yf_news() -> list[dict]:
    items = []
    seen: set[str] = set()
    for sym in _YF_TICKERS:
        try:
            raw = yf.Ticker(sym).news or []
            for n in raw[:4]:
                # yfinance >= 0.2.x wraps content in a nested dict
                content = n.get("content") or n
                title = (content.get("title") or n.get("title") or "").strip()
                url = (content.get("canonicalUrl", {}) or {}).get("url") or n.get("link") or ""
                pub = str(content.get("pubDate") or n.get("providerPublishTime") or "")
                if not title or title in seen:
                    continue
                seen.add(title)
                items.append({
                    "title": title,
                    "source": "Yahoo Finance",
                    "url": url,
                    "published_at": pub,
                    "sentiment": _sentiment(title),
                    "market_mover": _is_market_mover(title),
                })
        except Exception as e:
            logger.debug("yfinance news failed %s: %s", sym, e)
    return items


def _build_cache() -> None:
    global _cache, _cache_ts
    all_items: list[dict] = []

    for source, url in _RSS_FEEDS:
        all_items.extend(_parse_rss(source, url))

    all_items.extend(_fetch_yf_news())

    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=_MAX_AGE_HOURS)
    recent = [item for item in all_items if _is_recent(item.get("published_at", ""), cutoff)]

    seen_titles: set[str] = set()
    deduped = []
    for item in sorted(recent, key=_sort_key, reverse=True):
        key = item["title"].lower()[:60]
        if key not in seen_titles:
            seen_titles.add(key)
            deduped.append(item)

    with _lock:
        _cache = deduped
        _cache_ts = time.time()
    logger.info(
        "Market news cache refreshed: %d recent items (dropped %d old)",
        len(deduped),
        len(all_items) - len(recent),
    )


def _get_cached() -> list[dict]:
    if time.time() - _cache_ts > _CACHE_TTL or not _cache:
        _build_cache()
    with _lock:
        return list(_cache)


def _refresh_loop() -> None:
    while True:
        time.sleep(_CACHE_TTL)
        try:
            _build_cache()
        except Exception as exc:
            logger.debug("Background news refresh failed: %s", exc)


_bg_thread = threading.Thread(target=_refresh_loop, daemon=True)
_bg_thread.start()


@router.get("/news/market")
def get_market_news(_: str = Depends(verify_token)) -> dict:
    return {"items": _get_cached(), "cached_at": _cache_ts}
