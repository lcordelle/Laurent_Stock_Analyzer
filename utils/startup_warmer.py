import logging
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)

WARM_TICKERS = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA",
    "AMD", "AVGO", "TSM", "ARM", "SMCI",
    "CRM", "SNOW", "DDOG", "NET", "PLTR",
    "JPM", "V", "BRK-B", "UNH", "XOM", "LLY", "ORCL",
]

_YF_CACHE_DIR = Path.home() / '.cache' / 'stock_analyzer' / 'yf_cache'
_FRESH_SECONDS = 3600  # skip tickers whose disk cache is under 1 hour old


def _disk_cache_fresh(ticker: str) -> bool:
    path = _YF_CACHE_DIR / f"{ticker}_1y.json"
    if not path.exists():
        return False
    return time.time() - path.stat().st_mtime < _FRESH_SECONDS


def _warm():
    from utils.stock_analyzer import StockAnalyzer
    analyzer = StockAnalyzer()
    stale = [t for t in WARM_TICKERS if not _disk_cache_fresh(t)]
    if not stale:
        logger.info("Pre-warmer: all %d tickers already fresh, skipping", len(WARM_TICKERS))
        return
    logger.info("Pre-warmer: warming %d/%d tickers", len(stale), len(WARM_TICKERS))
    for ticker in stale:
        try:
            analyzer.get_stock_data(ticker)
        except Exception as e:
            logger.debug("Pre-warmer failed %s: %s", ticker, e)
        time.sleep(1)
    logger.info("Pre-warmer complete")


def start_warmer():
    threading.Thread(target=_warm, daemon=True, name="startup-warmer").start()
