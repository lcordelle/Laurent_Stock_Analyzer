"""
Market Breadth and Regime Analysis
VIX-based regime classification + SPY daily change.
"""

import time as _time
import yfinance as yf
import logging

logger = logging.getLogger(__name__)

# VIX thresholds for regime classification
_RISK_ON_THRESHOLD = 15
_RISK_OFF_THRESHOLD = 25


def get_market_regime() -> dict:
    """Fetch VIX and SPY data and classify the current market regime.

    Regime classification:
      VIX < 15  → Risk-On  (complacency, trend-following favored)
      VIX 15-25 → Risk-Off (elevated caution)
      VIX > 25  → Danger   (fear spike, defensive positioning)
    """
    result = {
        'vix': None,
        'spy_change': None,
        'spy_price': None,
        'regime': 'Unknown',
        'color': '#6b7280',
        'description': 'Market data unavailable',
        'error': None,
    }

    try:
        vix_info = yf.Ticker('^VIX').fast_info
        vix = vix_info.get('lastPrice') or vix_info.get('regularMarketPrice')
        if vix is None:
            raise ValueError('VIX price not found')
        result['vix'] = round(float(vix), 2)

        if vix < _RISK_ON_THRESHOLD:
            result['regime'] = 'Risk-On'
            result['color'] = '#22c55e'
            result['description'] = 'Low volatility — trend-following favored'
        elif vix < _RISK_OFF_THRESHOLD:
            result['regime'] = 'Risk-Off'
            result['color'] = '#f59e0b'
            result['description'] = 'Elevated volatility — trade selectively'
        else:
            result['regime'] = 'Danger'
            result['color'] = '#ef4444'
            result['description'] = 'High fear — capital preservation priority'

    except Exception as e:
        result['error'] = str(e)
        logger.warning("VIX fetch failed: %s", e)

    try:
        spy_info = yf.Ticker('SPY').fast_info
        price = spy_info.get('lastPrice') or spy_info.get('regularMarketPrice')
        prev_close = spy_info.get('regularMarketPreviousClose')
        if price is not None:
            result['spy_price'] = round(float(price), 2)
        if price is not None and prev_close and float(prev_close) > 0:
            result['spy_change'] = round((float(price) - float(prev_close)) / float(prev_close) * 100, 2)
    except Exception as e:
        logger.warning("SPY fetch failed: %s", e)

    return result


_REGIME_CACHE = {"ts": 0.0, "data": None}
_REGIME_TTL = 300  # 5 minutes

def get_market_regime_cached() -> dict:
    now = _time.monotonic()
    if _REGIME_CACHE["data"] is not None and (now - _REGIME_CACHE["ts"]) < _REGIME_TTL:
        return _REGIME_CACHE["data"]
    data = get_market_regime()
    _REGIME_CACHE["ts"] = now
    _REGIME_CACHE["data"] = data
    return data
