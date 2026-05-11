"""
Earnings Analysis — EPS/revenue surprise history, forward estimates, revision trend.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime


def _safe_float(v):
    try:
        return float(v) if v is not None and not pd.isna(v) else None
    except Exception:
        return None


def _format_period(idx_str):
    """Convert yfinance period index like '0q', '+1q', '0y', '+1y' to readable label."""
    mapping = {"0q": "Current Quarter", "+1q": "Next Quarter", "0y": "Current Year", "+1y": "Next Year"}
    return mapping.get(str(idx_str), str(idx_str))


def _parse_earnings_history(t):
    """Extract EPS surprise history from ticker."""
    results = []
    try:
        eh = t.earnings_history
        if eh is not None and not eh.empty:
            cols = [c.lower() for c in eh.columns]
            col_map = {c.lower(): c for c in eh.columns}

            def get_col(*candidates):
                for c in candidates:
                    if c.lower() in cols:
                        return col_map[c.lower()]
                return None

            actual_col = get_col("epsActual", "actual", "eps_actual")
            estimate_col = get_col("epsEstimate", "estimate", "eps_estimate")
            surprise_col = get_col("surprisePercent", "surprise_pct", "epssurprisepct")

            if actual_col and estimate_col:
                for i, (idx, row) in enumerate(eh.iterrows()):
                    if i >= 8:
                        break
                    actual = _safe_float(row.get(actual_col))
                    estimate = _safe_float(row.get(estimate_col))
                    surprise_pct = None
                    if surprise_col:
                        v = _safe_float(row.get(surprise_col))
                        surprise_pct = v * 100 if v is not None and abs(v) < 10 else v
                    elif actual is not None and estimate is not None and estimate != 0:
                        surprise_pct = ((actual - estimate) / abs(estimate)) * 100

                    date_str = str(idx.date()) if hasattr(idx, "date") else str(idx)
                    quarter = f"Q{(idx.month - 1) // 3 + 1} {idx.year}" if hasattr(idx, "month") else date_str
                    results.append({
                        "quarter": quarter,
                        "date": date_str,
                        "actual": actual,
                        "estimate": estimate,
                        "surprise_pct": round(surprise_pct, 2) if surprise_pct is not None else None,
                        "beat": (surprise_pct > 0) if surprise_pct is not None else None,
                    })
    except Exception:
        pass
    return results


def _parse_forward_estimates(t):
    """Extract forward EPS and revenue estimates."""
    forward_eps = {}
    forward_rev = {}

    try:
        ee = t.earnings_estimate
        if ee is not None and not ee.empty:
            for period in ee.columns:
                row = ee[period]
                label = _format_period(period)
                forward_eps[label] = {
                    "avg": _safe_float(row.get("avg") or row.get("Avg")),
                    "low": _safe_float(row.get("low") or row.get("Low")),
                    "high": _safe_float(row.get("high") or row.get("High")),
                    "n_analysts": _safe_float(row.get("numberOfAnalysts") or row.get("numberofanalysts")),
                    "growth": _safe_float(row.get("growth") or row.get("Growth")),
                }
    except Exception:
        pass

    try:
        re_ = t.revenue_estimate
        if re_ is not None and not re_.empty:
            for period in re_.columns:
                row = re_[period]
                label = _format_period(period)
                forward_rev[label] = {
                    "avg": _safe_float(row.get("avg") or row.get("Avg")),
                    "low": _safe_float(row.get("low") or row.get("Low")),
                    "high": _safe_float(row.get("high") or row.get("High")),
                    "n_analysts": _safe_float(row.get("numberOfAnalysts") or row.get("numberofanalysts")),
                    "growth": _safe_float(row.get("growth") or row.get("Growth")),
                }
    except Exception:
        pass

    return forward_eps, forward_rev


def _parse_eps_trend(t):
    """Extract EPS trend (estimate revisions over time)."""
    trend = {}
    try:
        et = t.eps_trend
        if et is not None and not et.empty:
            for period in et.columns:
                label = _format_period(period)
                row = et[period]
                trend[label] = {
                    "current": _safe_float(row.get("current") or row.get("Current")),
                    "7d_ago": _safe_float(row.get("7daysAgo") or row.get("7DaysAgo")),
                    "30d_ago": _safe_float(row.get("30daysAgo") or row.get("30DaysAgo")),
                    "60d_ago": _safe_float(row.get("60daysAgo") or row.get("60DaysAgo")),
                    "90d_ago": _safe_float(row.get("90daysAgo") or row.get("90DaysAgo")),
                }
    except Exception:
        pass
    return trend


def _parse_eps_revisions(t):
    """Extract up/down revision counts."""
    revisions = {}
    try:
        er = t.eps_revisions
        if er is not None and not er.empty:
            for period in er.columns:
                label = _format_period(period)
                row = er[period]

                def _pick(*keys):
                    for k in keys:
                        v = _safe_float(row.get(k))
                        if v is not None:
                            return int(v)
                    return 0

                revisions[label] = {
                    "up_7d": _pick("upLast7days", "up_7d", "uplast7days"),
                    "up_30d": _pick("upLast30days", "up_30d", "uplast30days"),
                    "down_7d": _pick("downLast7Days", "down_7d", "downlast7days"),
                    "down_30d": _pick("downLast30days", "down_30d", "downlast30days"),
                }
    except Exception:
        pass
    return revisions


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_earnings_data(ticker):
    """
    Fetch comprehensive earnings data for a stock.
    Returns dict with eps_history, forward estimates, revision trend, and summary metrics.
    """
    try:
        t = yf.Ticker(ticker)

        eps_history = _parse_earnings_history(t)
        forward_eps, forward_rev = _parse_forward_estimates(t)
        eps_trend = _parse_eps_trend(t)
        eps_revisions = _parse_eps_revisions(t)

        # Summary stats from history
        beat_rate_4q = None
        avg_surprise_4q = None
        if eps_history:
            last4 = eps_history[:4]
            beats = [e for e in last4 if e.get("beat") is True]
            surprises = [e["surprise_pct"] for e in last4 if e.get("surprise_pct") is not None]
            if last4:
                beat_rate_4q = round(len(beats) / len(last4) * 100, 1)
            if surprises:
                avg_surprise_4q = round(sum(surprises) / len(surprises), 2)

        data_available = bool(eps_history or forward_eps or eps_trend)

        # Next earnings date
        next_earnings = None
        try:
            cal = t.calendar
            if cal is not None:
                if hasattr(cal, "get"):
                    ne = cal.get("Earnings Date")
                    if ne:
                        next_earnings = str(ne[0]) if isinstance(ne, list) else str(ne)
                elif hasattr(cal, "columns"):
                    for col in cal.columns:
                        if "earnings" in col.lower():
                            v = cal[col].iloc[0]
                            next_earnings = str(v) if v else None
                            break
        except Exception:
            pass

        return {
            "ticker": ticker,
            "eps_history": eps_history,
            "forward_eps": forward_eps,
            "forward_revenue": forward_rev,
            "eps_trend": eps_trend,
            "eps_revisions": eps_revisions,
            "beat_rate_4q": beat_rate_4q,
            "avg_surprise_pct_4q": avg_surprise_4q,
            "next_earnings_date": next_earnings,
            "data_available": data_available,
        }
    except Exception as e:
        return {
            "ticker": ticker,
            "eps_history": [],
            "forward_eps": {},
            "forward_revenue": {},
            "eps_trend": {},
            "eps_revisions": {},
            "beat_rate_4q": None,
            "avg_surprise_pct_4q": None,
            "next_earnings_date": None,
            "data_available": False,
        }
