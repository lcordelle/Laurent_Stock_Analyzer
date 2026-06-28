"""
Factor Grade Engine — sector-relative A+ to F grades across five dimensions.
Mirrors Seeking Alpha's Quant Factor Grade system using yfinance data.
"""

import time
import re
import numpy as np
import yfinance as yf
import streamlit as st

from config import (
    GRADE_PERCENTILE_THRESHOLDS,
    SECTOR_METRIC_MEDIANS,
)

# Factor definitions: metric keys, direction (higher=better), and weight
FACTOR_METRICS = {
    "value": {
        "metrics": ["pe", "fwd_pe", "pb", "ps", "ev_ebitda"],
        "higher_is_better": False,
    },
    "growth": {
        "metrics": ["revenue_growth", "eps_growth", "ebitda_growth", "fcf_growth"],
        "higher_is_better": True,
    },
    "profitability": {
        "metrics": ["gross_margin", "net_margin", "roe", "roic", "fcf_margin"],
        "higher_is_better": True,
    },
    "momentum": {
        "metrics": ["mom_1m", "mom_3m", "mom_6m", "mom_12m"],
        "higher_is_better": True,
    },
}


def _percentile_to_grade(pct):
    if pct is None:
        return "N/A"
    for threshold, grade in GRADE_PERCENTILE_THRESHOLDS:
        if pct >= threshold:
            return grade
    return "F"


def _compute_percentile_in_peer_set(value, peer_values, higher_is_better):
    """Return 0-100 percentile of value within (peer_values + [value])."""
    valid = [v for v in peer_values if v is not None and not np.isnan(v)]
    if len(valid) < 2:
        return None
    all_vals = valid + [value]
    n = len(all_vals)
    count_below = sum(v < value for v in all_vals)
    count_equal = sum(v == value for v in all_vals)
    rank = count_below + (count_equal + 1) / 2
    pct = (rank / n) * 100
    return pct if higher_is_better else (100 - pct)


_SECTOR_ALIASES = {
    "financials": "Financial Services",
    "financial services": "Financial Services",
    "consumer discretionary": "Consumer Cyclical",
    "consumer cyclical": "Consumer Cyclical",
    "consumer staples": "Consumer Defensive",
    "consumer defensive": "Consumer Defensive",
}


def _normalize_sector(sector):
    if sector is None:
        return "_default"
    if sector in SECTOR_METRIC_MEDIANS:
        return sector
    normalized = _SECTOR_ALIASES.get(sector.lower())
    if normalized and normalized in SECTOR_METRIC_MEDIANS:
        return normalized
    return "_default"


def _get_sector_fallback(sector, metric_key):
    key = _normalize_sector(sector)
    medians = SECTOR_METRIC_MEDIANS.get(key) or SECTOR_METRIC_MEDIANS["_default"]
    return medians.get(metric_key)


def _safe_div(a, b):
    try:
        if b and b != 0:
            return a / b
    except Exception:
        pass
    return None


def _fetch_metrics_for_ticker(ticker_sym):
    """Fetch all sub-metrics for a single ticker. Returns dict with None for missing values."""
    try:
        t = yf.Ticker(ticker_sym)
        info = t.info or {}

        # Price history for momentum
        hist = t.history(period="1y", auto_adjust=True)
        close = hist["Close"] if not hist.empty else None

        def mom(days):
            if close is None or len(close) < days + 1:
                return None
            try:
                old = close.iloc[-(days + 1)]
                new = close.iloc[-1]
                return (new - old) / old if old else None
            except Exception:
                return None

        # Financials for EBITDA/FCF growth
        try:
            fin = t.financials
            cf = t.cashflow
        except Exception:
            fin = None
            cf = None

        def _fin_row(df, *keys):
            if df is None or df.empty:
                return None, None
            for k in keys:
                try:
                    row = df.loc[k]
                    vals = row.dropna()
                    if len(vals) >= 2:
                        return float(vals.iloc[0]), float(vals.iloc[1])
                except Exception:
                    continue
            return None, None

        ebitda_curr, ebitda_prev = _fin_row(fin, "EBITDA", "Ebitda")
        fcf_curr, fcf_prev = _fin_row(cf, "Free Cash Flow", "FreeCashFlow")
        rev_curr = info.get("totalRevenue") or None

        ebitda_growth = _safe_div(ebitda_curr - ebitda_prev, abs(ebitda_prev)) if ebitda_curr and ebitda_prev else None
        fcf_growth = _safe_div(fcf_curr - fcf_prev, abs(fcf_prev)) if fcf_curr and fcf_prev else None

        mktcap = info.get("marketCap")
        ps = _safe_div(mktcap, rev_curr) if mktcap and rev_curr else None

        # ROIC: FCF / Invested Capital
        ic = None
        try:
            bs = t.balance_sheet
            if bs is not None and not bs.empty:
                for k in ["Invested Capital", "InvestedCapital"]:
                    try:
                        ic = float(bs.loc[k].iloc[0])
                        break
                    except Exception:
                        pass
        except Exception:
            pass
        roic = _safe_div(fcf_curr, ic) if fcf_curr and ic else info.get("returnOnAssets")

        fcf_margin = _safe_div(info.get("freeCashflow"), rev_curr) if rev_curr else None

        return {
            "pe": info.get("trailingPE"),
            "fwd_pe": info.get("forwardPE"),
            "pb": info.get("priceToBook"),
            "ps": ps,
            "ev_ebitda": info.get("enterpriseToEbitda"),
            "revenue_growth": info.get("revenueGrowth"),
            "eps_growth": info.get("earningsGrowth"),
            "ebitda_growth": ebitda_growth,
            "fcf_growth": fcf_growth,
            "gross_margin": info.get("grossMargins"),
            "net_margin": info.get("profitMargins"),
            "roe": info.get("returnOnEquity"),
            "roic": roic,
            "fcf_margin": fcf_margin,
            "mom_1m": mom(21),
            "mom_3m": mom(63),
            "mom_6m": mom(126),
            "mom_12m": mom(252),
        }
    except Exception:
        return {k: None for k in [
            "pe", "fwd_pe", "pb", "ps", "ev_ebitda",
            "revenue_growth", "eps_growth", "ebitda_growth", "fcf_growth",
            "gross_margin", "net_margin", "roe", "roic", "fcf_margin",
            "mom_1m", "mom_3m", "mom_6m", "mom_12m",
        ]}


def _compute_eps_revision_score(ticker_sym):
    """Compute a 0-100 synthetic EPS revision score from yfinance estimate data."""
    try:
        t = yf.Ticker(ticker_sym)

        # Beat streak from earnings history
        beat_streak = 0
        try:
            eh = t.earnings_history
            if eh is not None and not eh.empty and "surprisePercent" in eh.columns:
                for v in eh["surprisePercent"].dropna().head(4):
                    if v > 0:
                        beat_streak += 1
                    else:
                        break
        except Exception:
            pass

        # Revision counts (7d)
        ups_7d = downs_7d = 0
        try:
            rev = t.eps_revisions
            if rev is not None and not rev.empty:
                for col in rev.columns:
                    row = rev[col]
                    for idx in row.index:
                        idx_s = str(idx).lower()
                        if "up" in idx_s and "7" in idx_s:
                            try:
                                ups_7d += int(row[idx] or 0)
                            except Exception:
                                pass
                        elif "down" in idx_s and "7" in idx_s:
                            try:
                                downs_7d += int(row[idx] or 0)
                            except Exception:
                                pass
        except Exception:
            pass

        # EPS trend: compare current to 60d ago for current year
        trend_change_pct = 0.0
        try:
            trend = t.eps_trend
            if trend is not None and not trend.empty:
                for period in ["0y", "1y"]:
                    if period in trend.columns:
                        row = trend[period]
                        curr = None
                        old = None
                        for idx in row.index:
                            s = str(idx).lower()
                            if "current" == s:
                                curr = row[idx]
                            elif "60" in s:
                                old = row[idx]
                        if curr and old and old != 0:
                            trend_change_pct = (curr - old) / abs(old)
                            break
        except Exception:
            pass

        # If nothing returned anything useful, try a simple forward EPS check
        if ups_7d == downs_7d == beat_streak == 0 and trend_change_pct == 0:
            try:
                info = t.info or {}
                fwd = info.get("forwardEps")
                trail = info.get("trailingEps")
                if fwd and trail and trail != 0:
                    trend_change_pct = (fwd - trail) / abs(trail)
            except Exception:
                pass

        # Score formula (base 50, ±50)
        revision_balance = max(-3, min(3, ups_7d - downs_7d)) / 3 * 35
        trend_component = max(-0.10, min(0.10, trend_change_pct)) / 0.10 * 40
        streak_component = min(beat_streak, 4) / 4 * 25

        score = 50 + revision_balance + trend_component + streak_component
        score = max(0.0, min(100.0, score))

        return {
            "score": score,
            "ups_7d": ups_7d,
            "downs_7d": downs_7d,
            "beat_streak": beat_streak,
            "trend_change_pct": trend_change_pct,
            "direction": "up" if score > 55 else "down" if score < 45 else "flat",
        }
    except Exception:
        return {"score": None, "direction": "unavailable", "ups_7d": 0, "downs_7d": 0, "beat_streak": 0}


def _grade_factor(stock_metrics, peer_metrics_list, factor, sector):
    """Grade one factor for the stock vs its peers. Returns grade dict."""
    config = FACTOR_METRICS[factor]
    metric_keys = config["metrics"]
    higher_is_better = config["higher_is_better"]

    sub_pcts = {}
    for key in metric_keys:
        stock_val = stock_metrics.get(key)
        if stock_val is None or (isinstance(stock_val, float) and np.isnan(stock_val)):
            sub_pcts[key] = None
            continue

        peer_vals = [pm.get(key) for pm in peer_metrics_list]
        valid_peers = [v for v in peer_vals if v is not None and not np.isnan(v)]

        if len(valid_peers) >= 2:
            pct = _compute_percentile_in_peer_set(stock_val, peer_vals, higher_is_better)
            sub_pcts[key] = pct
        else:
            # Absolute threshold fallback
            fallback = _get_sector_fallback(sector, key)
            if fallback is not None and fallback != 0:
                ratio = stock_val / fallback
                if higher_is_better:
                    pct = min(100, max(0, 50 + (ratio - 1) * 50))
                else:
                    pct = min(100, max(0, 50 - (ratio - 1) * 50))
                sub_pcts[key] = pct
            else:
                sub_pcts[key] = None

    valid_pcts = [v for v in sub_pcts.values() if v is not None]
    if not valid_pcts:
        return {
            "grade": "N/A",
            "percentile": None,
            "sub_scores": sub_pcts,
            "data_quality": "unavailable",
            "n_peers_used": len(peer_metrics_list),
            "tooltip": "Insufficient data",
        }

    composite_pct = float(np.mean(valid_pcts))
    data_quality = "sector_relative" if len(peer_metrics_list) >= 3 else "absolute_threshold"

    return {
        "grade": _percentile_to_grade(composite_pct),
        "percentile": round(composite_pct, 1),
        "sub_scores": sub_pcts,
        "data_quality": data_quality,
        "n_peers_used": len(peer_metrics_list),
        "tooltip": f"{_percentile_to_grade(composite_pct)} ({composite_pct:.0f}th pct) vs {len(peer_metrics_list)} sector peers",
    }


@st.cache_data(ttl=3600, show_spinner=False)
def compute_factor_grades(ticker, sector):
    """
    Compute five sector-relative factor grades (A+ to F) for a stock.
    Returns dict with 'grades', 'sector', 'n_peers', 'computed_at'.
    """
    from utils.peer_benchmark import PeerBenchmark
    from datetime import datetime

    pb = PeerBenchmark()
    peers = pb.get_sector_peers(ticker, sector)[:8]

    # Fetch stock metrics
    stock_metrics = _fetch_metrics_for_ticker(ticker)

    # Fetch peer metrics with rate-limit delay
    peer_metrics_list = []
    for peer in peers:
        m = _fetch_metrics_for_ticker(peer)
        peer_metrics_list.append(m)
        time.sleep(0.3)

    # Grade the four data-driven factors
    grades = {}
    normalized_sector = _normalize_sector(sector)
    for factor in ["value", "growth", "profitability", "momentum"]:
        grades[factor] = _grade_factor(stock_metrics, peer_metrics_list, factor, normalized_sector)

    # EPS Revisions: standalone score (not peer-relative)
    rev = _compute_eps_revision_score(ticker)
    if rev["score"] is not None:
        grades["eps_revisions"] = {
            "grade": _percentile_to_grade(rev["score"]),
            "percentile": round(rev["score"], 1),
            "sub_scores": {
                "ups_7d": rev["ups_7d"],
                "downs_7d": rev["downs_7d"],
                "beat_streak": rev["beat_streak"],
            },
            "data_quality": "eps_revision_model",
            "n_peers_used": 0,
            "tooltip": f"EPS Revisions: {rev['direction']} — {rev['ups_7d']} upgrades / {rev['downs_7d']} downgrades (7d), {rev['beat_streak']}/4 recent beats",
        }
    else:
        grades["eps_revisions"] = {
            "grade": "N/A",
            "percentile": None,
            "sub_scores": {},
            "data_quality": "unavailable",
            "n_peers_used": 0,
            "tooltip": "EPS revision data unavailable",
        }

    return {
        "ticker": ticker,
        "sector": sector or "Unknown",
        "grades": grades,
        "n_peers": len(peer_metrics_list),
        "computed_at": datetime.now().isoformat(),
    }
