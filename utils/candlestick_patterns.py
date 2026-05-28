"""
Candlestick Pattern Recognition
Pure pandas implementation — no external TA dependencies required.
"""

import pandas as pd


def detect_patterns(hist: pd.DataFrame) -> list:
    """Detect classic candlestick patterns in OHLCV history.

    Returns list of dicts: {date, pattern, direction, confidence}
    covering the last 10 detected signals.
    """
    if hist is None or len(hist) < 3:
        return []

    o = hist['Open']
    h = hist['High']
    l = hist['Low']
    c = hist['Close']
    body = (c - o).abs()
    total_range = h - l

    patterns = []

    for i in range(2, len(hist)):
        date = hist.index[i]

        # Skip rows with zero range (data gaps)
        if total_range.iloc[i] == 0:
            continue

        body_pct = body.iloc[i] / total_range.iloc[i]
        lower_wick = min(o.iloc[i], c.iloc[i]) - l.iloc[i]
        upper_wick = h.iloc[i] - max(o.iloc[i], c.iloc[i])

        # Doji: body < 10% of range — indecision
        if body_pct < 0.10:
            patterns.append({'date': date, 'pattern': 'Doji', 'direction': 'neutral', 'confidence': 65})

        # Hammer: long lower wick (>2x body), tiny upper wick, appears after decline
        if (body.iloc[i] > 0 and lower_wick > 2 * body.iloc[i]
                and upper_wick < body.iloc[i]
                and c.iloc[i - 1] < c.iloc[i - 2]):
            patterns.append({'date': date, 'pattern': 'Hammer', 'direction': 'bullish', 'confidence': 75})

        # Shooting Star: long upper wick (>2x body), tiny lower wick, appears after advance
        if (body.iloc[i] > 0 and upper_wick > 2 * body.iloc[i]
                and lower_wick < body.iloc[i]
                and c.iloc[i - 1] > c.iloc[i - 2]):
            patterns.append({'date': date, 'pattern': 'Shooting Star', 'direction': 'bearish', 'confidence': 75})

        # Bullish Engulfing: prior candle bearish, current candle bullish and fully engulfs prior
        prev_bearish = c.iloc[i - 1] < o.iloc[i - 1]
        curr_bullish = c.iloc[i] > o.iloc[i]
        if (prev_bearish and curr_bullish
                and o.iloc[i] <= c.iloc[i - 1]
                and c.iloc[i] >= o.iloc[i - 1]):
            patterns.append({'date': date, 'pattern': 'Bullish Engulfing', 'direction': 'bullish', 'confidence': 82})

        # Bearish Engulfing: prior candle bullish, current candle bearish and fully engulfs prior
        prev_bullish = c.iloc[i - 1] > o.iloc[i - 1]
        curr_bearish = c.iloc[i] < o.iloc[i]
        if (prev_bullish and curr_bearish
                and o.iloc[i] >= c.iloc[i - 1]
                and c.iloc[i] <= o.iloc[i - 1]):
            patterns.append({'date': date, 'pattern': 'Bearish Engulfing', 'direction': 'bearish', 'confidence': 82})

        # Morning Star (3-candle reversal): bearish, small body, bullish above midpoint
        if i >= 2:
            star_body_pct = body.iloc[i - 1] / max(total_range.iloc[i - 1], 0.0001)
            midpoint = (o.iloc[i - 2] + c.iloc[i - 2]) / 2
            if (c.iloc[i - 2] < o.iloc[i - 2]       # prior-prior bearish
                    and star_body_pct < 0.30           # middle is small star
                    and c.iloc[i] > o.iloc[i]          # current bullish
                    and c.iloc[i] > midpoint):         # closes above midpoint of first candle
                patterns.append({'date': date, 'pattern': 'Morning Star', 'direction': 'bullish', 'confidence': 87})

        # Evening Star (3-candle topping reversal)
        if i >= 2:
            star_body_pct = body.iloc[i - 1] / max(total_range.iloc[i - 1], 0.0001)
            midpoint = (o.iloc[i - 2] + c.iloc[i - 2]) / 2
            if (c.iloc[i - 2] > o.iloc[i - 2]         # prior-prior bullish
                    and star_body_pct < 0.30             # middle is small star
                    and c.iloc[i] < o.iloc[i]            # current bearish
                    and c.iloc[i] < midpoint):           # closes below midpoint of first candle
                patterns.append({'date': date, 'pattern': 'Evening Star', 'direction': 'bearish', 'confidence': 87})

    # Return last 10 signals (most recent)
    return patterns[-10:] if len(patterns) > 10 else patterns


def patterns_to_df(patterns: list) -> 'pd.DataFrame':
    """Convert pattern list to a formatted DataFrame for display."""
    import pandas as pd
    if not patterns:
        return pd.DataFrame()
    df = pd.DataFrame(patterns)
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    df['signal'] = df['direction'].map({'bullish': '▲ Bullish', 'bearish': '▼ Bearish', 'neutral': '◆ Neutral'})
    df = df.rename(columns={'date': 'Date', 'pattern': 'Pattern', 'signal': 'Signal', 'confidence': 'Confidence %'})
    return df[['Date', 'Pattern', 'Signal', 'Confidence %']].sort_values('Date', ascending=False)
