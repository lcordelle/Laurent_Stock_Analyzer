# Verdict Engine Enrichment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `_compute_verdict()` to aggregate all available `FullStockAnalysis` data into an 8-signal weighted verdict with live news sentiment scoring.

**Architecture:** All changes are in `api/routes/stocks.py` (two new helpers + rewritten verdict function) plus two tiny frontend edits. No new files, no new API endpoints, no extra network calls — the verdict endpoint already has the full analysis object in memory.

**Tech Stack:** Python 3, FastAPI, Pydantic, TypeScript, React

---

## File Map

| File | Change |
|---|---|
| `api/routes/stocks.py` | Add `_score_news_sentiment()`, `_score_earnings_quality()`, `_build_why()` helpers; rewrite `_compute_verdict()` for 8 signals |
| `frontend/src/lib/types.ts` | Add `news_sentiment` and `earnings_quality` to `VerdictResponse['signals']` |
| `frontend/src/components/stocks/VerdictBanner.tsx` | Extend `signalKey()` for the 2 new labels |

---

## Context for all tasks

### Key existing code locations
- `api/routes/stocks.py` line 800: `def _compute_verdict(analysis: FullStockAnalysis) -> VerdictResponse`
- `api/routes/stocks.py` lines 27–52: `VerdictResponse` and `VerdictSignalDetail` Pydantic models
- `frontend/src/lib/types.ts` lines 156–171: `VerdictResponse` TypeScript interface
- `frontend/src/components/stocks/VerdictBanner.tsx` line 12: `signalKey()` function

### Score component keys and max values (from `utils/stock_analyzer.py`)
`score.components` dict uses title-case keys:
- `'Gross Margin'` max 25 pts
- `'ROE'` max 20 pts
- `'FCF Margin'` max 20 pts
- `'Valuation'` max 20 pts
- `'Growth'` max 15 pts

These must be **normalised to 0–100** before weighting:
`gross_n = c.get('Gross Margin', 0) / 25 * 100`, etc.

### No automated test suite
Per `CLAUDE.md`: "No automated tests. Testing is manual via the web UI." Verification steps use `curl` against the running backend.

---

## Task 1: Add `_score_news_sentiment()` and `_score_earnings_quality()` helpers

**Files:**
- Modify: `api/routes/stocks.py` — insert two helpers immediately before `def _compute_verdict()` (line 800)

- [ ] **Step 1: Add `_score_news_sentiment()` immediately before `_compute_verdict` (line 800)**

Insert this block at line 800 (pushing `_compute_verdict` down):

```python
_NEWS_BULLISH_STRONG = {
    "beats", "exceeds", "record", "upgrade", "raises guidance",
    "outperforms", "strong growth", "buyback", "dividend increase", "partnership",
}
_NEWS_BULLISH_MILD = {"growth", "positive", "advances", "gains", "momentum", "recovery"}
_NEWS_BEARISH_STRONG = {
    "misses", "downgrade", "cuts guidance", "disappoints",
    "investigation", "fraud", "lawsuit", "bankruptcy", "layoffs", "recall",
}
_NEWS_BEARISH_MILD = {"decline", "falls", "concern", "weak", "slowdown", "loss"}


def _score_news_sentiment(news: list) -> tuple[int, str]:
    """Keyword-based news sentiment scorer. Returns (score 0-100, label).
    Upgrade path: swap internals only — caller signature is stable."""
    from datetime import datetime

    def _recency_weight(published) -> float:
        if not published:
            return 0.5
        try:
            pub_str = str(published)[:19]
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                try:
                    pub = datetime.strptime(pub_str, fmt)
                    age_h = (datetime.now() - pub).total_seconds() / 3600
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
    elif beat_count == len(recent):  score += 5  # 3/3 also gets bonus

    score = max(0, min(100, score))
    if score >= 80:   label = "Consistent Beats"
    elif score >= 60: label = "Mostly Beats"
    elif score >= 40: label = "Mixed"
    else:             label = "Missing Estimates"
    return score, label
```

- [ ] **Step 2: Verify the file parses cleanly**

```bash
cd /Users/laurentcordelle/Projects/VirtualFusion_Stock_Analyzer
python3 -c "import api.routes.stocks; print('OK')"
```

Expected output: `OK`

- [ ] **Step 3: Commit**

```bash
git add api/routes/stocks.py
git commit -m "feat: add _score_news_sentiment and _score_earnings_quality helpers"
```

---

## Task 2: Rewrite `_compute_verdict()` with 8 enriched signals

**Files:**
- Modify: `api/routes/stocks.py` — replace the entire `_compute_verdict` function body (lines ~800–953 after Task 1's insertions push them down)

- [ ] **Step 1: Replace the full `_compute_verdict` function**

Find the function starting with `def _compute_verdict(analysis: FullStockAnalysis) -> VerdictResponse:` and replace it entirely with:

```python
def _compute_verdict(analysis: FullStockAnalysis) -> VerdictResponse:
    sig  = analysis.trading_signals
    score = analysis.score
    fct  = analysis.forecast
    rat  = analysis.analyst_rating
    rsk  = analysis.risk_profile
    m    = analysis.metrics
    si   = analysis.short_interest
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
        "Bullish"        if "BUY"         in (sig.signal or "") else
        "Strong Bearish" if "STRONG SELL" in (sig.signal or "") else
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
        elif m.debt_to_equity > 2.0: fund_score = max(0,   fund_score - 10)
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
        if rat.target_mean and price and price > 0:
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

    bullish_count = sum(1 for s in scores_map.values() if s > 60)
    confidence = int(round(bullish_count / len(scores_map) * 100))

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

    if rat and rat.target_mean and price and price > 0:
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
        why = f"{', '.join(facts[:2])} — {tail}"
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
```

- [ ] **Step 2: Verify the file parses cleanly**

```bash
cd /Users/laurentcordelle/Projects/VirtualFusion_Stock_Analyzer
python3 -c "import api.routes.stocks; print('OK')"
```

Expected output: `OK`

- [ ] **Step 3: Hit the live verdict endpoint to verify the response shape**

Ensure the backend is running on port 8000 (or 8001). Then:

```bash
curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | python3 -c "import json,sys; print(json.load(sys.stdin).get('access_token',''))" > /tmp/tok.txt

TOKEN=$(cat /tmp/tok.txt)
curl -s "http://localhost:8000/api/stocks/AAPL/verdict?period=1y" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -40
```

Expected: JSON with `verdict`, `confidence`, `vf_score`, and `signals` containing exactly 8 keys: `technical`, `fundamental`, `ai_outlook`, `analyst`, `momentum`, `news_sentiment`, `earnings_quality`, `risk`.

- [ ] **Step 4: Commit**

```bash
git add api/routes/stocks.py
git commit -m "feat: rewrite _compute_verdict with 8-signal aggregate including news sentiment and earnings quality"
```

---

## Task 3: Update TypeScript types and VerdictBanner

**Files:**
- Modify: `frontend/src/lib/types.ts` lines 160–167
- Modify: `frontend/src/components/stocks/VerdictBanner.tsx` line 13

- [ ] **Step 1: Add the two new signal keys to `VerdictResponse` in `types.ts`**

In `frontend/src/lib/types.ts`, replace the `signals` block inside `VerdictResponse` (lines 160–167):

```ts
  signals: {
    technical: VerdictSignalDetail
    fundamental: VerdictSignalDetail
    ai_outlook: VerdictSignalDetail
    analyst: VerdictSignalDetail
    momentum: VerdictSignalDetail
    risk: VerdictSignalDetail
  }
```

With:

```ts
  signals: {
    technical: VerdictSignalDetail
    fundamental: VerdictSignalDetail
    ai_outlook: VerdictSignalDetail
    analyst: VerdictSignalDetail
    momentum: VerdictSignalDetail
    news_sentiment: VerdictSignalDetail
    earnings_quality: VerdictSignalDetail
    risk: VerdictSignalDetail
  }
```

- [ ] **Step 2: Extend `signalKey()` in `VerdictBanner.tsx` for the two new labels**

In `frontend/src/components/stocks/VerdictBanner.tsx`, replace line 13:

```ts
  return key === 'ai_outlook' ? 'AI Outlook' : key.charAt(0).toUpperCase() + key.slice(1)
```

With:

```ts
  const MAP: Record<string, string> = {
    ai_outlook: 'AI Outlook',
    news_sentiment: 'News',
    earnings_quality: 'Earnings',
  }
  return MAP[key] ?? key.charAt(0).toUpperCase() + key.slice(1)
```

- [ ] **Step 3: TypeScript check**

```bash
cd /Users/laurentcordelle/Projects/VirtualFusion_Stock_Analyzer/frontend
npx tsc --noEmit 2>&1 | head -20
```

Expected: no output (zero errors).

- [ ] **Step 4: Build frontend and redeploy**

```bash
cd /Users/laurentcordelle/Projects/VirtualFusion_Stock_Analyzer/frontend
npx vite build 2>&1 | tail -5
```

Expected: `✓ built in Xs`

Restart backend to pick up the `frontend/dist` rebuild:

```bash
pkill -f "uvicorn api.main:app" 2>/dev/null || true
sleep 1
cd /Users/laurentcordelle/Projects/VirtualFusion_Stock_Analyzer
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
sleep 3
curl -sf http://localhost:8000/api/health && echo " — OK"
```

- [ ] **Step 5: Visual verification**

Open https://laurent.ngrok.io, log in, go to Analysis, search AAPL.

Verify:
- Verdict banner shows 8 signal pills: Technical, Fundamental, AI Outlook, Analyst, Momentum, **News**, **Earnings**, Risk
- "Why" text references actual values (e.g. RSI reading, earnings beats count, analyst upside)
- Pills have correct colors (green/amber/red per score)
- No broken layout — 8 pills wrap cleanly

- [ ] **Step 6: Commit**

```bash
cd /Users/laurentcordelle/Projects/VirtualFusion_Stock_Analyzer
git add frontend/src/lib/types.ts frontend/src/components/stocks/VerdictBanner.tsx
git commit -m "feat: add news_sentiment and earnings_quality to VerdictBanner (8-signal layout)"
```
