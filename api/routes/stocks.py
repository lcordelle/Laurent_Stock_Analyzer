from __future__ import annotations
import asyncio
import logging
import os
import time
import numpy as np
import pandas as pd
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from api.auth import verify_token
from api.models.requests import AnalyzeRequest, BatchRequest
import yfinance as yf
from api.models.responses import (
    FullStockAnalysis, BatchAnalysisResponse,
    StockMetrics, ScoreBreakdown, ForecastResult,
    IndicatorData, TradingSignals, NewsArticle, AnalystRating, OHLCVRow,
    ShortInterestData, EarningsDate, RiskProfileData,
    VerdictSignalDetail, VerdictResponse, ValuationTunnel, Decision, HorizonDecision, Quality, Setup,
)
from utils.decision_engine import compute_conviction, quality_grade, read_line, decide_action, HORIZON_PROFILES
from utils.market_breadth import get_market_regime_cached
from utils.calibration import load_table, lookup as cal_lookup, percentile_of, band_for
from api.utils.verdict import _compute_verdict
from utils.risk_analysis import RiskAnalyzer
from utils.valuation_tunnel import build_valuation_tunnel
from utils.stock_analyzer import StockAnalyzer
from utils.news_market import NewsMarketData
from utils.ratings_aggregator import RatingsAggregator

router = APIRouter(tags=["stocks"])

logger = logging.getLogger(__name__)

_CAL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "calibration.json",
)
_CAL_TABLE: dict = {}


def _calibration_table() -> Optional[dict]:
    if "data" not in _CAL_TABLE:
        _CAL_TABLE["data"] = load_table(_CAL_PATH)
    return _CAL_TABLE["data"]


def _safe_float(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        f = float(v)
        return None if (f != f) else f  # NaN check
    except (TypeError, ValueError):
        return None


def _safe_int(v: Any) -> Optional[int]:
    try:
        if v is None:
            return None
        return int(v)
    except (TypeError, ValueError):
        return None


def _series_to_list(series: pd.Series) -> list[Optional[float]]:
    return [None if pd.isna(x) else float(x) for x in series]


def hist_to_ohlcv(hist: pd.DataFrame, max_rows: int = 252) -> list[OHLCVRow]:
    df = hist.tail(max_rows).copy()
    rows = []
    for idx, row in df.iterrows():
        o = row.get("Open")
        h = row.get("High")
        l = row.get("Low")
        c = row.get("Close")
        # Fall a single missing OHLC field back to a present price rather than
        # dropping the bar — dropping would shift this list out of positional
        # alignment with the indicator / valuation-tunnel arrays (same tail()).
        # Only a genuinely empty row (all four NaN — not seen in daily data) is skipped.
        present = [v for v in (c, o, h, l) if pd.notna(v)]
        if not present:
            continue
        ref = float(c) if pd.notna(c) else float(present[0])
        rows.append(OHLCVRow(
            date=idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx),
            open=float(o) if pd.notna(o) else ref,
            high=float(h) if pd.notna(h) else ref,
            low=float(l) if pd.notna(l) else ref,
            close=ref,
            volume=float(row["Volume"]) if pd.notna(row.get("Volume")) else 0.0,
        ))
    return rows


def _build_metrics(raw: dict) -> StockMetrics:
    return StockMetrics(
        current_price=_safe_float(raw.get("Current Price")),
        pe_ratio=_safe_float(raw.get("P/E Ratio")),
        forward_pe=_safe_float(raw.get("Forward P/E")),
        peg_ratio=_safe_float(raw.get("PEG Ratio")),
        price_to_book=_safe_float(raw.get("Price to Book")),
        dividend_yield=_safe_float(raw.get("Dividend Yield")),
        market_cap=_safe_float(raw.get("Market Cap")),
        gross_margin=_safe_float(raw.get("Gross Margin")),
        operating_margin=_safe_float(raw.get("Operating Margin")),
        profit_margin=_safe_float(raw.get("Profit Margin")),
        roe=_safe_float(raw.get("ROE")),
        roa=_safe_float(raw.get("ROA")),
        revenue_growth=_safe_float(raw.get("Revenue Growth")),
        earnings_growth=_safe_float(raw.get("Earnings Growth")),
        debt_to_equity=_safe_float(raw.get("Debt to Equity")),
        current_ratio=_safe_float(raw.get("Current Ratio")),
        quick_ratio=_safe_float(raw.get("Quick Ratio")),
        beta=_safe_float(raw.get("Beta")),
        target_price=_safe_float(raw.get("Target Price")),
        analyst_rating=raw.get("Analyst Rating"),
        number_of_analysts=_safe_int(raw.get("Number of Analysts")),
        recommendation_mean=_safe_float(raw.get("recommendationMean")),
        volume=_safe_float(raw.get("Volume")),
        average_volume=_safe_float(raw.get("Average Volume")),
        fifty_two_week_high=_safe_float(raw.get("52 Week High")),
        fifty_two_week_low=_safe_float(raw.get("52 Week Low")),
    )


def _build_score(raw: dict) -> ScoreBreakdown:
    return ScoreBreakdown(
        total=int(raw.get("total_score", 0)),
        components={k: int(v) for k, v in raw.get("components", {}).items()},
    )


def _build_forecast(raw: dict) -> Optional[ForecastResult]:
    if raw is None:
        return None
    return ForecastResult(
        current_price=float(raw["current_price"]),
        forecast_price=float(raw["forecast_price"]),
        forecast_change_pct=float(raw["forecast_change_pct"]),
        forecast_type=str(raw["forecast_type"]),
        probability=float(raw["probability"]),
        momentum=float(raw["momentum"]),
        volatility=float(raw["volatility"]),
        trend=str(raw["trend"]),
    )


def _build_indicators(hist: pd.DataFrame) -> IndicatorData:
    def col(name: str) -> list[float | None]:
        if name in hist.columns:
            return _series_to_list(hist[name].tail(252))
        return []

    return IndicatorData(
        sma_20=col("SMA_20"),
        sma_50=col("SMA_50"),
        sma_200=col("SMA_200"),
        rsi=col("RSI"),
        macd=col("MACD"),
        macd_signal=col("Signal"),
        bb_upper=col("BB_Upper"),
        bb_lower=col("BB_Lower"),
        obv=col("OBV"),
        vwap=col("VWAP"),
    )


def _build_news(raw_news: list) -> list[NewsArticle]:
    articles = []
    for item in (raw_news or []):
        if not isinstance(item, dict):
            continue
        title = item.get("title") or item.get("headline")
        if not title:
            continue
        articles.append(NewsArticle(
            title=str(title),
            summary=item.get("summary") or item.get("description"),
            url=item.get("link") or item.get("url"),
            published=str(item["published"]) if item.get("published") else None,
            sentiment=item.get("sentiment"),
        ))
    return articles


def _build_analyst(raw: Optional[dict]) -> Optional[AnalystRating]:
    if not raw:
        return None
    return AnalystRating(
        recommendation=raw.get("rating"),
        mean=_safe_float(raw.get("mean_rating")),
        count=_safe_int(raw.get("analysts")),
        target_high=_safe_float(raw.get("target_high")),
        target_low=_safe_float(raw.get("target_low")),
        target_mean=_safe_float(raw.get("target_price")),
    )


def _analyst_target_age(info: dict) -> Optional[int]:
    rec_date_ts = info.get("recommendationDate")
    if not rec_date_ts:
        return None
    try:
        return int((time.time() - float(rec_date_ts)) / 86400)
    except Exception:
        return None


def _compute_support_resistance(hist: pd.DataFrame, current_price: float) -> dict:
    """
    Identifies S/R levels from historical pivot clusters.
    A level requires 2+ touches within 1.5% to be considered significant.
    Returns nearest support below and resistance above, plus at-zone flags (within 3%).
    """
    empty = {"at_support": False, "at_resistance": False, "nearest_support": None, "nearest_resistance": None}
    if hist is None or len(hist) < 60 or current_price <= 0:
        return empty

    highs = hist["High"].values.astype(float)
    lows = hist["Low"].values.astype(float)
    n = len(highs)

    pivot_highs: list[float] = []
    pivot_lows: list[float] = []
    for i in range(3, n - 3):
        if highs[i] == np.nanmax(highs[max(0, i - 3): i + 4]):
            pivot_highs.append(float(highs[i]))
        if lows[i] == np.nanmin(lows[max(0, i - 3): i + 4]):
            pivot_lows.append(float(lows[i]))

    def cluster(levels: list[float]) -> list[float]:
        if not levels:
            return []
        groups: list[list[float]] = [[sorted(levels)[0]]]
        for lv in sorted(levels)[1:]:
            if (lv - groups[-1][0]) / groups[-1][0] <= 0.015:
                groups[-1].append(lv)
            else:
                groups.append([lv])
        return [float(np.mean(g)) for g in groups if len(g) >= 2]

    supports = cluster(pivot_lows)
    resistances = cluster(pivot_highs)

    below = [s for s in supports if s < current_price]
    above = [r for r in resistances if r > current_price]

    ns = round(max(below), 2) if below else None
    nr = round(min(above), 2) if above else None
    at_s = bool(ns and (current_price - ns) / current_price < 0.03)
    at_r = bool(nr and (nr - current_price) / current_price < 0.03)

    return {"at_support": at_s, "at_resistance": at_r, "nearest_support": ns, "nearest_resistance": nr}


def _compute_weekly_rsi(hist: pd.DataFrame) -> Optional[float]:
    """
    Derives weekly RSI from daily closes (14-week window).
    Uses the same data already fetched — no extra API call needed.
    Returns None when fewer than 20 weekly bars are available.
    """
    if hist is None or len(hist) < 70:
        return None
    try:
        idx = hist.index
        if hasattr(idx, "tz") and idx.tz is not None:
            idx = idx.tz_localize(None)
        weekly = hist["Close"].copy()
        weekly.index = pd.to_datetime(idx)
        weekly = weekly.resample("W").last().dropna()
        if len(weekly) < 20:
            return None
        delta = weekly.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        val = (100 - (100 / (1 + rs))).iloc[-1]
        return round(float(val), 1) if not np.isnan(float(val)) else None
    except Exception:
        return None


def _compute_rsi_reversal_profile(hist: pd.DataFrame) -> dict:
    """
    Derives per-stock RSI reversal zones from historical price action.

    For each RSI local minimum: if price rose >3% within 10 days → bullish reversal confirmed.
    For each RSI local maximum: if price fell >3% within 10 days → bearish reversal confirmed.
    The 35th percentile of confirmed bullish RSI levels becomes the stock's custom oversold threshold.
    The 65th percentile of confirmed bearish RSI levels becomes the custom overbought threshold.
    Falls back to 30/70 when fewer than 4 confirmed reversals are found.
    """
    if 'RSI' not in hist.columns or 'Close' not in hist.columns:
        return {"zone_low": 30.0, "zone_high": 70.0, "bullish_reversals": 0, "bearish_reversals": 0,
                "at_zone": False, "reversal_signal": None}

    rsi_arr = hist['RSI'].values.astype(float)
    close_arr = hist['Close'].values.astype(float)
    n = len(rsi_arr)

    if n < 60:
        return {"zone_low": 30.0, "zone_high": 70.0, "bullish_reversals": 0, "bearish_reversals": 0,
                "at_zone": False, "reversal_signal": None}

    bullish_levels: list[float] = []
    bearish_levels: list[float] = []

    for i in range(2, n - 12):
        r = rsi_arr[i]
        if np.isnan(r):
            continue
        # Local RSI minimum below 55 — potential bullish reversal
        if r < rsi_arr[i - 1] and r < rsi_arr[i - 2] and r < rsi_arr[i + 1] and r < 55:
            future = close_arr[i + 1: min(i + 12, n)]
            if len(future) and not np.all(np.isnan(future)):
                gain = (float(np.nanmax(future)) - close_arr[i]) / close_arr[i] * 100
                if gain > 3.0:
                    bullish_levels.append(r)
        # Local RSI maximum above 45 — potential bearish reversal
        if r > rsi_arr[i - 1] and r > rsi_arr[i - 2] and r > rsi_arr[i + 1] and r > 45:
            future = close_arr[i + 1: min(i + 12, n)]
            if len(future) and not np.all(np.isnan(future)):
                drop = (close_arr[i] - float(np.nanmin(future))) / close_arr[i] * 100
                if drop > 3.0:
                    bearish_levels.append(r)

    zone_low = round(float(np.percentile(bullish_levels, 35)), 1) if len(bullish_levels) >= 4 else 30.0
    zone_high = round(float(np.percentile(bearish_levels, 65)), 1) if len(bearish_levels) >= 4 else 70.0
    zone_low = float(np.clip(zone_low, 18.0, 45.0))
    zone_high = float(np.clip(zone_high, 55.0, 82.0))

    current_rsi: Optional[float] = None
    for i in range(n - 1, max(n - 6, -1), -1):
        if not np.isnan(rsi_arr[i]):
            current_rsi = float(rsi_arr[i])
            break

    reversal_signal: Optional[str] = None
    at_zone = False
    if current_rsi is not None:
        if current_rsi <= zone_low:
            reversal_signal = "HIST. OVERSOLD"
            at_zone = True
        elif current_rsi >= zone_high:
            reversal_signal = "HIST. OVERBOUGHT"
            at_zone = True
        elif current_rsi <= zone_low + 5:
            reversal_signal = "NEAR SUPPORT ZONE"
            at_zone = True
        elif current_rsi >= zone_high - 5:
            reversal_signal = "NEAR RESISTANCE ZONE"
            at_zone = True

    return {
        "zone_low": zone_low,
        "zone_high": zone_high,
        "bullish_reversals": len(bullish_levels),
        "bearish_reversals": len(bearish_levels),
        "at_zone": at_zone,
        "reversal_signal": reversal_signal,
    }


def _compute_trading_signals(
    hist: pd.DataFrame,
    current_price: Optional[float],
    earnings_dates: list | None = None,
    short_interest_pct: Optional[float] = None,
    recent_news_count: int = 0,
    fundamental_score: int = 0,
    analyst_upside_pct: Optional[float] = None,
) -> TradingSignals:
    if hist is None or len(hist) < 20 or current_price is None:
        return TradingSignals()

    last = hist.iloc[-1]

    def col_val(name: str) -> Optional[float]:
        v = last.get(name)
        return None if v is None or (isinstance(v, float) and v != v) else float(v)

    rsi = col_val("RSI")
    macd_val = col_val("MACD")
    macd_sig = col_val("Signal")
    sma_20 = col_val("SMA_20")
    sma_50 = col_val("SMA_50")
    sma_200 = col_val("SMA_200")
    bb_upper = col_val("BB_Upper")
    bb_lower = col_val("BB_Lower")
    adx_val = col_val("ADX")
    di_plus = col_val("DI_Plus")
    di_minus = col_val("DI_Minus")
    stoch_k = col_val("Stoch_K")
    stoch_d = col_val("Stoch_D")

    rp = _compute_rsi_reversal_profile(hist)
    rz_low = rp["zone_low"]
    rz_high = rp["zone_high"]

    score = 0.0

    if rsi is not None:
        if rsi <= rz_low: score += 2.0
        elif rsi < rz_low + 15: score += 1.0
        elif rsi >= rz_high: score -= 2.0
        elif rsi > rz_high - 15: score -= 0.5

    if macd_val is not None and macd_sig is not None:
        score += 1.0 if macd_val > macd_sig else -1.0

    if sma_20 is not None:
        score += 0.5 if current_price > sma_20 else -0.5
    if sma_50 is not None:
        score += 0.5 if current_price > sma_50 else -0.5
    if sma_200 is not None:
        score += 1.0 if current_price > sma_200 else -1.0

    if bb_upper is not None and bb_lower is not None:
        bb_range = bb_upper - bb_lower
        if bb_range > 0:
            bb_pos = (current_price - bb_lower) / bb_range
            if bb_pos < 0.2: score += 1.0
            elif bb_pos > 0.8: score -= 1.0

    # Volume confirmation — high volume confirms signals; low volume reduces confidence
    if 'Volume' in hist.columns and len(hist) >= 20:
        try:
            vol_avg = float(hist['Volume'].iloc[-20:].mean())
            last_vol = float(hist['Volume'].iloc[-1])
            if vol_avg > 0:
                vr = last_vol / vol_avg
                if vr >= 1.5:   score += 1.0
                elif vr < 0.7:  score -= 0.5
        except Exception:
            pass

    # ADX — trend strength filter (confirms directional signals; penalises ranging markets)
    adx_factor = 1.0
    if adx_val is not None:
        if adx_val < 20:
            adx_factor = 0.70   # Choppy: confidence will be multiplied down later
        elif adx_val > 25:
            score += 1.0 if (di_plus or 0) > (di_minus or 0) else -1.0
            if adx_val > 40:    # Very strong trend — amplify DI direction
                score += 0.5 if (di_plus or 0) > (di_minus or 0) else -0.5

    # OBV divergence — leading accumulation / distribution signal
    obv_divergent = False
    if "OBV" in hist.columns and len(hist) >= 20:
        try:
            obv_s = hist["OBV"].dropna()
            price_s = hist["Close"].tail(len(obv_s))
            if len(obv_s) >= 20:
                obv_slope = float(obv_s.iloc[-1] - obv_s.iloc[-20])
                price_slope = float(price_s.iloc[-1] - price_s.iloc[-20])
                if obv_slope > 0 and price_slope <= 0:
                    score += 1.0    # Hidden accumulation → bullish
                    obv_divergent = True
                elif obv_slope < 0 and price_slope >= 0:
                    score -= 1.0    # Hidden distribution → bearish
                    obv_divergent = True
        except Exception:
            pass

    # Stochastic confirmation — faster oscillator corroborating RSI zones
    if stoch_k is not None:
        if stoch_k < 20:
            score += 0.75
            if stoch_d is not None and stoch_k > stoch_d:
                score += 0.5    # Bullish Stoch crossover
        elif stoch_k > 80:
            score -= 0.75
            if stoch_d is not None and stoch_k < stoch_d:
                score -= 0.5    # Bearish Stoch crossover

    # Support / Resistance context
    sr = _compute_support_resistance(hist, current_price)
    if sr["at_support"]:
        score += 0.75
    if sr["at_resistance"]:
        score -= 0.75

    # Weekly RSI alignment — confirms daily signal on the higher timeframe
    weekly_rsi_val = _compute_weekly_rsi(hist)
    if weekly_rsi_val is not None:
        if weekly_rsi_val < 40 and rsi is not None and rsi <= rz_low + 10:
            score += 0.75   # Weekly and daily both oversold
        elif weekly_rsi_val > 60 and rsi is not None and rsi >= rz_high - 10:
            score -= 0.75   # Weekly and daily both overbought

    # Short interest amplifier
    # short_interest_pct arrives as a fraction from yfinance (e.g. 0.15 = 15%)
    if short_interest_pct is not None:
        si_pct = short_interest_pct * 100  # convert to percentage for threshold comparisons
        if si_pct > 15 and score > 0:
            score += 0.5    # High short float + buy = squeeze potential
        if si_pct > 20 and score < 0:
            score -= 0.3    # Institutional conviction on short side

    # News catalyst weight
    if recent_news_count >= 3 and score > 0:
        score += 0.5        # Catalyst confirmed
    elif recent_news_count == 0 and abs(score) > 1:
        score -= 0.25       # No catalyst reduces conviction

    # Fundamental quality modifier — prevents strong sell on high-quality companies
    # and boosts conviction when fundamentals + technicals align
    if fundamental_score >= 90:
        score = max(score, -1.0)         # Elite fundamentals: floor at SELL
        if analyst_upside_pct is not None and analyst_upside_pct > 20:
            score += 0.75                # Deep value + elite fundamentals
    elif fundamental_score >= 75:
        score = max(score, -1.5)         # Strong fundamentals: prevent STRONG SELL
        if analyst_upside_pct is not None and analyst_upside_pct > 15:
            score += 0.5
    elif fundamental_score >= 60:
        if analyst_upside_pct is not None and analyst_upside_pct > 25:
            score += 0.5                 # Significant analyst upside adds conviction

    if score >= 2.5:
        signal_str = "STRONG BUY"
    elif score >= 1.0:
        signal_str = "BUY"
    elif score <= -2.5:
        signal_str = "STRONG SELL"
    elif score <= -1.0:
        signal_str = "SELL"
    else:
        signal_str = "HOLD"

    # ATR-based stop loss (14-period average true range)
    atr: Optional[float] = None
    if len(hist) >= 14 and all(c in hist.columns for c in ("High", "Low", "Close")):
        try:
            tr = pd.concat([
                hist["High"] - hist["Low"],
                (hist["High"] - hist["Close"].shift(1)).abs(),
                (hist["Low"] - hist["Close"].shift(1)).abs(),
            ], axis=1).max(axis=1)
            atr = float(tr.tail(14).mean())
        except Exception:
            atr = None

    stop_distance = (atr * 1.5) if atr else (current_price * 0.07)

    if "BUY" in signal_str:
        stop_loss = round(current_price - stop_distance, 2)
        if atr:
            tp1 = round(current_price + 2.0 * atr, 2)
            tp2 = round(current_price + 3.5 * atr, 2)
            tp3 = round(current_price + 5.0 * atr, 2)
        else:
            tp1 = round(current_price * 1.08, 2)
            tp2 = round(current_price * 1.15, 2)
            tp3 = round(current_price * 1.25, 2)
    elif "SELL" in signal_str:
        stop_loss = round(current_price + stop_distance, 2)
        if atr:
            tp1 = round(current_price - 2.0 * atr, 2)
            tp2 = round(current_price - 3.5 * atr, 2)
            tp3 = round(current_price - 5.0 * atr, 2)
        else:
            tp1 = round(current_price * 0.92, 2)
            tp2 = round(current_price * 0.85, 2)
            tp3 = round(current_price * 0.75, 2)
    else:
        stop_loss = round(current_price - stop_distance, 2)
        if atr:
            tp1 = round(current_price + 1.5 * atr, 2)
            tp2 = round(current_price + 2.5 * atr, 2)
            tp3 = round(current_price + 4.0 * atr, 2)
        else:
            tp1 = round(current_price * 1.05, 2)
            tp2 = round(current_price * 1.10, 2)
            tp3 = round(current_price * 1.18, 2)

    # Confidence: normalize over expanded score range (-14..+14), then apply multipliers
    raw_conf = (score + 14) / 28 * 100
    raw_conf *= adx_factor      # ADX < 20 → choppy market penalty

    # Earnings proximity: reduce confidence when outcome is imminent/unknown
    earnings_ctx: Optional[str] = None
    if earnings_dates:
        try:
            today = pd.Timestamp.now().normalize()
            for ed in earnings_dates:
                ed_str = ed.date if hasattr(ed, "date") else (ed.get("date") if isinstance(ed, dict) else str(ed))
                ed_date = pd.Timestamp(str(ed_str))
                days = (ed_date - today).days
                if 0 <= days <= 5:
                    raw_conf *= 0.70
                    earnings_ctx = "IMMINENT"
                    break
                elif 6 <= days <= 14:
                    raw_conf *= 0.85
                    earnings_ctx = "UPCOMING"
                    break
        except Exception:
            pass

    confidence = int(min(100, max(0, raw_conf)))

    # Signal quality: count of independently confirmed factors
    quality_pts = 0
    if adx_val is not None and adx_val > 20:   quality_pts += 1  # trend present (≥20)
    if adx_val is not None and adx_val > 30:   quality_pts += 1  # strong trend bonus (≥30)
    if obv_divergent:                           quality_pts += 1
    if stoch_k is not None and ((stoch_k < 20 and score > 0) or (stoch_k > 80 and score < 0)): quality_pts += 1
    if sr.get("at_support") and score > 0:     quality_pts += 1
    if sr.get("at_resistance") and score < 0:  quality_pts += 1
    if weekly_rsi_val is not None and ((weekly_rsi_val < 40 and score > 0) or (weekly_rsi_val > 60 and score < 0)): quality_pts += 1
    if rp.get("at_zone"):                       quality_pts += 1
    if recent_news_count >= 2:                  quality_pts += 1  # catalyst present (≥2 articles)

    if quality_pts >= 5:
        signal_quality = "PRIME"
    elif quality_pts >= 3:
        signal_quality = "CONFIRMED"
    elif quality_pts >= 1:
        signal_quality = "STANDARD"
    else:
        signal_quality = "WEAK"

    # RSI signal label — uses stock-specific reversal thresholds
    if rsi is not None:
        if rsi <= rz_low: rsi_signal = "OVERSOLD"
        elif rsi >= rz_high: rsi_signal = "OVERBOUGHT"
        elif rsi <= rz_low + 5: rsi_signal = "MILDLY OVERSOLD"
        elif rsi >= rz_high - 5: rsi_signal = "MILDLY OVERBOUGHT"
        elif 40 <= rsi <= 60: rsi_signal = "NEUTRAL"
        else: rsi_signal = "NEUTRAL"
    else:
        rsi_signal = None

    # MACD signal label
    if macd_val is not None and macd_sig is not None:
        macd_label = "BULLISH" if macd_val > macd_sig else "BEARISH"
    else:
        macd_label = None

    # Trend strength from SMA alignment, gated by ADX to avoid false strong-trend labels
    smas_above = sum(1 for s in [sma_20, sma_50, sma_200] if s is not None and current_price > s)
    adx_strong = adx_val is not None and adx_val >= 25
    adx_trending = adx_val is None or adx_val >= 20  # None means unknown; don't penalise
    if smas_above == 3:
        trend_str = "STRONG UPTREND" if adx_strong else ("WEAK UPTREND" if not adx_trending else "UPTREND")
    elif smas_above == 2:
        trend_str = "UPTREND"
    elif smas_above == 1:
        trend_str = "MIXED"
    elif all(s is not None for s in [sma_20, sma_50, sma_200]):
        trend_str = "STRONG DOWNTREND" if adx_strong else ("WEAK DOWNTREND" if not adx_trending else "DOWNTREND")
    else:
        trend_str = "INSUFFICIENT DATA"

    # Risk/reward ratio to TP1
    risk = abs(current_price - stop_loss)
    reward = abs(tp1 - current_price)
    rr_ratio = round(reward / risk, 2) if risk > 0 else None

    # Optimal entry: prefer support/pullback for BUY, resistance/bounce for SELL
    sr_support = sr.get("nearest_support")
    sr_resistance = sr.get("nearest_resistance")
    if "BUY" in signal_str:
        if sr.get("at_resistance") and sr_support is not None and sr_support > stop_loss:
            optimal_entry = round(sr_support, 2)
        elif rsi is not None and rsi >= rz_high and atr is not None:
            optimal_entry = round(max(current_price - 0.5 * atr, stop_loss + 0.01), 2)
        else:
            optimal_entry = round(current_price, 2)
    elif "SELL" in signal_str:
        if sr.get("at_support") and sr_resistance is not None and sr_resistance < stop_loss:
            optimal_entry = round(sr_resistance, 2)
        elif rsi is not None and rsi <= rz_low and atr is not None:
            optimal_entry = round(current_price + 0.5 * atr, 2)
        else:
            optimal_entry = round(current_price, 2)
    else:
        optimal_entry = round(current_price, 2)

    return TradingSignals(
        signal=signal_str,
        confidence=confidence,
        optimal_entry=optimal_entry,
        stop_loss=stop_loss,
        tp1=tp1,
        tp2=tp2,
        tp3=tp3,
        rsi_value=round(rsi, 1) if rsi is not None else None,
        rsi_signal=rsi_signal,
        macd_signal=macd_label,
        trend_strength=trend_str,
        risk_reward=rr_ratio,
        rsi_reversal_zone_low=rp["zone_low"],
        rsi_reversal_zone_high=rp["zone_high"],
        rsi_bullish_reversals=rp["bullish_reversals"],
        rsi_bearish_reversals=rp["bearish_reversals"],
        rsi_at_reversal_zone=rp["at_zone"],
        rsi_reversal_signal=rp["reversal_signal"],
        adx=round(adx_val, 1) if adx_val is not None else None,
        weekly_rsi=weekly_rsi_val,
        sr_nearest_support=sr.get("nearest_support"),
        sr_nearest_resistance=sr.get("nearest_resistance"),
        sr_at_support=sr.get("at_support"),
        sr_at_resistance=sr.get("at_resistance"),
        earnings_proximity=earnings_ctx,
        signal_quality=signal_quality,
    )


def _analyze_ticker(ticker: str, period: str) -> FullStockAnalysis:
    analyzer = StockAnalyzer()
    data = analyzer.get_stock_data(ticker, period)

    if not data or "error" in data:
        return FullStockAnalysis(ticker=ticker, error=data.get("error", "fetch_failed") if data else "fetch_failed")

    info = data.get("info", {})
    hist = data.get("history")

    raw_metrics = analyzer.get_key_metrics(data)
    raw_score = analyzer.calculate_score(data)

    hist_with_indicators = None
    if hist is not None and len(hist) >= 50:
        hist_with_indicators = analyzer.calculate_technical_indicators(hist.copy())

    raw_forecast = None
    if raw_metrics and raw_score:
        raw_forecast = analyzer.calculate_forecast(data, raw_metrics, raw_score)

    try:
        raw_news = NewsMarketData().get_stock_news(ticker)
    except Exception:
        raw_news = []

    try:
        raw_analyst = RatingsAggregator().get_yahoo_ratings(ticker)
    except Exception:
        raw_analyst = None

    short_interest = ShortInterestData(
        short_ratio=_safe_float(info.get("shortRatio")),
        short_pct_float=_safe_float(info.get("shortPercentOfFloat")),
        shares_short=_safe_int(info.get("sharesShort")),
        insider_own_pct=_safe_float(info.get("heldPercentInsiders")),
        institution_own_pct=_safe_float(info.get("heldPercentInstitutions")),
    )

    earnings_dates = []
    try:
        t_obj = yf.Ticker(ticker)
        ed = t_obj.earnings_dates
        if ed is not None and not ed.empty:
            for date_idx, row in ed.head(8).iterrows():
                eps_est = _safe_float(row.get("EPS Estimate"))
                eps_act = _safe_float(row.get("Reported EPS"))
                surp = _safe_float(row.get("Surprise(%)"))
                beat = None
                if eps_act is not None and eps_est is not None:
                    beat = eps_act >= eps_est
                earnings_dates.append(EarningsDate(
                    date=date_idx.strftime("%Y-%m-%d") if hasattr(date_idx, "strftime") else str(date_idx)[:10],
                    eps_estimate=eps_est,
                    eps_actual=eps_act,
                    surprise_pct=surp,
                    beat=beat,
                ))
    except Exception as e:
        logger.debug("Earnings dates failed for %s: %s", ticker, e)

    risk_profile: Optional[RiskProfileData] = None
    try:
        if hist is not None and len(hist) >= 60:
            ra = RiskAnalyzer()
            r = ra.comprehensive_risk_analysis(hist["Close"])
            risk_profile = RiskProfileData(
                volatility=round(float(r["volatility"]), 1) if r.get("volatility") is not None else None,
                var_5pct=round(abs(float(r["var_5pct"])) * 100, 2) if r.get("var_5pct") is not None else None,
                sharpe_ratio=round(float(r["sharpe_ratio"]), 2) if r.get("sharpe_ratio") is not None else None,
                sortino_ratio=round(float(r["sortino_ratio"]), 2) if r.get("sortino_ratio") is not None else None,
                max_drawdown_pct=round(abs(float(r["max_drawdown_pct"])), 1) if r.get("max_drawdown_pct") is not None else None,
            )
    except Exception as e:
        logger.debug("Risk profile failed for %s: %s", ticker, e)

    relative_strength_list: list[Optional[float]] = []
    try:
        spy_hist = yf.Ticker("SPY").history(period=period)
        if spy_hist is not None and not spy_hist.empty and hist is not None and len(hist) > 5:
            hist_close = hist["Close"].rename("stock")
            spy_close = spy_hist["Close"].rename("spy")
            hist_close.index = hist_close.index.tz_localize(None) if hist_close.index.tzinfo else hist_close.index
            spy_close.index = spy_close.index.tz_localize(None) if spy_close.index.tzinfo else spy_close.index
            combined = pd.concat([hist_close, spy_close], axis=1).dropna()
            if len(combined) > 5:
                stock_norm = combined["stock"] / combined["stock"].iloc[0] * 100
                spy_norm = combined["spy"] / combined["spy"].iloc[0] * 100
                rs = stock_norm / spy_norm
                hist_index_normalized = hist.index.tz_localize(None) if hist.index.tzinfo else hist.index
                rs_full = rs.reindex(hist_index_normalized)
                relative_strength_list = [None if pd.isna(v) else round(float(v), 4) for v in rs_full.tail(252)]
    except Exception as e:
        logger.debug("Relative strength failed for %s: %s", ticker, e)

    valuation_tunnel = None
    try:
        if hist is not None and len(hist) >= 30:
            h = hist.tail(252)
            tun = build_valuation_tunnel(
                closes=[float(c) for c in h["Close"].tolist()],
                dates=[
                    idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]
                    for idx in h.index
                ],
                target_price=raw_metrics.get("Target Price") if raw_metrics else None,
            )
            if tun:
                valuation_tunnel = ValuationTunnel(**tun)
    except Exception as e:
        logger.debug("Valuation tunnel failed for %s: %s", ticker, e)

    trading_signals_obj = _compute_trading_signals(
        hist_with_indicators if hist_with_indicators is not None else hist,
        raw_metrics.get("Current Price") if raw_metrics else None,
        earnings_dates=earnings_dates,
        short_interest_pct=short_interest.short_pct_float,
        recent_news_count=len(raw_news),
        fundamental_score=int(raw_score.get("total_score", 0)) if raw_score else 0,
        analyst_upside_pct=_safe_float(
            ((raw_analyst.get("target_price") or 0) - (raw_metrics.get("Current Price") or 0))
            / (raw_metrics.get("Current Price") or 1) * 100
        ) if raw_analyst and raw_metrics else None,
    ) if raw_metrics and raw_metrics.get("Current Price") else TradingSignals()

    decision = None
    try:
        sig = trading_signals_obj.model_dump()
        cur = raw_metrics.get("Current Price") if raw_metrics else None
        cur_vs_fair = None
        if valuation_tunnel is not None and cur:
            mids = [m for m in valuation_tunnel.hist_mid if m is not None]
            if mids:
                cur_vs_fair = (cur / mids[-1] - 1.0) * 100.0
        tunnel_in = {"current_vs_fair_pct": cur_vs_fair} if cur_vs_fair is not None else None
        regime_in = get_market_regime_cached()
        q_score = int(raw_score["total_score"]) if raw_score and raw_score.get("total_score") is not None else None
        quality = Quality(score=q_score, grade=quality_grade(q_score))

        table = _calibration_table()
        cal_horizons = (table or {}).get("horizons", {})
        as_of = (table or {}).get("generated_at")

        horizons = {}
        for hkey, prof in HORIZON_PROFILES.items():
            sr = compute_conviction(score=None, signals=sig, forecast=raw_forecast,
                                    tunnel=tunnel_in, regime=regime_in, weights=prof["weights"])
            ch = cal_horizons.get(hkey) or {}
            pct = band = hit = avg = n = low = None
            win = prof["window"]
            if ch.get("conviction_percentiles"):
                pct = percentile_of(ch["conviction_percentiles"], sr["conviction"])
                band = band_for(pct)
                win = ch.get("horizon_days", prof["window"])
                b = cal_lookup(ch.get("buckets", []), sr["conviction"])
                if b and b.get("n"):
                    hit, avg, n = b["hit_rate"], b["avg_forward_return"], b["n"]
                    low = b["n"] < 100
            setup = Setup(
                score=sr["conviction"], direction=sr["direction"],
                percentile=pct, band=band, hit_rate=hit, avg_forward_return=avg, n=n,
                low_sample=low, as_of=as_of, horizon_days=win,
                expected_value_r=sr["expected_value_r"],
                factors=[f for f in sr["factors"] if f["label"] != "Fundamentals"],
                regime=sr["regime"],
            )
            horizons[hkey] = HorizonDecision(
                action=decide_action(quality.grade, band, sr["direction"], hkey),
                read=read_line(quality.grade, band, sr["direction"], hkey),
                setup=setup,
            )
        decision = Decision(quality=quality, default_horizon="swing", horizons=horizons)
    except Exception as e:
        logger.debug("Decision build failed for %s: %s", ticker, e)
        decision = None

    return FullStockAnalysis(
        ticker=ticker,
        company_name=info.get("longName") or info.get("shortName"),
        sector=info.get("sector"),
        industry=info.get("industry"),
        description=info.get("longBusinessSummary"),
        ohlcv=hist_to_ohlcv(hist) if hist is not None and len(hist) > 0 else [],
        metrics=_build_metrics(raw_metrics) if raw_metrics else None,
        score=_build_score(raw_score) if raw_score else None,
        forecast=_build_forecast(raw_forecast),
        indicators=_build_indicators(hist_with_indicators) if hist_with_indicators is not None else None,
        valuation_tunnel=valuation_tunnel,
        decision=decision,
        trading_signals=trading_signals_obj,
        risk_profile=risk_profile,
        news=_build_news(raw_news),
        analyst_rating=_build_analyst(raw_analyst),
        short_interest=short_interest,
        earnings_dates=earnings_dates,
        relative_strength=relative_strength_list,
        analyst_target_age_days=_analyst_target_age(info),
        data_source=data.get('data_source'),
        cached_at=data.get('cached_at'),
        is_stale=bool(data.get('is_stale', False)),
    )


@router.post("/analyze", response_model=FullStockAnalysis)
async def analyze(body: AnalyzeRequest, _: str = Depends(verify_token)):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _analyze_ticker, body.ticker, body.period)


@router.post("/batch", response_model=BatchAnalysisResponse)
async def batch(body: BatchRequest, _: str = Depends(verify_token)):
    loop = asyncio.get_event_loop()
    results = []
    failed = []

    async def _fetch_one(ticker: str) -> FullStockAnalysis:
        return await loop.run_in_executor(None, _analyze_ticker, ticker, body.period)

    tasks = [_fetch_one(t) for t in body.tickers]
    outcomes = await asyncio.gather(*tasks, return_exceptions=True)

    for ticker, outcome in zip(body.tickers, outcomes):
        if isinstance(outcome, Exception):
            logger.error("Batch fetch failed for %s: %s", ticker, outcome)
            failed.append(ticker)
            results.append(FullStockAnalysis(ticker=ticker, error=str(outcome)))
        else:
            if outcome.error:
                failed.append(ticker)
            results.append(outcome)

    return BatchAnalysisResponse(results=results, total=len(results), failed=failed)


@router.get("/stocks/{ticker}/verdict", response_model=VerdictResponse)
async def get_verdict(ticker: str, period: str = "1y", horizon: str = "swing", _: str = Depends(verify_token)):
    loop = asyncio.get_event_loop()
    analysis = await loop.run_in_executor(None, _analyze_ticker, ticker.upper(), period)
    if analysis.error:
        raise HTTPException(status_code=404, detail=analysis.error)
    return _compute_verdict(analysis, time_horizon=horizon)
