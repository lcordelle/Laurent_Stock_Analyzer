from __future__ import annotations
import asyncio
import logging
import time
import numpy as np
import pandas as pd
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from api.auth import verify_token
from api.models.requests import AnalyzeRequest, BatchRequest
import yfinance as yf
from api.models.responses import (
    FullStockAnalysis, BatchAnalysisResponse,
    StockMetrics, ScoreBreakdown, ForecastResult,
    IndicatorData, TradingSignals, NewsArticle, AnalystRating, OHLCVRow,
    ShortInterestData, EarningsDate, RiskProfileData,
)
from utils.risk_analysis import RiskAnalyzer
from utils.stock_analyzer import StockAnalyzer
from utils.news_market import NewsMarketData
from utils.ratings_aggregator import RatingsAggregator

router = APIRouter(tags=["stocks"])


class VerdictSignalDetail(BaseModel):
    label: str
    score: int
    weight: float


class VerdictResponse(BaseModel):
    verdict: str
    confidence: int
    vf_score: int
    signals: dict[str, VerdictSignalDetail]
    price_target: Optional[float] = None
    stop_loss: Optional[float] = None
    why: str
logger = logging.getLogger(__name__)


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
        rows.append(OHLCVRow(
            date=idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx),
            open=float(row["Open"]) if pd.notna(row.get("Open")) else 0.0,
            high=float(row["High"]) if pd.notna(row.get("High")) else 0.0,
            low=float(row["Low"]) if pd.notna(row.get("Low")) else 0.0,
            close=float(row["Close"]) if pd.notna(row.get("Close")) else 0.0,
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
    if short_interest_pct is not None:
        if short_interest_pct > 15 and score > 0:
            score += 0.5    # High short float + buy = squeeze potential
        elif short_interest_pct > 20 and score < 0:
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
    if stoch_k is not None and ((stoch_k < 25 and score > 0) or (stoch_k > 75 and score < 0)): quality_pts += 1
    if sr.get("at_support") and score > 0:     quality_pts += 1
    if sr.get("at_resistance") and score < 0:  quality_pts += 1
    if weekly_rsi_val is not None and ((weekly_rsi_val < 45 and score > 0) or (weekly_rsi_val > 55 and score < 0)): quality_pts += 1
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
        elif rsi <= rz_low + 8: rsi_signal = "MILDLY OVERSOLD"
        elif rsi >= rz_high - 8: rsi_signal = "MILDLY OVERBOUGHT"
        elif 40 <= rsi <= 60: rsi_signal = "NEUTRAL"
        else: rsi_signal = "NEUTRAL"
    else:
        rsi_signal = None

    # MACD signal label
    if macd_val is not None and macd_sig is not None:
        macd_label = "BULLISH" if macd_val > macd_sig else "BEARISH"
    else:
        macd_label = None

    # Trend strength from SMA alignment
    smas_above = sum(1 for s in [sma_20, sma_50, sma_200] if s is not None and current_price > s)
    if smas_above == 3: trend_str = "STRONG UPTREND"
    elif smas_above == 2: trend_str = "UPTREND"
    elif smas_above == 1: trend_str = "MIXED"
    elif all(s is not None for s in [sma_20, sma_50, sma_200]): trend_str = "DOWNTREND"
    else: trend_str = "INSUFFICIENT DATA"

    # Risk/reward ratio to TP1
    risk = abs(current_price - stop_loss)
    reward = abs(tp1 - current_price)
    rr_ratio = round(reward / risk, 2) if risk > 0 else None

    return TradingSignals(
        signal=signal_str,
        confidence=confidence,
        optimal_entry=round(current_price, 2),
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
        trading_signals=_compute_trading_signals(
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
        ) if raw_metrics and raw_metrics.get("Current Price") else TradingSignals(),
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


_NEWS_BULLISH_STRONG = {
    "beats", "exceeds", "record", "upgrade", "raises guidance",
    "outperforms", "strong growth", "buyback", "dividend increase", "partnership",
}
_NEWS_BULLISH_MILD = {"positive", "advances", "gains", "momentum", "recovery"}
_NEWS_BEARISH_STRONG = {
    "misses", "downgrade", "cuts guidance", "disappoints",
    "investigation", "fraud", "lawsuit", "bankruptcy", "layoffs", "recall",
}
_NEWS_BEARISH_MILD = {"decline", "falls", "concern", "weak", "slowdown", "loss"}


def _score_news_sentiment(news: list) -> tuple[int, str]:
    """Keyword-based news sentiment scorer. Returns (score 0-100, label).
    Upgrade path: swap internals only — caller signature is stable."""
    from datetime import datetime, timezone

    def _recency_weight(published) -> float:
        if not published:
            return 0.5
        try:
            pub_str = str(published)[:19]
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                try:
                    pub = datetime.strptime(pub_str, fmt)
                    age_h = (datetime.now(timezone.utc).replace(tzinfo=None) - pub).total_seconds() / 3600
                    if age_h <= 24:   return 3.0
                    if age_h <= 72:   return 1.5
                    if age_h <= 168:  return 0.5
                    return 0.0
                except ValueError:
                    continue
        except Exception:
            pass
        return 0.5

    def _score_text(text: str) -> float:
        t = text.lower()
        s = 0.0
        for kw in _NEWS_BULLISH_STRONG:
            if kw in t: s += 2
        for kw in _NEWS_BULLISH_MILD:
            if kw in t: s += 1
        for kw in _NEWS_BEARISH_STRONG:
            if kw in t: s -= 2
        for kw in _NEWS_BEARISH_MILD:
            if kw in t: s -= 1
        return max(-10.0, min(10.0, s))

    weighted_sum = 0.0
    total_weight = 0.0
    for article in news:
        w = _recency_weight(article.published)
        if w == 0.0:
            continue
        text = f"{article.title or ''} {article.summary or ''}"
        weighted_sum += _score_text(text) * w
        total_weight += w

    if total_weight == 0.0:
        return 50, "No Recent News"

    raw = weighted_sum / total_weight
    score = int(max(0, min(100, 50 + raw * 5)))
    if score >= 75:   label = "Positive"
    elif score >= 60: label = "Mildly Positive"
    elif score >= 40: label = "Neutral"
    elif score >= 25: label = "Mildly Negative"
    else:             label = "Negative"
    return score, label


def _score_earnings_quality(earnings_dates: list) -> tuple[int, str]:
    """Score based on last 4 EPS beat/miss results. Returns (score 0-100, label)."""
    with_beat = [e for e in earnings_dates if e.beat is not None]
    recent = sorted(with_beat, key=lambda e: e.date, reverse=True)[:4]

    if len(recent) < 2:
        return 50, "Insufficient Data"

    score = 50
    for e in recent:
        score += 20 if e.beat else -20
    beat_count = sum(1 for e in recent if e.beat)
    if beat_count == 4:              score += 10
    elif beat_count == len(recent):  score += 5

    score = max(0, min(100, score))
    if score >= 80:   label = "Consistent Beats"
    elif score >= 60: label = "Mostly Beats"
    elif score >= 40: label = "Mixed"
    else:             label = "Missing Estimates"
    return score, label


def _compute_verdict(analysis: FullStockAnalysis) -> VerdictResponse:
    sig   = analysis.trading_signals
    score = analysis.score
    fct   = analysis.forecast
    rat   = analysis.analyst_rating
    rsk   = analysis.risk_profile
    m     = analysis.metrics
    si    = analysis.short_interest
    price = m.current_price if m else None

    # ── Technical (20%) ──────────────────────────────────────────────────────
    tech_score = sig.confidence if sig and sig.confidence is not None else 50
    if sig:
        if sig.rsi_value is not None:
            if sig.rsi_value < 35:   tech_score = min(100, tech_score + 10)
            elif sig.rsi_value > 70: tech_score = max(0,   tech_score - 10)
        if sig.macd_signal:
            ms = sig.macd_signal.lower()
            if ms == "bullish":   tech_score = min(100, tech_score + 5)
            elif ms == "bearish": tech_score = max(0,   tech_score - 5)
        if sig.adx and sig.adx > 25:
            tech_score = min(100, int(tech_score * 1.1))
        if sig.sr_at_support:    tech_score = min(100, tech_score + 8)
        if sig.sr_at_resistance: tech_score = max(0,   tech_score - 8)
        if sig.signal_quality == "LOW":
            tech_score = min(65, tech_score)
    tech_label = (
        "Strong Bullish" if "STRONG BUY"  in (sig.signal or "") else
        "Strong Bearish" if "STRONG SELL" in (sig.signal or "") else
        "Bullish"        if "BUY"         in (sig.signal or "") else
        "Bearish"        if "SELL"        in (sig.signal or "") else
        "Neutral"
    )

    # ── Fundamental (20%) ────────────────────────────────────────────────────
    if score and score.components:
        c = score.components
        gross_n  = c.get("Gross Margin", 0) / 25 * 100
        roe_n    = c.get("ROE",          0) / 20 * 100
        fcf_n    = c.get("FCF Margin",   0) / 20 * 100
        val_n    = c.get("Valuation",    0) / 20 * 100
        growth_n = c.get("Growth",       0) / 15 * 100
        fund_score = int(
            gross_n  * 0.30 +
            roe_n    * 0.25 +
            fcf_n    * 0.25 +
            val_n    * 0.10 +
            growth_n * 0.10
        )
        fund_score = max(0, min(100, fund_score))
    elif score:
        fund_score = score.total
    else:
        fund_score = 50
    if m and m.debt_to_equity is not None:
        if m.debt_to_equity < 0.5:  fund_score = min(100, fund_score + 5)
        elif m.debt_to_equity > 2.0: fund_score = max(0,  fund_score - 10)
    if si and si.insider_own_pct is not None and si.insider_own_pct > 10:
        fund_score = min(100, fund_score + 5)
    fund_label = (
        "Exceptional" if fund_score >= 80 else
        "Strong"      if fund_score >= 65 else
        "Moderate"    if fund_score >= 50 else
        "Weak"
    )

    # ── AI Outlook (20%) ─────────────────────────────────────────────────────
    if fct and fct.probability is not None and fct.forecast_change_pct is not None:
        if fct.forecast_change_pct > 0:
            ai_score = int(min(100, 50 + fct.probability * 50))
        else:
            ai_score = int(max(0, 50 - fct.probability * 50))
    else:
        ai_score = 50
    ai_label = (
        "Bullish" if ai_score >= 65 else
        "Neutral" if ai_score >= 45 else
        "Bearish"
    )

    # ── Analyst (10%) ────────────────────────────────────────────────────────
    if rat and rat.mean is not None:
        analyst_score = int(max(0, min(100, (5 - rat.mean) / 4 * 100)))
        if rat.target_mean is not None and price and price > 0:
            upside = (rat.target_mean - price) / price * 100
            if upside > 20:   analyst_score = min(100, analyst_score + 10)
            elif upside > 10: analyst_score = min(100, analyst_score + 5)
    else:
        analyst_score = 50
    analyst_label = (
        "Strong Buy" if analyst_score >= 80 else
        "Buy"        if analyst_score >= 60 else
        "Hold"       if analyst_score >= 40 else
        "Sell"
    )

    # ── Momentum (10%) ───────────────────────────────────────────────────────
    trend = sig.trend_strength if sig else None
    momentum_score = (
        85 if trend == "STRONG UPTREND" else
        70 if trend == "UPTREND"        else
        50 if trend == "MIXED"          else
        30 if trend == "DOWNTREND"      else
        50
    )
    if m and m.current_price and m.fifty_two_week_high and m.fifty_two_week_low:
        w_range = m.fifty_two_week_high - m.fifty_two_week_low
        if w_range > 0:
            pos = (m.current_price - m.fifty_two_week_low) / w_range
            if pos >= 0.9:   momentum_score = min(100, momentum_score + 10)
            elif pos <= 0.1: momentum_score = max(0,   momentum_score - 5)
    rs = analysis.relative_strength
    if rs:
        last_rs = next((v for v in reversed(rs) if v is not None), None)
        if last_rs is not None:
            if last_rs > 0: momentum_score = min(100, momentum_score + 5)
            elif last_rs < 0: momentum_score = max(0, momentum_score - 5)
    momentum_label = (
        "Strong Uptrend" if momentum_score >= 80 else
        "Uptrend"        if momentum_score >= 65 else
        "Neutral"        if momentum_score >= 45 else
        "Downtrend"
    )

    # ── News & Sentiment (10%) ───────────────────────────────────────────────
    news_score, news_label = _score_news_sentiment(analysis.news)

    # ── Earnings Quality (5%) ────────────────────────────────────────────────
    eq_score, eq_label = _score_earnings_quality(analysis.earnings_dates)

    # ── Risk (5%) ────────────────────────────────────────────────────────────
    if rsk and rsk.sharpe_ratio is not None:
        risk_score = (
            80 if rsk.sharpe_ratio >= 1.0 else
            65 if rsk.sharpe_ratio >= 0.5 else
            45 if rsk.sharpe_ratio >= 0.0 else
            25
        )
    elif rsk and rsk.volatility is not None:
        risk_score = int(max(0, min(100, 100 - rsk.volatility)))
    else:
        risk_score = 50
    if si and si.short_pct_float is not None and si.short_pct_float > 20:
        risk_score = max(0, risk_score - 15)
    if m and m.beta is not None:
        if m.beta > 2.0:   risk_score = max(0,   risk_score - 10)
        elif m.beta < 0.5: risk_score = min(100, risk_score + 5)
    risk_label = (
        "Low Risk"      if risk_score >= 70 else
        "Moderate Risk" if risk_score >= 45 else
        "High Risk"
    )

    # ── Weighted composite ───────────────────────────────────────────────────
    weights = {
        "technical": 0.20, "fundamental": 0.20, "ai_outlook": 0.20,
        "analyst": 0.10, "momentum": 0.10, "news_sentiment": 0.10,
        "earnings_quality": 0.05, "risk": 0.05,
    }
    scores_map = {
        "technical": tech_score, "fundamental": fund_score, "ai_outlook": ai_score,
        "analyst": analyst_score, "momentum": momentum_score,
        "news_sentiment": news_score, "earnings_quality": eq_score, "risk": risk_score,
    }
    composite = sum(scores_map[k] * w for k, w in weights.items())

    verdict = (
        "STRONG BUY"  if composite >= 75 else
        "BUY"         if composite >= 60 else
        "HOLD"        if composite >= 45 else
        "SELL"        if composite >= 30 else
        "STRONG SELL"
    )

    confidence = int(round(composite))

    # ── Price target + stop loss ─────────────────────────────────────────────
    price_target = None
    if rat and rat.target_mean:
        price_target = round(rat.target_mean, 2)
    elif sig and sig.tp1:
        price_target = sig.tp1

    stop_loss = round(sig.stop_loss, 2) if sig and sig.stop_loss else None

    # ── Why text ─────────────────────────────────────────────────────────────
    facts = []
    if sig and sig.rsi_value is not None:
        if sig.rsi_value < 35:
            facts.append(f"RSI {sig.rsi_value:.0f} (oversold)")
        elif sig.rsi_value > 70:
            facts.append(f"RSI {sig.rsi_value:.0f} (overbought)")

    beats_with_data = [e for e in analysis.earnings_dates if e.beat is not None]
    recent_beats = sorted(beats_with_data, key=lambda e: e.date, reverse=True)[:4]
    if len(recent_beats) >= 3:
        beat_count = sum(1 for e in recent_beats if e.beat)
        facts.append(f"{beat_count}/{len(recent_beats)} earnings beats")

    if news_score >= 70:
        facts.append("positive news flow")
    elif news_score <= 30:
        facts.append("negative news flow")

    if rat and rat.target_mean is not None and price and price > 0:
        upside = (rat.target_mean - price) / price * 100
        if upside > 15:
            facts.append(f"{upside:.0f}% analyst upside")

    if composite >= 60:
        tail = "constructive risk/reward"
    elif composite >= 45:
        tail = "monitor for catalyst"
    else:
        tail = "risk management priority"

    if facts:
        why = f"{', '.join(facts)} — {tail}"
    elif composite >= 60:
        why = "Multiple signals confirm bullish bias — monitor for optimal entry"
    elif composite >= 45:
        why = "Mixed signals — wait for a clearer technical or fundamental catalyst"
    else:
        why = "Bearish signal convergence across multiple dimensions — risk management priority"

    return VerdictResponse(
        verdict=verdict,
        confidence=confidence,
        vf_score=int(round(composite)),
        signals={
            "technical":        VerdictSignalDetail(label=tech_label,      score=tech_score,     weight=0.20),
            "fundamental":      VerdictSignalDetail(label=fund_label,      score=fund_score,     weight=0.20),
            "ai_outlook":       VerdictSignalDetail(label=ai_label,        score=ai_score,       weight=0.20),
            "analyst":          VerdictSignalDetail(label=analyst_label,   score=analyst_score,  weight=0.10),
            "momentum":         VerdictSignalDetail(label=momentum_label,  score=momentum_score, weight=0.10),
            "news_sentiment":   VerdictSignalDetail(label=news_label,      score=news_score,     weight=0.10),
            "earnings_quality": VerdictSignalDetail(label=eq_label,        score=eq_score,       weight=0.05),
            "risk":             VerdictSignalDetail(label=risk_label,      score=risk_score,     weight=0.05),
        },
        price_target=price_target,
        stop_loss=stop_loss,
        why=why,
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
async def get_verdict(ticker: str, period: str = "1y", _: str = Depends(verify_token)):
    loop = asyncio.get_event_loop()
    analysis = await loop.run_in_executor(None, _analyze_ticker, ticker.upper(), period)
    if analysis.error:
        raise HTTPException(status_code=404, detail=analysis.error)
    return _compute_verdict(analysis)
