from __future__ import annotations
import math
import os
from api.models.responses import FullStockAnalysis, VerdictSignalDetail, VerdictResponse


def _clean(v: float | None) -> float | None:
    """Return None for NaN/inf — keeps JSON serialisation clean."""
    if v is None:
        return None
    try:
        f = float(v)
        return None if (not math.isfinite(f)) else f
    except (TypeError, ValueError):
        return None

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

# ── Time-horizon signal weights ───────────────────────────────────────────────
# Each row sums to 1.0. Scalp leans on technical/momentum; long-term on fundamentals.
_HORIZON_WEIGHTS: dict[str, dict[str, float]] = {
    "scalp": {
        "technical": 0.40, "momentum": 0.25, "news_sentiment": 0.15,
        "ai_outlook": 0.10, "fundamental": 0.05, "analyst": 0.02,
        "earnings_quality": 0.02, "risk": 0.01,
    },
    "swing": {
        "technical": 0.20, "fundamental": 0.20, "ai_outlook": 0.20,
        "analyst": 0.10, "momentum": 0.10, "news_sentiment": 0.10,
        "earnings_quality": 0.05, "risk": 0.05,
    },
    "position": {
        "technical": 0.15, "fundamental": 0.25, "ai_outlook": 0.20,
        "analyst": 0.15, "momentum": 0.10, "news_sentiment": 0.05,
        "earnings_quality": 0.05, "risk": 0.05,
    },
    "longterm": {
        "technical": 0.08, "fundamental": 0.32, "ai_outlook": 0.22,
        "analyst": 0.15, "momentum": 0.05, "news_sentiment": 0.03,
        "earnings_quality": 0.10, "risk": 0.05,
    },
}


def _score_news_sentiment(news: list) -> tuple[int, str]:
    """Keyword news scorer with optional LLM upgrade (env-gated).
    Upgrade path: swap internals only — caller signature is stable."""
    from datetime import datetime, timezone

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if anthropic_key and news:
        try:
            return _score_news_llm(news)
        except Exception:
            pass  # fall through to keyword scorer

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


def _score_news_llm(news: list) -> tuple[int, str]:
    """Claude Haiku sentiment — batches top 5 headlines for one API call."""
    import anthropic
    headlines = []
    for a in news[:5]:
        title = (a.title or "").strip()
        if title:
            headlines.append(title)
    if not headlines:
        return 50, "No Recent News"

    client = anthropic.Anthropic()
    prompt = (
        "Rate the overall stock news sentiment for these headlines (1-10 scale, "
        "10=very bullish, 5=neutral, 1=very bearish). Respond with JSON only: "
        "{\"score\": <1-10>, \"label\": \"<Positive|Mildly Positive|Neutral|Mildly Negative|Negative>\", "
        "\"reason\": \"<one sentence>\"}\n\nHeadlines:\n" +
        "\n".join(f"- {h}" for h in headlines)
    )
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=128,
        messages=[{"role": "user", "content": prompt}],
    )
    import json
    raw_text = msg.content[0].text.strip()
    # strip markdown code fences if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    data = json.loads(raw_text)
    llm_score = int(data.get("score", 5))
    label = data.get("label", "Neutral")
    score = int(max(0, min(100, (llm_score - 1) / 9 * 100)))
    return score, label


def _score_earnings_quality(earnings_dates: list) -> tuple[int, str]:
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


def _entry_timing(
    sig, price: float | None, composite: float, earnings_proximity: str | None
) -> tuple[str, list[float] | None]:
    """Returns (timing_label, [zone_low, zone_high] | None)."""
    if earnings_proximity in ("IMMINENT",):
        return "WAIT POST-EARNINGS", None

    if composite < 45:
        return "DO NOT ENTER", None

    if sig is None or price is None:
        return "EVALUATE", None

    rsi = sig.rsi_value
    at_support = sig.sr_at_support
    at_resistance = sig.sr_at_resistance
    support = sig.sr_nearest_support
    resistance = sig.sr_nearest_resistance

    # Overbought near resistance → wait
    if rsi is not None and rsi > 68 and at_resistance:
        if support and support > 0:
            zone_low = round(support * 0.99, 2)
            zone_high = round(support * 1.01, 2)
            return f"WAIT — pullback to ${support:.2f}", [zone_low, zone_high]
        return "WAIT — overbought at resistance", None

    # Ideal: oversold / at support with bullish composite
    if at_support and composite >= 60:
        if support and support > 0:
            zone_low = round(support * 0.995, 2)
            zone_high = round(price * 1.005, 2)
            return "ENTER NOW — at support", [zone_low, zone_high]
        return "ENTER NOW", None

    # Near support but not confirmed
    if support and price and (price - support) / price < 0.02 and composite >= 55:
        zone_low = round(support * 0.99, 2)
        zone_high = round(price * 1.01, 2)
        return "ENTER — near support", [zone_low, zone_high]

    if composite >= 65:
        return "ENTER NOW", None

    if composite >= 55:
        return "SCALE IN — partial position", None

    return "MONITOR — wait for confirmation", None


def _position_size(
    composite: float,
    price: float | None,
    stop_loss: float | None,
    volatility: float | None,
) -> tuple[float | None, float | None]:
    """Kelly-inspired sizing. Returns (suggested_pct, max_pct)."""
    if price is None or price <= 0:
        return None, None

    # Win probability from composite (linear mapping: 45→0.45, 75→0.65)
    win_prob = max(0.0, min(0.9, (composite - 10) / 100))

    # Risk per trade from stop loss or volatility
    if stop_loss and price > 0 and stop_loss < price:
        risk_pct = (price - stop_loss) / price
    elif volatility and volatility > 0:
        risk_pct = min(0.20, volatility / 100 * 1.5)
    else:
        risk_pct = 0.08  # default 8% risk per position

    # Kelly fraction: f = (p * b - q) / b where b = reward/risk ≈ 2
    reward_risk = 2.0
    q = 1 - win_prob
    kelly = (win_prob * reward_risk - q) / reward_risk
    kelly = max(0.0, kelly)

    # Half-Kelly is standard practice to reduce variance
    half_kelly = kelly * 0.5

    # Convert to portfolio % with position risk constraint
    if risk_pct > 0:
        position_pct = min(half_kelly, 0.02 / risk_pct)  # risk 2% of portfolio max
    else:
        position_pct = half_kelly

    suggested = round(min(position_pct * 100, 10.0), 1)  # cap at 10%
    max_pos = round(min(suggested * 1.5, 12.0), 1)
    return suggested if suggested >= 0.5 else None, max_pos if max_pos >= 0.5 else None


def _price_target_range(
    rat, sig, price: float | None
) -> tuple[float | None, float | None, float | None]:
    """Returns (bear, base, bull) price targets. NaN/inf values are dropped."""
    base = None
    bear = None
    bull = None

    if rat:
        base = _clean(rat.target_mean)
        if base:
            base = round(base, 2)
        bear_raw = _clean(rat.target_low)
        if bear_raw:
            bear = round(bear_raw, 2)
        bull_raw = _clean(rat.target_high)
        if bull_raw:
            bull = round(bull_raw, 2)

    # Derive missing endpoints from base if we have price
    if base and price and price > 0:
        if bear is None:
            bear = round(price * 0.88, 2)  # -12% floor
        if bull is None:
            bull = round(base * 1.25, 2)

    # Fallback: use technical TPs
    if base is None and sig:
        if sig.tp2:
            base = sig.tp2
        elif sig.tp1:
            base = sig.tp1
        if sig.tp3:
            bull = sig.tp3
        if price and base:
            bear = round(price * 0.88, 2)

    return bear, base, bull


def _catalyst_info(earnings_dates: list) -> tuple[str | None, int | None]:
    """Return (event_label, days_until) for the nearest upcoming earnings."""
    from datetime import date as dt_date
    today = dt_date.today()
    upcoming = []
    for e in earnings_dates:
        try:
            d = e.date if hasattr(e.date, "year") else dt_date.fromisoformat(str(e.date)[:10])
            if d >= today:
                upcoming.append(d)
        except Exception:
            continue
    if not upcoming:
        return None, None
    nearest = min(upcoming)
    days = (nearest - today).days
    label = f"Earnings in {days}d ({nearest.strftime('%b %d')})"
    return label, days


def _build_why(
    composite: float,
    scores_map: dict[str, int],
    sig, rat, price: float | None,
    news_score: int, eq_score: int,
    entry_timing: str,
    conflict_note: str | None,
) -> str:
    facts = []

    if sig and sig.rsi_value is not None:
        if sig.rsi_value < 35:
            facts.append(f"RSI {sig.rsi_value:.0f} (oversold)")
        elif sig.rsi_value > 70:
            facts.append(f"RSI {sig.rsi_value:.0f} (overbought)")

    beats_with_data = []
    if sig:
        pass
    if eq_score >= 75:
        facts.append("consistent EPS beats")
    elif eq_score <= 30:
        facts.append("EPS misses trend")

    if news_score >= 70:
        facts.append("positive news flow")
    elif news_score <= 30:
        facts.append("negative news flow")

    if rat and rat.target_mean is not None and price and price > 0:
        upside = (rat.target_mean - price) / price * 100
        if upside > 15:
            facts.append(f"{upside:.0f}% analyst upside")
        elif upside < -10:
            facts.append(f"{abs(upside):.0f}% below analyst target")

    # Conflict note takes priority in the tail
    if conflict_note:
        tail = conflict_note
    elif entry_timing.startswith("WAIT POST"):
        tail = "earnings risk — size smaller or wait for the print"
    elif entry_timing.startswith("ENTER NOW"):
        tail = "setup confirmed — entry conditions met"
    elif entry_timing.startswith("DO NOT"):
        tail = "risk management priority"
    elif composite >= 60:
        tail = "constructive risk/reward"
    elif composite >= 45:
        tail = "monitor for catalyst"
    else:
        tail = "risk management priority"

    if facts:
        return f"{', '.join(facts)} — {tail}"
    if composite >= 60:
        return "Multiple signals confirm bullish bias — " + tail
    if composite >= 45:
        return "Mixed signals — " + tail
    return "Bearish signal convergence across multiple dimensions — " + tail


def _detect_conflict(scores_map: dict[str, int]) -> str | None:
    """Detect when high-weight signals diverge meaningfully."""
    tech = scores_map.get("technical", 50)
    fund = scores_map.get("fundamental", 50)
    news = scores_map.get("news_sentiment", 50)
    mom  = scores_map.get("momentum", 50)

    bullish = [k for k, v in scores_map.items() if v >= 65]
    bearish = [k for k, v in scores_map.items() if v <= 35]

    if not bullish or not bearish:
        return None

    # Major conflict: technicals bullish but fundamentals bearish (or vice versa)
    if tech >= 65 and fund <= 35:
        return "technical setup is bullish but fundamentals are weak — treat as speculative"
    if fund >= 65 and tech <= 35:
        return "strong fundamentals but technical timing is poor — wait for chart confirmation"
    if news <= 30 and tech >= 65:
        return "negative news flow conflicts with bullish technicals — monitor headline risk"
    if mom <= 35 and fund >= 65:
        return "strong fundamentals but momentum is fading — wait for trend reversal"

    # Generic conflict
    bull_labels = ", ".join(bullish[:2])
    bear_labels = ", ".join(bearish[:2])
    return f"{bull_labels} bullish vs {bear_labels} bearish — mixed conviction"


def _compute_verdict(analysis: FullStockAnalysis, time_horizon: str = "swing") -> VerdictResponse:
    sig   = analysis.trading_signals
    score = analysis.score
    fct   = analysis.forecast
    rat   = analysis.analyst_rating
    rsk   = analysis.risk_profile
    m     = analysis.metrics
    si    = analysis.short_interest
    price = m.current_price if m else None

    horizon = time_horizon if time_horizon in _HORIZON_WEIGHTS else "swing"
    weights = _HORIZON_WEIGHTS[horizon]

    # ── Technical ────────────────────────────────────────────────────────────
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

    # ── Fundamental ──────────────────────────────────────────────────────────
    if score and score.components:
        c = score.components
        gross_n  = c.get("Gross Margin", 0) / 25 * 100
        roe_n    = c.get("ROE",          0) / 20 * 100
        fcf_n    = c.get("FCF Margin",   0) / 20 * 100
        val_n    = c.get("Valuation",    0) / 20 * 100
        growth_n = c.get("Growth",       0) / 15 * 100
        fund_score = int(gross_n * 0.30 + roe_n * 0.25 + fcf_n * 0.25 + val_n * 0.10 + growth_n * 0.10)
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

    # ── AI Outlook ───────────────────────────────────────────────────────────
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

    # ── Analyst ──────────────────────────────────────────────────────────────
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

    # ── Momentum ─────────────────────────────────────────────────────────────
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

    # ── News & Sentiment ─────────────────────────────────────────────────────
    news_score, news_label = _score_news_sentiment(analysis.news)

    # ── Earnings Quality ─────────────────────────────────────────────────────
    eq_score, eq_label = _score_earnings_quality(analysis.earnings_dates)

    # ── Risk ─────────────────────────────────────────────────────────────────
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

    # ── Weighted composite (horizon-aware) ───────────────────────────────────
    scores_map = {
        "technical": tech_score, "fundamental": fund_score, "ai_outlook": ai_score,
        "analyst": analyst_score, "momentum": momentum_score,
        "news_sentiment": news_score, "earnings_quality": eq_score, "risk": risk_score,
    }
    composite = sum(scores_map[k] * weights[k] for k in weights)

    verdict = (
        "STRONG BUY"  if composite >= 75 else
        "BUY"         if composite >= 60 else
        "HOLD"        if composite >= 45 else
        "SELL"        if composite >= 30 else
        "STRONG SELL"
    )

    # ── Price targets (bear / base / bull) ───────────────────────────────────
    pt_bear, pt_base, pt_bull = _price_target_range(rat, sig, price)
    price_target = pt_base
    if price_target is None and sig and sig.tp1:
        price_target = sig.tp1

    stop_loss = _clean(round(sig.stop_loss, 2) if sig and sig.stop_loss else None)

    # ── Entry timing ─────────────────────────────────────────────────────────
    earnings_prox = sig.earnings_proximity if sig else None
    entry_timing, entry_zone = _entry_timing(sig, price, composite, earnings_prox)

    # ── Position sizing ──────────────────────────────────────────────────────
    vol = rsk.volatility if rsk else None
    pos_suggested, pos_max = _position_size(composite, price, stop_loss, vol)

    # ── Catalyst ─────────────────────────────────────────────────────────────
    catalyst_event, catalyst_days = _catalyst_info(analysis.earnings_dates)

    # ── Conflict detection ───────────────────────────────────────────────────
    conflict_note = _detect_conflict(scores_map)

    # ── Why text ─────────────────────────────────────────────────────────────
    why = _build_why(
        composite, scores_map, sig, rat, price,
        news_score, eq_score, entry_timing, conflict_note,
    )

    return VerdictResponse(
        verdict=verdict,
        confidence=int(round(composite)),
        vf_score=int(round(composite)),
        signals={
            "technical":        VerdictSignalDetail(label=tech_label,      score=tech_score,     weight=weights["technical"]),
            "fundamental":      VerdictSignalDetail(label=fund_label,      score=fund_score,     weight=weights["fundamental"]),
            "ai_outlook":       VerdictSignalDetail(label=ai_label,        score=ai_score,       weight=weights["ai_outlook"]),
            "analyst":          VerdictSignalDetail(label=analyst_label,   score=analyst_score,  weight=weights["analyst"]),
            "momentum":         VerdictSignalDetail(label=momentum_label,  score=momentum_score, weight=weights["momentum"]),
            "news_sentiment":   VerdictSignalDetail(label=news_label,      score=news_score,     weight=weights["news_sentiment"]),
            "earnings_quality": VerdictSignalDetail(label=eq_label,        score=eq_score,       weight=weights["earnings_quality"]),
            "risk":             VerdictSignalDetail(label=risk_label,      score=risk_score,     weight=weights["risk"]),
        },
        price_target=price_target,
        stop_loss=stop_loss,
        why=why,
        time_horizon=horizon,
        entry_timing=entry_timing,
        entry_price_zone=entry_zone,
        price_target_bear=pt_bear,
        price_target_bull=pt_bull,
        position_size_pct=pos_suggested,
        position_max_pct=pos_max,
        catalyst_event=catalyst_event,
        catalyst_days=catalyst_days,
        conflict_note=conflict_note,
    )
