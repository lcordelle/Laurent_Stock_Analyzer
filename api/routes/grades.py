from __future__ import annotations
import asyncio
import time
import logging
from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
import yfinance as yf
from api.auth import verify_token
from api.models.responses import (
    GradeItem, FactorGradesResponse, DividendGradeSet,
    DividendScorecardResponse, EpsHistoryItem, EarningsAnalysisResponse,
)
from utils.peer_benchmark import PeerBenchmark

router = APIRouter(tags=["grades"])
logger = logging.getLogger(__name__)

GRADE_THRESHOLDS = [
    (92, "A+"), (85, "A"), (77, "A-"), (69, "B+"), (62, "B"), (54, "B-"),
    (46, "C+"), (38, "C"), (31, "C-"), (23, "D+"), (15, "D"), (8, "D-"), (0, "F"),
]


def _sf(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        f = float(v)
        return None if f != f else f
    except (TypeError, ValueError):
        return None


def _percentile_to_grade(pct: float) -> str:
    for threshold, grade in GRADE_THRESHOLDS:
        if pct >= threshold:
            return grade
    return "F"


def _percentile(value: Optional[float], peer_values: list[float], higher_is_better: bool) -> Optional[float]:
    if value is None or not peer_values:
        return None
    all_vals = peer_values + [value]
    rank = sum(1 for v in all_vals if v < value)
    pct = rank / len(all_vals) * 100
    return pct if higher_is_better else 100 - pct


def _fetch_info(ticker: str) -> dict:
    try:
        return yf.Ticker(ticker).info or {}
    except Exception:
        return {}


def _factor_grade(stock_val: Optional[float], peer_vals: list[float], higher_is_better: bool, label: str) -> GradeItem:
    pct = _percentile(stock_val, peer_vals, higher_is_better)
    if pct is None:
        return GradeItem(grade="N/A", tooltip=f"Insufficient data for {label}")
    grade = _percentile_to_grade(pct)
    return GradeItem(grade=grade, percentile=round(pct, 1), tooltip=f"{label}: {pct:.0f}th percentile vs peers")


def _compute_factor_grades_sync(ticker: str, sector: str) -> FactorGradesResponse:
    peers = PeerBenchmark().get_sector_peers(ticker, sector)[:8]

    stock_info = _fetch_info(ticker)
    peer_infos: list[dict] = []
    for p in peers:
        time.sleep(0.25)
        peer_infos.append(_fetch_info(p))

    def collect(infos: list[dict], key: str, transform=None) -> list[float]:
        out = []
        for info in infos:
            v = _sf(info.get(key))
            if v is not None:
                out.append(transform(v) if transform else v)
        return out

    mktcap = _sf(stock_info.get("marketCap"))
    rev = _sf(stock_info.get("totalRevenue"))
    ps_stock = mktcap / rev if mktcap and rev and rev > 0 else None
    ev_ebitda_stock = _sf(stock_info.get("enterpriseToEbitda"))

    peer_ps = []
    for info in peer_infos:
        mc = _sf(info.get("marketCap"))
        rv = _sf(info.get("totalRevenue"))
        if mc and rv and rv > 0:
            peer_ps.append(mc / rv)

    # Value: lower is better (cheap valuation = high grade)
    pe_vals = [_sf(i.get("trailingPE")) for i in peer_infos]
    pe_peers = [v for v in pe_vals if v is not None]
    value_metrics = [
        _percentile(_sf(stock_info.get("trailingPE")), pe_peers, False),
        _percentile(_sf(stock_info.get("forwardPE")), collect(peer_infos, "forwardPE"), False),
        _percentile(_sf(stock_info.get("priceToBook")), collect(peer_infos, "priceToBook"), False),
        _percentile(ps_stock, peer_ps, False),
        _percentile(ev_ebitda_stock, collect(peer_infos, "enterpriseToEbitda"), False),
    ]
    value_pcts = [v for v in value_metrics if v is not None]
    value_pct = sum(value_pcts) / len(value_pcts) if value_pcts else None
    value_grade = GradeItem(
        grade=_percentile_to_grade(value_pct) if value_pct is not None else "N/A",
        percentile=round(value_pct, 1) if value_pct is not None else None,
        tooltip=f"Value: {value_pct:.0f}th pct (P/E, Fwd P/E, P/B, P/S, EV/EBITDA)" if value_pct is not None else "Insufficient data",
    )

    # Growth: higher is better
    growth_metrics = [
        _percentile(_sf(stock_info.get("revenueGrowth")), collect(peer_infos, "revenueGrowth"), True),
        _percentile(_sf(stock_info.get("earningsGrowth")), collect(peer_infos, "earningsGrowth"), True),
    ]
    growth_pcts = [v for v in growth_metrics if v is not None]
    growth_pct = sum(growth_pcts) / len(growth_pcts) if growth_pcts else None
    growth_grade = GradeItem(
        grade=_percentile_to_grade(growth_pct) if growth_pct is not None else "N/A",
        percentile=round(growth_pct, 1) if growth_pct is not None else None,
        tooltip=f"Growth: {growth_pct:.0f}th pct (revenue, earnings growth)" if growth_pct is not None else "Insufficient data",
    )

    # Profitability: higher is better
    prof_metrics = [
        _percentile(_sf(stock_info.get("grossMargins")), collect(peer_infos, "grossMargins"), True),
        _percentile(_sf(stock_info.get("profitMargins")), collect(peer_infos, "profitMargins"), True),
        _percentile(_sf(stock_info.get("returnOnEquity")), collect(peer_infos, "returnOnEquity"), True),
    ]
    prof_pcts = [v for v in prof_metrics if v is not None]
    prof_pct = sum(prof_pcts) / len(prof_pcts) if prof_pcts else None
    prof_grade = GradeItem(
        grade=_percentile_to_grade(prof_pct) if prof_pct is not None else "N/A",
        percentile=round(prof_pct, 1) if prof_pct is not None else None,
        tooltip=f"Profitability: {prof_pct:.0f}th pct (gross margin, net margin, ROE)" if prof_pct is not None else "Insufficient data",
    )

    # Momentum: use 52w high/low position as proxy
    hi52 = _sf(stock_info.get("fiftyTwoWeekHigh"))
    lo52 = _sf(stock_info.get("fiftyTwoWeekLow"))
    cur = _sf(stock_info.get("currentPrice") or stock_info.get("regularMarketPrice"))
    mom_stock = (cur - lo52) / (hi52 - lo52) if hi52 and lo52 and hi52 > lo52 and cur else None

    peer_moms = []
    for info in peer_infos:
        ph = _sf(info.get("fiftyTwoWeekHigh"))
        pl = _sf(info.get("fiftyTwoWeekLow"))
        pc = _sf(info.get("currentPrice") or info.get("regularMarketPrice"))
        if ph and pl and ph > pl and pc:
            peer_moms.append((pc - pl) / (ph - pl))

    mom_pct = _percentile(mom_stock, peer_moms, True)
    mom_grade = GradeItem(
        grade=_percentile_to_grade(mom_pct) if mom_pct is not None else "N/A",
        percentile=round(mom_pct, 1) if mom_pct is not None else None,
        tooltip=f"Momentum: {mom_pct:.0f}th pct (52-week price position)" if mom_pct is not None else "Insufficient data",
    )

    # EPS Revisions: use recommendation mean as proxy (lower mean = more bullish = better)
    rec_mean_stock = _sf(stock_info.get("recommendationMean"))
    peer_rec_means = collect(peer_infos, "recommendationMean")
    eps_rev_pct = _percentile(rec_mean_stock, peer_rec_means, False) if rec_mean_stock else None
    eps_rev_grade = GradeItem(
        grade=_percentile_to_grade(eps_rev_pct) if eps_rev_pct is not None else "N/A",
        percentile=round(eps_rev_pct, 1) if eps_rev_pct is not None else None,
        tooltip=f"EPS Revisions: {eps_rev_pct:.0f}th pct (analyst consensus trend)" if eps_rev_pct is not None else "Insufficient data",
    )

    return FactorGradesResponse(
        ticker=ticker.upper(),
        sector=sector,
        n_peers=len(peers),
        grades={
            "value": value_grade,
            "growth": growth_grade,
            "profitability": prof_grade,
            "momentum": mom_grade,
            "eps_revisions": eps_rev_grade,
        },
    )


def _compute_dividend_scorecard_sync(ticker: str, sector: str) -> DividendScorecardResponse:
    info = _fetch_info(ticker)
    div_yield = _sf(info.get("dividendYield"))
    div_rate = _sf(info.get("dividendRate"))

    if not div_yield or div_yield < 0.001:
        return DividendScorecardResponse(ticker=ticker.upper(), pays_dividend=False)

    # Safety: absolute thresholds
    payout = _sf(info.get("payoutRatio")) or 0.0
    debt_eq = _sf(info.get("debtToEquity")) or 0.0
    interest_cov = _sf(info.get("ebitda", 0)) or 0
    total_debt = _sf(info.get("totalDebt", 0)) or 0
    int_exp = _sf(info.get("interestExpense", 0)) or 0
    icr = abs(interest_cov / int_exp) if int_exp and int_exp != 0 else 10.0

    safety_pts = 100
    if payout > 0.85: safety_pts -= 40
    elif payout > 0.70: safety_pts -= 20
    elif payout > 0.50: safety_pts -= 10
    if debt_eq > 2.0: safety_pts -= 25
    elif debt_eq > 1.5: safety_pts -= 15
    elif debt_eq > 1.0: safety_pts -= 5
    if icr < 1.5: safety_pts -= 25
    elif icr < 2.0: safety_pts -= 15
    elif icr < 3.0: safety_pts -= 5
    safety_pct = max(0, min(100, safety_pts))
    safety_grade = GradeItem(
        grade=_percentile_to_grade(safety_pct),
        percentile=float(safety_pct),
        tooltip=f"Safety: payout {payout:.0%}, D/E {debt_eq:.1f}, ICR {icr:.1f}x",
    )

    # Yield: sector-relative
    peers = PeerBenchmark().get_sector_peers(ticker, sector)[:6]
    peer_yields = []
    for p in peers:
        time.sleep(0.2)
        pi = _fetch_info(p)
        py = _sf(pi.get("dividendYield"))
        if py and py > 0.001:
            peer_yields.append(py)
    yield_pct = _percentile(div_yield, peer_yields, True)
    yield_grade = GradeItem(
        grade=_percentile_to_grade(yield_pct) if yield_pct is not None else "C",
        percentile=round(yield_pct, 1) if yield_pct is not None else None,
        tooltip=f"Yield: {div_yield:.2%} vs sector peers",
    )

    # Growth: use 5yr avg div growth (proxy via trailing EPS growth)
    div_growth = _sf(info.get("earningsGrowth")) or 0.05
    growth_score = min(100, max(0, 50 + div_growth * 200))
    growth_grade = GradeItem(
        grade=_percentile_to_grade(growth_score),
        percentile=round(growth_score, 1),
        tooltip=f"Dividend growth proxy: {div_growth:.1%}",
    )

    # Consistency: use years of dividend payment as proxy
    try:
        t = yf.Ticker(ticker)
        divs = t.dividends
        if divs is not None and len(divs) > 0:
            years = (divs.index[-1] - divs.index[0]).days / 365.25
        else:
            years = 0
    except Exception:
        years = 0

    if years >= 25: cons_pct = 95
    elif years >= 15: cons_pct = 80
    elif years >= 10: cons_pct = 65
    elif years >= 5: cons_pct = 50
    elif years >= 2: cons_pct = 35
    else: cons_pct = 15
    consistency_grade = GradeItem(
        grade=_percentile_to_grade(cons_pct),
        percentile=float(cons_pct),
        tooltip=f"Consistency: ~{years:.0f} years of dividend history",
    )

    return DividendScorecardResponse(
        ticker=ticker.upper(),
        pays_dividend=True,
        current_yield=div_yield,
        annual_rate=div_rate,
        grades=DividendGradeSet(
            safety=safety_grade,
            growth=growth_grade,
            yield_grade=yield_grade,
            consistency=consistency_grade,
        ),
    )


def _compute_earnings_sync(ticker: str) -> EarningsAnalysisResponse:
    try:
        t = yf.Ticker(ticker)
        history = t.earnings_history
        eps_items: list[EpsHistoryItem] = []

        if history is not None and not history.empty:
            for date_idx, row in history.head(8).iterrows():
                act = _sf(row.get("epsActual"))
                est = _sf(row.get("epsEstimate"))
                surp = _sf(row.get("surprisePercent"))
                beat = (act >= est) if act is not None and est is not None else None
                date_str = date_idx.strftime("%Y-%m-%d") if hasattr(date_idx, "strftime") else str(date_idx)[:10]
                eps_items.append(EpsHistoryItem(
                    date=date_str,
                    eps_actual=act,
                    eps_estimate=est,
                    surprise_pct=surp,
                    beat=beat,
                ))

        if not eps_items:
            qe = t.quarterly_earnings
            if qe is not None and not qe.empty:
                for date_idx, row in qe.head(8).iterrows():
                    act = _sf(row.get("Earnings"))
                    date_str = str(date_idx)[:10] if not hasattr(date_idx, "strftime") else date_idx.strftime("%Y-%m-%d")
                    eps_items.append(EpsHistoryItem(date=date_str, eps_actual=act))

        last4 = [e for e in eps_items if e.beat is not None][:4]
        beat_rate = (sum(1 for e in last4 if e.beat) / len(last4) * 100) if last4 else None
        surps = [e.surprise_pct for e in last4 if e.surprise_pct is not None]
        avg_surp = sum(surps) / len(surps) if surps else None

        next_date = None
        try:
            ed = t.earnings_dates
            if ed is not None and not ed.empty:
                import pandas as pd
                now = pd.Timestamp.now(tz="UTC")
                future = ed[ed.index > now]
                if not future.empty:
                    next_date = future.index[0].strftime("%Y-%m-%d")
        except Exception:
            pass

        return EarningsAnalysisResponse(
            ticker=ticker.upper(),
            data_available=len(eps_items) > 0,
            eps_history=eps_items,
            beat_rate_4q=beat_rate,
            avg_surprise_pct_4q=avg_surp,
            next_earnings_date=next_date,
        )
    except Exception as e:
        logger.warning("Earnings analysis failed for %s: %s", ticker, e)
        return EarningsAnalysisResponse(ticker=ticker.upper(), data_available=False)


@router.get("/grades/factors", response_model=FactorGradesResponse)
async def factor_grades(
    ticker: str = Query(...),
    sector: str = Query(default=""),
    _: str = Depends(verify_token),
):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _compute_factor_grades_sync, ticker.upper(), sector)


@router.get("/grades/dividend", response_model=DividendScorecardResponse)
async def dividend_scorecard(
    ticker: str = Query(...),
    sector: str = Query(default=""),
    _: str = Depends(verify_token),
):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _compute_dividend_scorecard_sync, ticker.upper(), sector)


@router.get("/grades/earnings", response_model=EarningsAnalysisResponse)
async def earnings_analysis(
    ticker: str = Query(...),
    _: str = Depends(verify_token),
):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _compute_earnings_sync, ticker.upper())
