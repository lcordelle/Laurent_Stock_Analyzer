"""Fuse existing per-stock signals + market regime into a conviction + sizing-ready decision."""
from typing import Optional

DEFAULT_WEIGHTS = {"Fundamentals": 0.30, "Technical": 0.30, "Trend": 0.20, "Valuation": 0.20}
REGIME_MULT = {"Risk-On": 1.0, "Neutral": 0.85, "Risk-Off": 0.65, "Danger": 0.45, "Unknown": 1.0}
_SIGNAL_MAP = {"STRONG BUY": 1.0, "BUY": 0.6, "HOLD": 0.0, "NEUTRAL": 0.0,
               "SELL": -0.6, "STRONG SELL": -1.0}
_QUALITY_MAP = {"PRIME": 1.0, "CONFIRMED": 0.75, "STANDARD": 0.5, "WEAK": 0.25}


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def _fundamentals(score) -> Optional[float]:
    if score is None:
        return None
    return _clamp((float(score) - 50.0) / 50.0, -1.0, 1.0)


def _technical(signals) -> Optional[float]:
    if not signals:
        return None
    sig = _SIGNAL_MAP.get((signals.get("signal") or "").upper())
    if sig is None:
        return None
    conf = (signals.get("confidence") or 50) / 100.0          # 0..1
    qual = _QUALITY_MAP.get((signals.get("signal_quality") or "STANDARD").upper(), 0.5)
    # scale the signed signal by how strong/clean it is
    return _clamp(sig * (0.5 + 0.5 * conf) * (0.5 + 0.5 * qual), -1.0, 1.0)


def _trend(signals) -> Optional[float]:
    if not signals:
        return None
    ts = (signals.get("trend_strength") or "").upper()
    if not ts:
        return None
    sign = 1.0 if "UP" in ts else -1.0 if "DOWN" in ts else 0.0
    mag = 1.0 if "STRONG" in ts else 0.4 if "WEAK" in ts else 0.6
    return _clamp(sign * mag, -1.0, 1.0)


def _valuation(forecast, tunnel) -> Optional[float]:
    parts = []
    if tunnel and tunnel.get("current_vs_fair_pct") is not None:
        # below fair value (negative %) is bullish -> invert sign
        parts.append(_clamp(-(tunnel["current_vs_fair_pct"]) / 15.0, -1.0, 1.0))
    if forecast and forecast.get("forecast_change_pct") is not None:
        chg = forecast["forecast_change_pct"]
        parts.append(_clamp(chg / 10.0, -1.0, 1.0))
    if not parts:
        return None
    return sum(parts) / len(parts)


def _expected_value_r(signals, raw, mult) -> Optional[float]:
    if not signals:
        return None
    entry = signals.get("optimal_entry")
    stop = signals.get("stop_loss")
    tp1 = signals.get("tp1")
    if entry is None or stop is None or tp1 is None:
        return None
    risk = abs(entry - stop)
    if risk <= 0:
        return None
    r = abs(tp1 - entry) / risk
    p = _clamp(0.5 + raw * mult * 0.4, 0.05, 0.95)
    return round(p * r - (1 - p) * 1.0, 2)


def compute_conviction(score, signals, forecast, tunnel, regime, weights=None) -> dict:
    weights = weights or DEFAULT_WEIGHTS
    subs = {
        "Fundamentals": _fundamentals(score),
        "Technical": _technical(signals),
        "Trend": _trend(signals),
        "Valuation": _valuation(forecast, tunnel),
    }
    details = {
        "Fundamentals": f"Score {score}" if score is not None else "no score",
        "Technical": f"{(signals or {}).get('signal','?')} / {(signals or {}).get('signal_quality','?')}",
        "Trend": (signals or {}).get("trend_strength") or "no trend",
        "Valuation": "fair-value & forecast",
    }
    avail = {k: v for k, v in subs.items() if v is not None}
    total_w = sum(weights[k] for k in avail) or 1.0
    raw = sum(subs[k] * weights[k] for k in avail) / total_w  # [-1,1]

    regime_label = (regime or {}).get("regime") or "Unknown"
    mult = REGIME_MULT.get(regime_label, 1.0)

    conviction = round(_clamp(abs(raw) * mult, 0.0, 1.0) * 10.0, 1)
    direction = "Long" if raw > 0.15 else "Short" if raw < -0.15 else "Stand aside"

    factors = [{
        "label": k,
        "subscore": round(subs[k], 3) if subs[k] is not None else None,
        "weight": weights[k],
        "contribution": round((subs[k] * weights[k] / total_w), 3) if subs[k] is not None else None,
        "detail": details[k],
    } for k in DEFAULT_WEIGHTS]

    ev_r = _expected_value_r(signals, raw, mult)
    rationale = (f"{direction} · conviction {conviction}/10 · regime {regime_label}"
                 f"{'' if mult == 1.0 else f' (×{mult})'}")

    return {
        "conviction": conviction,
        "direction": direction,
        "factors": factors,
        "regime": {"label": regime_label, "vix": (regime or {}).get("vix"), "multiplier": mult},
        "expected_value_r": ev_r,
        "rationale": rationale,
    }
