# Radar — Unified Stock Discovery
**Date:** 2026-06-04
**Status:** Approved

## Objective

Replace the Screener and Opportunities pages with a single **Radar** page that is decisive, directive, and powered by the same 8-signal verdict engine used on the Analysis page. Every stock in the ranked output carries the exact same composite score, verdict, and why text as if you had opened its full Analysis page.

---

## 1. Navigation

Remove two nav items ("Screener", "⚡ Opportunities"). Add one: **"Radar"** at route `/radar`.

Routes `/screener` and `/opportunities` redirect to `/radar`.

---

## 2. Page Modes

A toggle at the top of the page switches between two modes. Both produce the same ranked output format.

### Universe Mode (default)
Scans the curated ~500-stock universe automatically. Two-pass process (see Section 4). Results served from a 30-minute cache. A status bar shows total stocks scanned, stocks that made the shortlist, and time since last scan. A manual "Refresh" button triggers a background re-scan and returns the current cache immediately.

### My List Mode
User types up to 20 tickers (comma or space separated) and clicks "Run Verdict". Skips Pass 1. Runs `_compute_verdict()` directly on all submitted tickers in parallel. No caching — always fresh. Status bar shows "Your N stocks" and run timestamp.

---

## 3. Page Layout (both modes)

### Status bar
One line: mode label | stocks scanned | shortlist count | last updated | Refresh button (Universe only).

### Hero card — #1 pick
Full-width card for the top-ranked stock by composite score. Contains:
- Verdict badge (STRONG BUY / BUY / HOLD / SELL / STRONG SELL) in large type
- Ticker + company name
- Composite score (bold, large number, 0–100)
- All 8 signal pills: label + score + weight (Technical 20%, Fundamental 20%, AI Outlook 20%, Analyst 10%, Momentum 10%, News 10%, Earnings 5%, Risk 5%)
- Dynamic why text (e.g. "RSI 28 (oversold), 4/4 earnings beats, 22% analyst upside — asymmetric setup")
- Entry price, stop loss, analyst target, R:R ratio
- Primary CTA: "Full Analysis →" (navigates to `/analysis?ticker=XXX`)

### Filter bar
Pills above the shortlist: filter by domain, verdict tier (STRONG BUY / BUY / HOLD), signal quality. Filtering does not re-scan — hides/shows from current ranked set.

### Ranked shortlist — #2 to #25
Compact 2-column grid. Each card shows:
- Rank number
- Ticker + company name
- Verdict badge
- Composite score
- Why text (truncated to 1 line)
- 3 highest-conviction signal scores as mini pills
- Click → navigates to full Analysis page

### My List input (My List mode only)
Replaces hero + shortlist until submitted. Text area for tickers, "Run Verdict" button. After submission, renders same hero + shortlist layout. "Clear" link resets to Universe mode.

If My List returns 1–3 stocks, render all as full cards with no hero/shortlist split.

---

## 4. Two-Pass Backend Scoring (Universe Mode)

### Pass 1 — Quick scan (~500 stocks)
Reuse existing `_quick_scan()` in `opportunities.py`. Returns lightweight combined score per stock. Filter to top 50 by combined score. This pass already exists and is fast.

### Pass 2 — Full verdict (top 50)
For each of the top 50 stocks, call `_full_scan_ticker(ticker)` to fetch the complete yfinance dataset and build a `FullStockAnalysis` object. Then call `_compute_verdict(analysis)` — the exact same function used by the Analysis page. Returns composite score (0–100), verdict, all 8 signal details, price target, stop loss, and why text.

Run Pass 2 concurrently with a semaphore (max 4 concurrent, 0.3s delay between) to respect yfinance rate limits.

### Ranking
Sort Pass 2 results descending by composite score. Position 1 is the hero. Positions 2–25 are the shortlist. Positions 26–50 are held in the response but not rendered by default (available for filter expansion).

### Caching
30-minute in-memory cache. Disk backup as `radar_cache.json`. If a live scan returns fewer than 20 results (rate-limited), keep existing cache. Cache warmed on first request; background refresh available via manual trigger.

### My List scoring
No Pass 1. Run `_full_scan_ticker()` + `_compute_verdict()` on all submitted tickers in parallel. No cache. Ranked by composite score.

---

## 5. Verdict Engine Extraction

`_compute_verdict()`, `_score_news_sentiment()`, `_score_earnings_quality()`, and the 4 keyword sets (`_NEWS_BULLISH_STRONG`, `_NEWS_BULLISH_MILD`, `_NEWS_BEARISH_STRONG`, `_NEWS_BEARISH_MILD`) move from `api/routes/stocks.py` to **`api/utils/verdict.py`**.

Both `api/routes/stocks.py` and `api/routes/opportunities.py` import from `api/utils/verdict.py`.

No behaviour change to the Analysis page. The extraction is a pure refactor.

---

## 6. Data Models

### `RadarStock` (new, `api/models/responses.py`)
```python
class RadarStock(BaseModel):
    ticker: str
    name: Optional[str]
    domain: Optional[str]
    price: Optional[float]
    verdict: str                        # STRONG BUY / BUY / HOLD / SELL / STRONG SELL
    composite: int                      # 0–100, from _compute_verdict
    confidence: int                     # 0–100
    signals: dict[str, VerdictSignalDetail]   # 8 signals
    why: str                            # dynamic why text
    price_target: Optional[float]
    stop_loss: Optional[float]
    analyst_upside: Optional[float]
    risk_reward: Optional[float]
```

### `RadarResponse` (new, `api/models/responses.py`)
```python
class RadarResponse(BaseModel):
    mode: str                           # "universe" or "custom"
    stocks: list[RadarStock]            # ranked by composite desc
    total_scanned: int
    shortlist_count: int
    cached_at: Optional[float]          # unix timestamp
    scan_duration_seconds: Optional[float]
```

---

## 7. API Endpoints

### `GET /api/radar`
Returns cached `RadarResponse` for universe mode. Triggers background scan on first call if cache is empty.

### `POST /api/radar/refresh`
Triggers a fresh two-pass scan in the background. Returns current cache immediately.

### `POST /api/radar/custom`
Body: `{ "tickers": ["AAPL", "MSFT", ...] }` (max 20)
Runs full verdict on submitted tickers. Returns `RadarResponse` with `mode="custom"`.

---

## 8. Files Changed

### New
- `api/utils/verdict.py` — extracted verdict engine
- `frontend/src/pages/Radar.tsx` — unified Radar page

### Modified
- `api/routes/stocks.py` — import verdict engine from `api/utils/verdict.py`
- `api/routes/opportunities.py` — add `_full_scan_ticker()`, `_two_pass_scan()`, new `/api/radar` endpoints; keep existing `/opportunities` endpoint for backwards compatibility during transition
- `api/models/responses.py` — add `RadarStock`, `RadarResponse`
- `api/main.py` — register new radar router (if separated) or keep in opportunities.py
- `frontend/src/services/api.ts` — add `radarApi` (getUniverse, refresh, runCustom)
- `frontend/src/lib/types.ts` — add `RadarStock`, `RadarResponse`; keep old types until pages deleted
- `frontend/src/components/layout/TopNav.tsx` — replace Screener + Opportunities with Radar
- `frontend/src/App.tsx` — update routes

### Deleted
- `frontend/src/pages/Screener.tsx`
- `frontend/src/pages/Opportunities.tsx`

---

## 9. Removed Features

The following are intentionally removed — they added visual noise without improving decisiveness:

- Domain breakdown bar chart
- Investment themes grid (12 hardcoded theses)
- Market pulse KPI strip (universe/buy/sell counts)
- Top 5 conviction picks grid (replaced by hero card)
- Portfolio Analyzer tab (was in Screener — out of scope for this feature)

The domain filter pill is kept — it's the only filtering mechanism worth preserving.
