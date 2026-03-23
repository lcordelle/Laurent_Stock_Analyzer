"""
Ticker Resolver - Resolve ticker symbol OR company name (full/partial) to ticker
Used across all app features so users can type "Apple", "Microsoft", "NVDA" or "AAPL"
"""

from typing import Optional
import yfinance as yf
import re

# Cache to avoid repeated lookups (in-memory, per session)
_resolve_cache = {}


def _looks_like_ticker(s: str) -> bool:
    """Check if input looks like a ticker (1-6 chars, alphanumeric, optional . or -)"""
    s = s.strip().upper()
    if not s or len(s) > 6:
        return False
    # Tickers: AAPL, BRK.B, BF-B, etc.
    return bool(re.match(r'^[A-Z0-9][A-Z0-9.\-]*$', s))


def resolve_to_ticker(query: str) -> Optional[str]:
    """
    Resolve ticker symbol or company name (full/partial) to a valid ticker.
    Returns the ticker symbol (e.g., 'AAPL') or None if not found.
    
    Examples:
        'AAPL' -> 'AAPL'
        'Apple' -> 'AAPL'
        'Microsoft' -> 'MSFT'
        'Nvidia' -> 'NVDA'
    """
    if not query or not str(query).strip():
        return None
    
    query = str(query).strip()
    query_upper = query.upper()
    
    # Check cache
    cache_key = query_upper
    if cache_key in _resolve_cache:
        return _resolve_cache[cache_key]
    
    result = None
    
    # 1. If it looks like a ticker, try direct fetch first
    if _looks_like_ticker(query):
        try:
            stock = yf.Ticker(query_upper)
            hist = stock.history(period="5d")
            if hist is not None and len(hist) > 0:
                result = query_upper
        except Exception:
            pass
    
    # 2. If direct fetch failed or input looks like a name, search
    if result is None:
        try:
            search = yf.Search(query, max_results=10)
            quotes = getattr(search, 'quotes', None) or []
            for q in quotes:
                if isinstance(q, dict):
                    quote_type = q.get('quoteType', '')
                    symbol = q.get('symbol', '')
                    if quote_type == 'EQUITY' and symbol:
                        # Verify we can fetch data for this symbol
                        try:
                            stock = yf.Ticker(symbol)
                            hist = stock.history(period="5d")
                            if hist is not None and len(hist) > 0:
                                result = symbol
                                break
                        except Exception:
                            continue
        except Exception:
            pass
    
    # Cache result (including None to avoid repeated failed lookups)
    _resolve_cache[cache_key] = result
    if result:
        _resolve_cache[result] = result  # Also cache ticker -> ticker
    
    return result


def resolve_tickers_batch(queries: list) -> dict:
    """
    Resolve multiple queries (tickers or names) to tickers.
    Returns dict mapping original query -> resolved ticker (or None if failed).
    Skips duplicates.
    """
    seen = set()
    result = {}
    for q in queries:
        q_clean = str(q).strip().upper()
        if not q_clean or q_clean in seen:
            continue
        seen.add(q_clean)
        resolved = resolve_to_ticker(q)
        result[q.strip()] = resolved
    return result
