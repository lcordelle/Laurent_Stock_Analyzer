"""
Options Flow Analysis
Unusual options activity detection using yfinance option chains.
"""

import yfinance as yf
import logging

logger = logging.getLogger(__name__)


def get_options_flow(ticker: str) -> dict:
    """Fetch options chain and identify unusual activity.

    Unusual = volume > open interest AND volume > 100 contracts.
    Returns summary metrics and top 20 unusual trades sorted by volume.
    """
    result = {
        'unusual': [],
        'summary': {
            'total_call_oi': 0,
            'total_put_oi': 0,
            'total_call_volume': 0,
            'total_put_volume': 0,
            'pc_ratio': 0.0,
            'pc_volume_ratio': 0.0,
        },
        'expirations': [],
        'error': None,
    }

    try:
        stock = yf.Ticker(ticker)
        expirations = stock.options
        if not expirations:
            result['error'] = 'No options data available'
            return result

        result['expirations'] = list(expirations[:8])
        target_expiries = expirations[:4]  # next 4 expiries

        for exp in target_expiries:
            try:
                chain = stock.option_chain(exp)
            except Exception as e:
                logger.warning("Failed to fetch option chain %s %s: %s", ticker, exp, e)
                continue

            for df, side in [(chain.calls, 'call'), (chain.puts, 'put')]:
                if df is None or df.empty:
                    continue
                df = df.dropna(subset=['volume', 'openInterest'])
                df = df[(df['volume'] > 0) & (df['openInterest'] >= 0)]

                oi_sum = int(df['openInterest'].sum())
                vol_sum = int(df['volume'].sum())
                result['summary'][f'total_{side}_oi'] += oi_sum
                result['summary'][f'total_{side}_volume'] += vol_sum

                flags = df[(df['volume'] > df['openInterest']) & (df['volume'] > 100)]
                for _, row in flags.iterrows():
                    iv = row.get('impliedVolatility', 0)
                    result['unusual'].append({
                        'expiry': exp,
                        'side': side,
                        'strike': float(row['strike']),
                        'volume': int(row['volume']),
                        'oi': int(row['openInterest']),
                        'vol_oi_ratio': round(row['volume'] / max(row['openInterest'], 1), 1),
                        'iv': round(float(iv) * 100, 1) if iv else 0,
                        'last': float(row.get('lastPrice', 0)),
                        'type': 'call' if side == 'call' else 'put',
                    })

        result['unusual'].sort(key=lambda x: x['volume'], reverse=True)
        result['unusual'] = result['unusual'][:20]

        call_oi = result['summary']['total_call_oi']
        put_oi = result['summary']['total_put_oi']
        call_vol = result['summary']['total_call_volume']
        put_vol = result['summary']['total_put_volume']

        if call_oi > 0:
            result['summary']['pc_ratio'] = round(put_oi / call_oi, 2)
        if call_vol > 0:
            result['summary']['pc_volume_ratio'] = round(put_vol / call_vol, 2)

    except Exception as e:
        result['error'] = str(e)
        logger.error("Options flow error for %s: %s", ticker, e)

    return result


def sentiment_label(pc_ratio: float) -> tuple[str, str]:
    """Return (label, color) for put/call ratio."""
    if pc_ratio < 0.7:
        return 'Bullish', '#22c55e'
    elif pc_ratio < 1.0:
        return 'Neutral', '#f59e0b'
    elif pc_ratio < 1.5:
        return 'Bearish', '#ef4444'
    else:
        return 'Extreme Fear', '#7f1d1d'
