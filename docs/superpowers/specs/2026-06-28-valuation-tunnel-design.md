# Valuation Tunnel — Design Spec

**Date:** 2026-06-28
**Status:** Approved design, pending implementation plan

## Purpose

Add a "blue tunnel" overlay to the candlestick chart that lets a pro trader see, at a
glance, **where price is relative to where value should be — and where it is heading.**

One continuous blue band:
- **Left of today (historical):** a fair-value channel across the visible history.
- **Right of today (forecast):** the channel projected forward, widening with √time.
- **Price/trend line overlaid**, so the read is immediate:
  - Price **above** the tunnel → stretched / overvalued.
  - Price **below** the tunnel → cheap / oversold.
  - Price **inside** → fairly valued.
  - Trend rising into the upper edge → momentum running ahead of value.

## Non-goals

- Not a moving-average tunnel (Vegas/EMA band). Explicitly rejected.
- No new valuation model. Reuse existing `calculate_forecast` outputs.
- No changes to the running production service lifecycle (see Deployment).

## Approach

### Historical portion — linear regression channel
- Fit a linear regression to `log(Close)` over the requested period window.
- Center line = regression trendline (exp-transformed back to price space).
- Band = trendline × (1 ± k · σ_resid), where σ_resid = std-dev of regression residuals
  in log space, k configurable (default k = 2).
- Reads as the classic statistical trend channel: "where is price vs its trend."

### Forecast portion — drift ± volatility cone (GBM confidence cone)
For t = 1 … N trading days forward from today (P₀ = last close):
- `center(t)  = P₀ · (1 + drift · t/252)`
- `upper(t)   = center(t) · (1 + k · σ_daily · √t)`
- `lower(t)   = center(t) · (1 − k · σ_daily · √t)`

Where:
- `drift` = **upgraded blended drift** (see below), not raw `annual_return_estimate`.
- `σ_daily` derived from the existing annualized `volatility` (÷ √252).
- The √t term is why the cone fans out — uncertainty compounds with √time.
- Handoff at "today": forecast center anchored so it joins the historical channel's
  right end (continuity at P₀).

### Upgraded drift model (do this before drawing the cone)
The cone's center must be defensible, not momentum-biased. Replace the single
momentum/score drift with a blended annualized drift from independent, weighted signals:

- **Analyst target** — `(target_mean / current_price − 1)` annualized over the analyst
  horizon. Fundamental anchor. Source: existing `AnalystRating.target_mean`. Skip if absent.
- **Regression slope** — annualized slope of the historical log-price regression (same fit
  used for the historical channel). Statistical trend continuation.
- **Mean reversion** — pull toward the regression fair-value line: when price sits above
  the channel, drift is dampened/negative; below, lifted. Prevents extrapolating froth.
- **Momentum/score** — the existing `annual_return_estimate`, retained but down-weighted.

Default weights (tunable, document in code): analyst 0.35, regression 0.30,
mean-reversion 0.20, momentum 0.15. Renormalize over whichever components are available.
Clamp final annual drift to a sane range (e.g. ±50%) so the cone center stays on-scale.

### Defaults
- N (forecast horizon) = 30 trading days (matches existing forecast `days=30`).
- k (band width) = 2 (≈95% under normal assumptions).
- Tunnel is **toggleable**, default **on**.

## Data contract

Extend the analysis response with a `valuation_tunnel` object (sibling of `indicators`):

```ts
export interface ValuationTunnel {
  // Historical arrays, aligned 1:1 with ohlcv rows:
  hist_mid:   (number|null)[]
  hist_upper: (number|null)[]
  hist_lower: (number|null)[]
  // Forecast arrays, one entry per future trading day:
  future_dates: string[]            // ISO dates after last candle
  fc_mid:   number[]
  fc_upper: number[]
  fc_lower: number[]
  // Meta
  horizon_days: number
  k: number
  drift_annual: number
  sigma_annual: number
}
```

Backend: computed in `utils/stock_analyzer.py` (new method, e.g.
`calculate_valuation_tunnel(hist, forecast)`), assembled in `api/routes/stocks.py`,
typed in `api/models/responses.py`, returned on `FullStockAnalysis`.

Frontend: mirror type in `frontend/src/lib/types.ts`, consume in
`CandlestickChart.tsx`.

## Rendering (CandlestickChart.tsx)

- Reuse the existing Bollinger band pattern (two `Line`s + shaded fill).
- Append the `future_dates` as extra rows to the chart series with **null OHLC** and
  populated tunnel values, so recharts extends the x-axis past the last candle.
  (This future-row append is the one genuinely new mechanic vs. existing overlays.)
- Blue palette: solid-ish historical band, forecast cone shaded and fading toward edges.
- `ReferenceLine` (vertical) at "today" marking the history→forecast handoff.
- Toggle chip alongside the existing period buttons to show/hide the tunnel.

## Edge cases

- Insufficient history (< ~30 rows): skip the tunnel, return null, chart renders as today.
- `calculate_forecast` returns None: no forecast cone; still draw historical channel if
  enough data, or skip entirely.
- NaN/None safety: follow the existing NaN-safe JSON encoder pattern already in the app.
- Very high volatility: cap k·σ·√t so the cone doesn't blow the y-axis scale (clamp to a
  sane multiple of price, e.g. ±60%).

## Deployment / operational constraints

- The production service runs continuously: `uvicorn api.main:app` on **port 8001**,
  tunneled via **laurent.ngrok.io**. This process MUST NOT be killed or disrupted.
- Backend changes take effect only on reload — confirm whether the running process uses
  `--reload`; if not, coordinate a safe reload rather than a blind restart.
- Frontend changes require a `vite build`; the API serves the built bundle. Rebuild and
  let the existing no-cache/stale-bundle reload logic pick it up.

## Testing

- Backend unit test for the blended drift: each component isolated (analyst-only,
  regression-only, etc.) returns expected sign/magnitude; weights renormalize when a
  component is missing; final drift clamps within ±50%.
- Backend unit test for `calculate_valuation_tunnel`: known synthetic series →
  monotonic cone widening, correct handoff continuity, null on insufficient data.
- Frontend: verify future rows extend the axis, tunnel toggles, no crash on null arrays.
- Visual QA via the browse tool against a live ticker.
