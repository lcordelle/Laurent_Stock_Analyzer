# utils/calibration.py
"""Conviction calibration: bucket the (ex-fundamentals) conviction model over history
against realized forward returns. Reuses the real decision engine — score=None drops
Fundamentals and renormalizes over Technical/Trend/Valuation."""
import json
import os
from typing import Optional

import numpy as np
import pandas as pd

from utils.decision_engine import compute_conviction

HORIZON_DAYS = 30
BUCKETS = [(0.0, 2.0), (2.0, 4.0), (4.0, 6.0), (6.0, 8.0), (8.0, 10.0)]
_BUCKET_LABELS = {(0.0, 2.0): "0–2", (2.0, 4.0): "2–4", (4.0, 6.0): "4–6",
                  (6.0, 8.0): "6–8", (8.0, 10.0): "8–10"}
_RISK_ON, _RISK_OFF = 15, 25  # mirrors utils/market_breadth thresholds

# Curated S&P 100 (large-cap) universe.
SP100 = [
    "AAPL","MSFT","AMZN","NVDA","GOOGL","GOOG","META","BRK-B","LLY","AVGO","TSLA","JPM",
    "V","XOM","UNH","MA","PG","JNJ","HD","COST","ORCL","MRK","ABBV","CVX","KO","PEP",
    "ADBE","WMT","BAC","CRM","ACN","MCD","NFLX","TMO","LIN","ABT","CSCO","INTC","AMD",
    "DHR","WFC","DIS","TXN","PM","VZ","CMCSA","INTU","COP","NKE","AMGN","NEE","UNP",
    "RTX","HON","LOW","SPGI","IBM","GS","CAT","BA","SBUX","BLK","DE","ELV","PLD","MDT",
    "AXP","GILD","ADP","C","BKNG","MDLZ","TJX","MMC","CB","ISRG","VRTX","SYK","NOW","LMT",
    "AMT","REGN","ADI","PGR","SLB","ETN","BMY","ZTS","MU","SO","BSX","DUK","CI","MO",
    "FI","CME","PYPL","T","GE","MS",
]


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def regime_for_vix(vix) -> dict:
    if vix is None or (isinstance(vix, float) and np.isnan(vix)):
        return {"regime": "Unknown", "vix": None}
    v = float(vix)
    label = "Risk-On" if v < _RISK_ON else "Risk-Off" if v < _RISK_OFF else "Danger"
    return {"regime": label, "vix": round(v, 2)}


def synth_signals(rsi, macd_hist, sma20, sma50, sma200, adx, close) -> dict:
    """Reconstructable proxy for the live trading-signal inputs (documented approximation)."""
    # Trend label from SMA alignment + ADX (mirrors the live trend_strength buckets).
    ts = None
    if None not in (sma20, sma50, sma200) and not any(np.isnan(x) for x in (sma20, sma50, sma200)):
        up = close > sma20 > sma50 > sma200
        down = close < sma20 < sma50 < sma200
        strong = adx is not None and not np.isnan(adx) and adx >= 25
        weak = adx is not None and not np.isnan(adx) and adx < 20
        if up:
            ts = "STRONG UPTREND" if strong else "WEAK UPTREND" if weak else "UPTREND"
        elif down:
            ts = "STRONG DOWNTREND" if strong else "WEAK DOWNTREND" if weak else "DOWNTREND"
        else:
            ts = "MIXED"
    # Technical signal proxy from RSI + MACD histogram.
    mom = 0.0
    if rsi is not None and not np.isnan(rsi):
        mom += _clamp((rsi - 50) / 30.0, -1, 1) * 0.6
    if macd_hist is not None and not np.isnan(macd_hist):
        mom += _clamp(macd_hist, -1, 1) * 0.4
    if mom > 0.5:
        sig, qual = "STRONG BUY", "CONFIRMED"
    elif mom > 0.15:
        sig, qual = "BUY", "STANDARD"
    elif mom < -0.5:
        sig, qual = "STRONG SELL", "CONFIRMED"
    elif mom < -0.15:
        sig, qual = "SELL", "STANDARD"
    else:
        sig, qual = "HOLD", "STANDARD"
    conf = int(_clamp(50 + mom * 50, 0, 100))
    return {"trend_strength": ts, "signal": sig, "confidence": conf, "signal_quality": qual}


def bar_conviction(rsi, macd_hist, sma20, sma50, sma200, adx, close, vix, weights=None):
    signals = synth_signals(rsi, macd_hist, sma20, sma50, sma200, adx, close)
    # Valuation proxy: price vs SMA50 as fair value, fed through the engine's _valuation.
    tunnel = None
    if sma50 is not None and not np.isnan(sma50) and sma50 > 0:
        tunnel = {"current_vs_fair_pct": (close / sma50 - 1.0) * 100.0}
    regime = regime_for_vix(vix)
    d = compute_conviction(score=None, signals=signals, forecast=None, tunnel=tunnel, regime=regime, weights=weights)
    return d["conviction"], d["direction"]


def _indicators(hist: pd.DataFrame):
    c = hist["Close"]
    sma20 = c.rolling(20).mean(); sma50 = c.rolling(50).mean(); sma200 = c.rolling(200).mean()
    delta = c.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - 100 / (1 + rs)
    ema12 = c.ewm(span=12, adjust=False).mean(); ema26 = c.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26; macd_hist = macd - macd.ewm(span=9, adjust=False).mean()
    # ADX (Wilder)
    up = hist["High"].diff(); dn = -hist["Low"].diff()
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = pd.concat([(hist["High"] - hist["Low"]),
                    (hist["High"] - c.shift()).abs(),
                    (hist["Low"] - c.shift()).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    pdi = 100 * pd.Series(plus_dm, index=hist.index).ewm(alpha=1/14, adjust=False, min_periods=14).mean() / atr
    mdi = 100 * pd.Series(minus_dm, index=hist.index).ewm(alpha=1/14, adjust=False, min_periods=14).mean() / atr
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    adx = dx.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    return sma20, sma50, sma200, rsi, macd_hist, adx


def observations_for_history(hist: pd.DataFrame, vix_series: pd.Series,
                             horizon: int = HORIZON_DAYS, weights=None) -> list:
    if hist is None or len(hist) < 60 + horizon:
        return []
    c = hist["Close"].reset_index(drop=True)
    sma20, sma50, sma200, rsi, macd_hist, adx = (s.reset_index(drop=True) for s in _indicators(hist))
    vix = vix_series.reindex(hist.index).reset_index(drop=True) if vix_series is not None else pd.Series([np.nan] * len(c))
    fwd = c.shift(-horizon) / c - 1.0
    out = []
    for i in range(len(c) - horizon):
        if pd.isna(fwd.iloc[i]) or pd.isna(c.iloc[i]):
            continue
        conv, direction = bar_conviction(
            _nan(rsi, i), _nan(macd_hist, i), _nan(sma20, i), _nan(sma50, i),
            _nan(sma200, i), _nan(adx, i), float(c.iloc[i]), _nan(vix, i), weights)
        out.append({"conviction": conv, "direction": direction, "fwd_return": float(fwd.iloc[i])})
    return out


def _nan(series, i):
    v = series.iloc[i]
    return None if pd.isna(v) else float(v)


def bucketize(observations: list) -> list:
    buckets = []
    for lo, hi in BUCKETS:
        in_band = [o for o in observations if (o["conviction"] >= lo and (o["conviction"] < hi or hi == 10.0))]
        directional = [o for o in in_band if o["direction"] in ("Long", "Short")]
        signed = [(o["fwd_return"] if o["direction"] == "Long" else -o["fwd_return"]) for o in directional]
        n = len(directional)
        if n:
            hits = sum(1 for s in signed if s > 0)
            hit_rate = round(hits / n * 100, 1)
            avg = round(float(np.mean(signed)) * 100, 2)
            med = round(float(np.median(signed)) * 100, 2)
        else:
            hit_rate = avg = med = None
        buckets.append({"label": _BUCKET_LABELS[(lo, hi)], "lo": lo, "hi": hi,
                        "n": n, "hit_rate": hit_rate,
                        "avg_forward_return": avg, "median_forward_return": med})
    return buckets


def lookup(buckets: list, conviction: float) -> Optional[dict]:
    c = _clamp(float(conviction), 0.0, 10.0)
    for b in buckets:
        if c >= b["lo"] and (c < b["hi"] or b["hi"] == 10.0):
            return b
    return None


def load_table(path: str) -> Optional[dict]:
    try:
        if not os.path.exists(path):
            return None
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def conviction_percentiles(observations: list) -> list:
    vals = sorted(o["conviction"] for o in observations if o["direction"] in ("Long", "Short"))
    if not vals:
        return []
    out = []
    for p in range(0, 101, 5):
        idx = int(round((p / 100.0) * (len(vals) - 1)))
        out.append({"p": p, "value": round(float(vals[idx]), 4)})
    return out


def percentile_of(breakpoints: list, conviction: float) -> Optional[float]:
    if not breakpoints:
        return None
    c = float(conviction)
    if c <= breakpoints[0]["value"]:
        return 0.0
    if c >= breakpoints[-1]["value"]:
        return 100.0
    for i in range(1, len(breakpoints)):
        lo, hi = breakpoints[i - 1], breakpoints[i]
        if c <= hi["value"]:
            span = hi["value"] - lo["value"]
            frac = 0.0 if span <= 0 else (c - lo["value"]) / span
            return round(lo["p"] + frac * (hi["p"] - lo["p"]), 1)
    return 100.0


def band_for(percentile: Optional[float]) -> Optional[str]:
    if percentile is None:
        return None
    if percentile < 50:
        return "Weak"
    if percentile < 80:
        return "Fair"
    if percentile < 95:
        return "Strong"
    return "Prime"
