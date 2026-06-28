"""Valuation Tunnel: regression fair-value channel (history) + GBM forecast cone."""
import math
from datetime import datetime, timedelta
from typing import Optional

import numpy as np

DEFAULT_WEIGHTS = {"analyst": 0.35, "regression": 0.30,
                   "mean_reversion": 0.20, "momentum": 0.15}
DRIFT_CLAMP = 0.5     # ±50% annual drift cap
BAND_CLAMP = 0.6      # cone half-width capped at ±60% of price


def log_regression_channel(closes: np.ndarray, k: float = 2.0):
    """Least-squares line on log(price); band = line ± k·std(residuals)."""
    closes = np.asarray(closes, dtype=float)
    if np.any(closes <= 0) or np.any(np.isnan(closes)):
        raise ValueError("closes must be positive and finite")
    n = len(closes)
    x = np.arange(n, dtype=float)
    y = np.log(closes)
    slope, intercept = np.polyfit(x, y, 1)
    fit = slope * x + intercept
    resid = y - fit
    sigma = float(resid.std(ddof=1)) if n > 2 else 0.0
    mid = np.exp(fit)
    upper = np.exp(fit + k * sigma)
    lower = np.exp(fit - k * sigma)
    return mid, upper, lower, float(slope), sigma


def daily_sigma(closes: np.ndarray) -> float:
    lr = np.diff(np.log(closes))
    return float(lr.std(ddof=1)) if len(lr) > 1 else 0.0


def blended_annual_drift(closes, target_price, mid_last, reg_slope_daily,
                         weights=None) -> float:
    """Weighted annual drift from available signals, renormalized + clamped."""
    weights = weights or DEFAULT_WEIGHTS
    current = closes[-1]
    comps, used_w = {}, {}

    if target_price and current and target_price > 0:
        comps["analyst"] = target_price / current - 1.0
        used_w["analyst"] = weights["analyst"]

    comps["regression"] = math.exp(reg_slope_daily * 252) - 1.0
    used_w["regression"] = weights["regression"]

    if mid_last and current:
        comps["mean_reversion"] = -(current / mid_last - 1.0)
        used_w["mean_reversion"] = weights["mean_reversion"]

    if len(closes) >= 21 and closes[-21] > 0:
        m = closes[-1] / closes[-21] - 1.0
        comps["momentum"] = m * (252 / 20)
        used_w["momentum"] = weights["momentum"]

    total_w = sum(used_w.values()) or 1.0
    drift = sum(comps[k] * used_w[k] for k in comps) / total_w
    return max(-DRIFT_CLAMP, min(DRIFT_CLAMP, drift))


def forecast_cone(p0, drift_annual, sigma_daily, horizon_days, k=2.0):
    mid, upper, lower = [], [], []
    mu_daily = math.log(1.0 + drift_annual) / 252.0
    for t in range(1, horizon_days + 1):
        center = p0 * math.exp(mu_daily * t)
        half = min(k * sigma_daily * math.sqrt(t), BAND_CLAMP)
        mid.append(center)
        upper.append(center * math.exp(half))
        lower.append(center * math.exp(-half))
    return mid, upper, lower


def next_trading_days(last_date_str: str, n: int) -> list[str]:
    d = datetime.strptime(last_date_str[:10], "%Y-%m-%d")
    out: list[str] = []
    while len(out) < n:
        d += timedelta(days=1)
        if d.weekday() < 5:  # Mon-Fri (holidays ignored)
            out.append(d.strftime("%Y-%m-%d"))
    return out


def build_valuation_tunnel(closes, dates, target_price: Optional[float] = None,
                           horizon_days: int = 30, k: float = 2.0,
                           weights=None) -> Optional[dict]:
    if closes is None or len(closes) < 30:
        return None
    arr = np.asarray(closes, dtype=float)
    if np.any(arr <= 0) or np.any(np.isnan(arr)):
        return None

    mid, upper, lower, slope, _ = log_regression_channel(arr, k=k)
    sig_d = daily_sigma(arr)
    drift = blended_annual_drift(arr, target_price, float(mid[-1]), slope, weights)
    p0 = float(arr[-1])
    fc_mid, fc_up, fc_lo = forecast_cone(p0, drift, sig_d, horizon_days, k)
    future = next_trading_days(dates[-1], horizon_days)

    return {
        "hist_mid": [float(v) for v in mid],
        "hist_upper": [float(v) for v in upper],
        "hist_lower": [float(v) for v in lower],
        "future_dates": future,
        "fc_mid": fc_mid,
        "fc_upper": fc_up,
        "fc_lower": fc_lo,
        "horizon_days": horizon_days,
        "k": k,
        "drift_annual": drift,
        "sigma_annual": sig_d * math.sqrt(252),
    }
