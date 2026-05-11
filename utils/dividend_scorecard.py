"""
Dividend Scorecard — four-dimension grading: Safety, Growth, Yield, Consistency.
"""

import time
import numpy as np
import yfinance as yf
import streamlit as st

from config import (
    GRADE_PERCENTILE_THRESHOLDS,
    DIVIDEND_PAYOUT_THRESHOLDS,
    DIVIDEND_COVERAGE_THRESHOLDS,
    DIVIDEND_DEBT_THRESHOLDS,
)
from utils.peer_benchmark import PeerBenchmark


def _percentile_to_grade(pct):
    if pct is None:
        return "N/A"
    for threshold, grade in GRADE_PERCENTILE_THRESHOLDS:
        if pct >= threshold:
            return grade
    return "F"


def _score_to_grade(score):
    """Convert 0-100 absolute score to letter grade."""
    return _percentile_to_grade(score)


def _grade_dividend_safety(payout_ratio, interest_coverage, debt_equity):
    score = 100.0
    details = []

    if payout_ratio is not None:
        if payout_ratio > DIVIDEND_PAYOUT_THRESHOLDS[3]:    # >85%
            score -= 40; details.append(f"Payout {payout_ratio:.0%} very high")
        elif payout_ratio > DIVIDEND_PAYOUT_THRESHOLDS[2]:  # >70%
            score -= 25; details.append(f"Payout {payout_ratio:.0%} elevated")
        elif payout_ratio > DIVIDEND_PAYOUT_THRESHOLDS[1]:  # >50%
            score -= 10; details.append(f"Payout {payout_ratio:.0%} moderate")
        else:
            details.append(f"Payout {payout_ratio:.0%} healthy")

    if debt_equity is not None and debt_equity > 0:
        if debt_equity > DIVIDEND_DEBT_THRESHOLDS[3]:       # >2.0
            score -= 25; details.append(f"D/E {debt_equity:.1f}x high")
        elif debt_equity > DIVIDEND_DEBT_THRESHOLDS[2]:     # >1.5
            score -= 15; details.append(f"D/E {debt_equity:.1f}x elevated")
        elif debt_equity > DIVIDEND_DEBT_THRESHOLDS[1]:     # >1.0
            score -= 5
        else:
            details.append(f"D/E {debt_equity:.1f}x manageable")

    if interest_coverage is not None:
        if interest_coverage < DIVIDEND_COVERAGE_THRESHOLDS[3]:    # <1.5
            score -= 30; details.append(f"Coverage {interest_coverage:.1f}x very low")
        elif interest_coverage < DIVIDEND_COVERAGE_THRESHOLDS[2]:  # <2.0
            score -= 20; details.append(f"Coverage {interest_coverage:.1f}x low")
        elif interest_coverage < DIVIDEND_COVERAGE_THRESHOLDS[1]:  # <3.0
            score -= 10
        else:
            details.append(f"Coverage {interest_coverage:.1f}x good")

    score = max(0.0, min(100.0, score))
    tooltip = " | ".join(details) if details else "Safety assessment"
    return {"grade": _score_to_grade(score), "score": round(score), "tooltip": tooltip}


def _grade_dividend_growth(ticker_cagr, peer_cagrs):
    valid_peers = [v for v in peer_cagrs if v is not None and not np.isnan(v)]
    if ticker_cagr is None:
        return {"grade": "N/A", "percentile": None, "tooltip": "Growth data unavailable"}

    if len(valid_peers) >= 2:
        all_vals = valid_peers + [ticker_cagr]
        rank = sorted(all_vals).index(ticker_cagr) + 1
        pct = (rank / len(all_vals)) * 100
        tooltip = f"{pct:.0f}th percentile DPS growth vs {len(valid_peers)} peers ({ticker_cagr:.1%} CAGR)"
    else:
        # Absolute: >10% = A+, >5% = A, >2% = B, >0% = C, <0% = D
        if ticker_cagr > 0.10:
            pct = 95.0
        elif ticker_cagr > 0.05:
            pct = 80.0
        elif ticker_cagr > 0.02:
            pct = 60.0
        elif ticker_cagr > 0:
            pct = 45.0
        else:
            pct = 20.0
        tooltip = f"Dividend CAGR {ticker_cagr:.1%}"

    return {"grade": _percentile_to_grade(pct), "percentile": round(pct, 1), "tooltip": tooltip}


def _grade_dividend_yield(current_yield, peer_yields):
    valid_peers = [v for v in peer_yields if v is not None and not np.isnan(v)]
    if current_yield is None:
        return {"grade": "N/A", "percentile": None, "tooltip": "Yield data unavailable"}

    if len(valid_peers) >= 2:
        all_vals = valid_peers + [current_yield]
        rank = sorted(all_vals).index(current_yield) + 1
        pct = (rank / len(all_vals)) * 100
        tooltip = f"{pct:.0f}th percentile yield vs {len(valid_peers)} peers ({current_yield:.2%})"
    else:
        if current_yield > 0.04:
            pct = 92.0
        elif current_yield > 0.03:
            pct = 75.0
        elif current_yield > 0.02:
            pct = 55.0
        elif current_yield > 0.01:
            pct = 35.0
        else:
            pct = 15.0
        tooltip = f"Yield {current_yield:.2%}"

    return {"grade": _percentile_to_grade(pct), "percentile": round(pct, 1), "tooltip": tooltip}


def _grade_dividend_consistency(dividend_series):
    """Grade based on years of consecutive payments and increase streaks."""
    if dividend_series is None or dividend_series.empty:
        return {"grade": "N/A", "tooltip": "No dividend history"}

    try:
        annual = dividend_series.resample("YE").sum()
        annual = annual[annual > 0]
        years_paid = len(annual)
        if years_paid == 0:
            return {"grade": "F", "tooltip": "No dividends paid"}

        # Count consecutive increase years (from most recent)
        increases = 0
        vals = annual.values.tolist()
        for i in range(len(vals) - 1, 0, -1):
            if vals[i] > vals[i - 1]:
                increases += 1
            else:
                break

        if increases >= 25:
            grade, note = "A+", f"Dividend Aristocrat — {increases} yrs consecutive increases"
        elif increases >= 10:
            grade, note = "A", f"{increases} consecutive years of increases"
        elif increases >= 5:
            grade, note = "A-", f"{increases} consecutive years of increases"
        elif years_paid >= 10:
            grade, note = "B+", f"{years_paid} years paying, no long increase streak"
        elif years_paid >= 5:
            grade, note = "B", f"{years_paid} years of payment history"
        elif years_paid >= 3:
            grade, note = "B-", f"{years_paid} years of payment history"
        elif years_paid >= 2:
            grade, note = "C+", f"{years_paid} years of payment history"
        else:
            grade, note = "C", "1 year of payment history"

        return {"grade": grade, "tooltip": note}
    except Exception:
        return {"grade": "N/A", "tooltip": "Unable to compute consistency"}


def _compute_div_cagr(dividend_series, years=5):
    """5-year dividend CAGR from annual totals."""
    try:
        if dividend_series is None or dividend_series.empty:
            return None
        annual = dividend_series.resample("YE").sum()
        annual = annual[annual > 0]
        if len(annual) < 2:
            return None
        n = min(years, len(annual) - 1)
        latest = float(annual.iloc[-1])
        oldest = float(annual.iloc[-1 - n])
        if oldest <= 0:
            return None
        return (latest / oldest) ** (1 / n) - 1
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def compute_dividend_scorecard(ticker, sector):
    """
    Compute four-dimension dividend scorecard for a stock.
    Returns dict with 'pays_dividend', 'current_yield', 'annual_rate', 'grades'.
    """
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}

        current_yield = info.get("dividendYield")
        annual_rate = info.get("dividendRate")

        if not current_yield or current_yield <= 0:
            return {
                "ticker": ticker,
                "pays_dividend": False,
                "current_yield": 0,
                "annual_rate": 0,
                "grades": {
                    "safety": {"grade": "N/A", "tooltip": "No dividend"},
                    "growth": {"grade": "N/A", "tooltip": "No dividend"},
                    "yield": {"grade": "N/A", "tooltip": "No dividend"},
                    "consistency": {"grade": "N/A", "tooltip": "Company does not pay a dividend"},
                },
                "data_quality": "unavailable",
            }

        payout_ratio = info.get("payoutRatio")
        debt_equity = info.get("debtToEquity")
        if debt_equity:
            debt_equity = debt_equity / 100  # yfinance returns as e.g. 150 for 1.5x

        # Interest coverage: EBIT / interest expense
        interest_coverage = None
        try:
            fin = t.financials
            if fin is not None and not fin.empty:
                ebit = None
                interest = None
                for k in ["EBIT", "Operating Income"]:
                    try:
                        ebit = float(fin.loc[k].iloc[0])
                        break
                    except Exception:
                        pass
                for k in ["Interest Expense", "Net Interest Income"]:
                    try:
                        v = float(fin.loc[k].iloc[0])
                        interest = abs(v)
                        break
                    except Exception:
                        pass
                if ebit and interest and interest > 0:
                    interest_coverage = ebit / interest
        except Exception:
            pass

        divs = t.dividends
        ticker_cagr = _compute_div_cagr(divs)

        # Fetch peer dividend data for yield and growth comparison
        pb = PeerBenchmark()
        peers = pb.get_sector_peers(ticker, sector)[:6]
        peer_yields = []
        peer_cagrs = []
        for peer in peers:
            try:
                pt = yf.Ticker(peer)
                pi = pt.info or {}
                peer_yields.append(pi.get("dividendYield"))
                peer_cagrs.append(_compute_div_cagr(pt.dividends))
                time.sleep(0.2)
            except Exception:
                pass

        safety = _grade_dividend_safety(payout_ratio, interest_coverage, debt_equity)
        growth = _grade_dividend_growth(ticker_cagr, peer_cagrs)
        yield_grade = _grade_dividend_yield(current_yield, peer_yields)
        consistency = _grade_dividend_consistency(divs)

        return {
            "ticker": ticker,
            "pays_dividend": True,
            "current_yield": current_yield,
            "annual_rate": annual_rate,
            "grades": {
                "safety": safety,
                "growth": growth,
                "yield": yield_grade,
                "consistency": consistency,
            },
            "data_quality": "sector_relative" if len(peers) >= 3 else "absolute_threshold",
        }
    except Exception as e:
        return {
            "ticker": ticker,
            "pays_dividend": False,
            "current_yield": 0,
            "annual_rate": 0,
            "grades": {
                "safety": {"grade": "N/A", "tooltip": "Data error"},
                "growth": {"grade": "N/A", "tooltip": "Data error"},
                "yield": {"grade": "N/A", "tooltip": "Data error"},
                "consistency": {"grade": "N/A", "tooltip": "Data error"},
            },
            "data_quality": "unavailable",
        }
