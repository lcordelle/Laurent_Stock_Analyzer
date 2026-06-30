"""Fuse existing per-stock signals + market regime into a conviction + sizing-ready decision."""
from typing import Optional

DEFAULT_WEIGHTS = {"Fundamentals": 0.30, "Technical": 0.30, "Trend": 0.20, "Valuation": 0.20}

HORIZON_PROFILES = {
    "day":   {"window": 5,   "label": "Day-trade", "weights": {"Technical": 0.6, "Trend": 0.3, "Valuation": 0.1}},
    "swing": {"window": 30,  "label": "Swing",     "weights": {"Technical": 0.4, "Trend": 0.3, "Valuation": 0.3}},
    "long":  {"window": 120, "label": "Long-term", "weights": {"Technical": 0.2, "Trend": 0.3, "Valuation": 0.5}},
}
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
    return _clamp(sum(parts) / len(parts), -1.0, 1.0)


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
    # Win-probability heuristic: base 50%, tilted by signed conviction (raw·regime),
    # capped to [5%,95%]; loss leg assumed at 1R (the stop). EV in R-multiples.
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
    total_w = sum(weights.get(k, 0.0) for k in avail) or 1.0
    raw = sum(subs[k] * weights.get(k, 0.0) for k in avail) / total_w  # [-1,1]

    regime_label = (regime or {}).get("regime") or "Unknown"
    mult = REGIME_MULT.get(regime_label, 1.0)

    direction = "Long" if raw > 0.15 else "Short" if raw < -0.15 else "Stand aside"
    effective_mult = mult if direction == "Long" else 1.0
    conviction = round(_clamp(abs(raw) * effective_mult * 10.0, 0.0, 10.0), 1)

    factors = [{
        "label": k,
        "subscore": round(subs[k], 3) if subs[k] is not None else None,
        "weight": weights.get(k, 0.0),
        "contribution": round((subs[k] * weights.get(k, 0.0) / total_w), 3) if subs[k] is not None else None,
        "detail": details[k],
    } for k in DEFAULT_WEIGHTS]

    ev_r = _expected_value_r(signals, raw, effective_mult)
    rationale = (f"{direction} · conviction {conviction}/10 · regime {regime_label}"
                 f"{'' if effective_mult == 1.0 else f' (×{effective_mult})'}")

    return {
        "conviction": conviction,
        "direction": direction,
        "factors": factors,
        "regime": {"label": regime_label, "vix": (regime or {}).get("vix"), "multiplier": effective_mult},
        "expected_value_r": ev_r,
        "rationale": rationale,
    }


def quality_grade(score) -> Optional[str]:
    if score is None:
        return None
    s = float(score)
    if s >= 80:
        return "A"
    if s >= 65:
        return "B"
    if s >= 50:
        return "C"
    if s >= 35:
        return "D"
    return "F"


def read_line(grade: Optional[str], setup_band: Optional[str], direction: str, horizon: str = "swing") -> str:
    if grade is not None and setup_band is not None and horizon == "day":
        if setup_band in ("Strong", "Prime"):
            return f"Momentum {direction.lower()} setup for an intraday/short swing — technicals lead; manage tightly."
        return "No intraday edge — technicals don't support a day trade here; stand aside."
    if grade is not None and setup_band is not None and horizon == "long":
        q_strong_l = grade in ("A", "B"); q_weak_l = grade in ("D", "F")
        s_good_l = setup_band in ("Strong", "Prime")
        if q_strong_l and s_good_l:
            return "High-quality compounder with a strong long-term setup — accumulate with conviction."
        if q_strong_l:
            return "High-quality compounder; entry is soft but matters little over months — start scaling in, add on weakness."
        if q_weak_l:
            return "Weak fundamentals — not a long-term hold regardless of price; avoid."
        return "Average quality for a long-term hold — own only at a clear value entry."
    q_strong = grade in ("A", "B")
    q_weak = grade in ("D", "F")
    s_good = setup_band in ("Strong", "Prime")
    s_poor = setup_band in ("Weak", "Fair")
    if grade is None or setup_band is None:
        return f"{direction} setup; full read needs both quality and calibration data."
    if q_strong and s_good:
        return f"High-quality company and a strong {direction.lower()} setup — the two align."
    if q_strong and s_poor:
        return ("High-quality company, but a weak entry right now — "
                "watchlist candidate, not a buy here.")
    if q_weak and s_good:
        return ("Strong setup on a weak-quality company — a trade, not an investment; "
                "keep size and stops tight.")
    if q_weak and s_poor:
        return "Weak on both quality and setup — little here; likely avoid."
    if s_good:
        return f"Average quality with a strong {direction.lower()} setup — a timing trade."
    return "Average quality and a soft setup — no edge; wait for a better entry."


def decide_action(grade: Optional[str], band: Optional[str], direction: str, horizon: str = "swing") -> str:
    if direction == "Short":
        return "AVOID"
    if direction == "Stand aside":
        return "WATCH"
    if band is None:
        return "WATCH"
    if horizon == "day":
        # Day-trade: setup is the whole call; quality is irrelevant intraday.
        return {"Prime": "STRONG BUY", "Strong": "BUY", "Fair": "WATCH", "Weak": "AVOID"}.get(band, "WATCH")
    if grade is None:
        return "WATCH"
    if horizon == "long":
        # Long-term: quality leads; a soft entry on a quality name is still an accumulate.
        if grade in ("A", "B"):
            if band == "Prime":
                return "STRONG BUY"
            if band == "Strong":
                return "BUY"
            return "ACCUMULATE"
        if grade == "C":
            return "BUY" if band in ("Prime", "Strong") else "WATCH"
        return "AVOID"
    # swing (default): balanced quality x setup matrix.
    if grade in ("A", "B"):
        if band == "Prime":
            return "STRONG BUY"
        if band == "Strong":
            return "BUY"
        if band == "Fair":
            return "ACCUMULATE"
        return "WATCH"
    if grade == "C":
        return "BUY" if band in ("Prime", "Strong") else "WATCH"
    return "SPECULATIVE" if band in ("Prime", "Strong") else "AVOID"


ACTION_RANK = {"STRONG BUY": 5, "BUY": 4, "ACCUMULATE": 3, "WATCH": 2, "SPECULATIVE": 1, "AVOID": 0}


def action_urgency(action: str) -> str:
    if action in ("STRONG BUY", "BUY"):
        return "ACT_NOW"
    if action in ("ACCUMULATE", "WATCH"):
        return "WATCH"
    return "REST"


def size_cap_pct(conviction: float) -> float:
    try:
        c = max(0.0, min(10.0, float(conviction)))
    except (TypeError, ValueError):
        return 0.0
    return round(c * 10.0, 0)
