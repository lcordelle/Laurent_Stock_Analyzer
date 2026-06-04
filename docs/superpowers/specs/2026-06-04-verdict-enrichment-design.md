# Verdict Engine Enrichment — Full Data Aggregate
**Date:** 2026-06-04
**Status:** Approved

## Objective

Upgrade the verdict engine so every available data point in `FullStockAnalysis` feeds into the BUY/SELL/HOLD decision. Add news sentiment scoring (keyword-based now, AI-upgradeable later) and earnings quality as a standalone signal. Enrich all existing signals with deeper sub-factors. Make the "why" text reference actual values.

---

## 1. Signal Architecture (8 signals)

| Signal | Weight | Was |
|---|---|---|
| Technical | 20% | 25% |
| Fundamental | 20% | 25% |
| AI Outlook | 20% | 20% |
| Analyst | 10% | 15% |
| Momentum | 10% | 10% |
| News & Sentiment | 10% | — new — |
| Earnings Quality | 5% | — new — |
| Risk | 5% | 5% |

All weights sum to 100%.

---

## 2. Signal Enrichment Details

### Technical (20%)
**Base:** `sig.confidence` (current behaviour preserved as starting point)

**Additions:**
- RSI value: `rsi_value < 35` → +10pts (oversold), `> 70` → −10pts (overbought)
- MACD signal: `macd_signal == "bullish"` → +5pts, `"bearish"` → −5pts
- ADX: `adx > 25` → trend is confirmed, apply 1.1× multiplier to final score (capped at 100)
- Support/resistance: `sr_at_support == True` → +8pts; `sr_at_resistance == True` → −8pts
- Signal quality cap: `signal_quality == "LOW"` → cap score at 65

**Fallback:** if `sig` is None → 50

### Fundamental (20%)
**Base:** Weighted average of `score.components`:
- profitability: 30%, roe: 25%, fcf: 25%, valuation: 10%, growth: 10%
- If components missing, fall back to `score.total`

**Additions:**
- Debt quality: `debt_to_equity < 0.5` → +5pts; `> 2.0` → −10pts
- Insider ownership: `short_interest.insider_own_pct > 10` → +5pts

**Fallback:** if `score` is None → 50

### AI Outlook (20%)
Unchanged from current implementation.

### Analyst (10%)
Unchanged from current implementation (mean rating + target upside).

### Momentum (10%)
**Base:** `trend_strength` mapping (current behaviour preserved)

**Additions:**
- 52-week range position: price in top 10% of 52w range → +10pts; bottom 10% → −5pts
- Relative strength: last value of `relative_strength` list > 0 → +5pts; < 0 → −5pts

**Fallback:** if `sig` is None → 50

### News & Sentiment (10%)

**Recency filter (applied before scoring):**
- Last 24 hours: weight 3.0
- 24–72 hours: weight 1.5
- 3–7 days: weight 0.5
- > 7 days: excluded

If no articles within 7 days → score 50, label "No Recent News"

**Keyword scoring per article (raw score −10 to +10):**

Bullish (+2 each): `beats`, `exceeds`, `record`, `upgrade`, `raises guidance`, `outperforms`, `strong growth`, `buyback`, `dividend increase`, `partnership`

Mild bullish (+1 each): `growth`, `positive`, `advances`, `gains`, `momentum`, `recovery`

Bearish (−2 each): `misses`, `downgrade`, `cuts guidance`, `disappoints`, `investigation`, `fraud`, `lawsuit`, `bankruptcy`, `layoffs`, `recall`

Mild bearish (−1 each): `decline`, `falls`, `concern`, `weak`, `slowdown`, `loss`

Scoring applies to both `title` and `summary` fields (case-insensitive).

**Aggregation:** `weighted_avg = sum(article_raw_score × recency_weight) / sum(recency_weight)`, mapped to 0–100 via `score = int(50 + weighted_avg * 5)`, clamped to [0, 100].

**Label mapping:**
| Score | Label |
|---|---|
| ≥ 75 | Positive |
| 60–74 | Mildly Positive |
| 40–59 | Neutral |
| 25–39 | Mildly Negative |
| < 25 | Negative |

**AI upgrade path:** Encapsulated in `_score_news_sentiment(news: list[NewsArticle]) -> tuple[int, str]`. Swap internals only when upgrading — caller signature unchanged.

### Earnings Quality (5%)
Uses last 4 entries from `earnings_dates` (sorted by date, most recent first).

**Base scoring:** Each entry with `beat` field:
- `beat == True` → +20pts toward 100-pt scale
- `beat == False` → −20pts
- Start at 50, apply beats/misses

**Streak bonus:**
- 4/4 beats → +10pts
- 3/4 beats → +5pts

**Fallback:** if fewer than 2 entries with `beat` data → score 50, label "Insufficient Data"

**Label mapping:**
| Score | Label |
|---|---|
| ≥ 80 | Consistent Beats |
| 60–79 | Mostly Beats |
| 40–59 | Mixed |
| < 40 | Missing Estimates |

### Risk (5%)
**Base:** `sharpe_ratio` mapping (current behaviour preserved)

**Additions:**
- Short interest: `short_pct_float > 20` → −15pts (high short = risk amplifier)
- Beta: `beta > 2.0` → −10pts; `beta < 0.5` → +5pts

**Fallback:** if `rsk` is None → 50

---

## 3. "Why" Text

Replace static if/else strings with a dynamic builder that references actual values. Examples:

- *"RSI at 32 (oversold) with 4 consecutive earnings beats and positive news momentum — asymmetric setup"*
- *"Analyst consensus cut to Hold as news turns negative — wait for re-rating catalyst"*
- *"Strong fundamentals and low volatility but no recent news coverage — monitor for catalyst"*

Logic: identify the 2 strongest signals (by score distance from 50) and the 1 weakest, compose a sentence from their labels and values. Fall back to current generic strings if values are missing.

---

## 4. Verdict Thresholds

Unchanged from current implementation:
| Composite | Verdict |
|---|---|
| ≥ 75 | STRONG BUY |
| 60–74 | BUY |
| 45–59 | HOLD |
| 30–44 | SELL |
| < 30 | STRONG SELL |

---

## 5. Files Changed

### Modified
- `api/routes/stocks.py` — `_score_news_sentiment()` helper + enrich `_compute_verdict()` for all 8 signals + dynamic `why` builder
- `frontend/src/lib/types.ts` — add `news_sentiment` and `earnings_quality` to `VerdictResponse['signals']`
- `frontend/src/components/stocks/VerdictBanner.tsx` — extend `signalKey()` for 2 new labels

### No new files required
