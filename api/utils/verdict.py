from __future__ import annotations
from typing import TYPE_CHECKING
from api.models.responses import FullStockAnalysis, VerdictSignalDetail, VerdictResponse

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
