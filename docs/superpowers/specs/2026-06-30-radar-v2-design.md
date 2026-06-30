# Radar v2 — Unified Decision + World-Class Surface — Design Spec

**Date:** 2026-06-30
**Status:** Approved design, pending implementation plan

## Goal

Make the Radar's per-stock recommendation **identical, by construction, to the single-stock
Analysis page**, and redesign the Radar UI to world-class standard around the same
Quality × Entry-timing model. Eliminate the current contradiction where a stock can read
"STRONG BUY / ENTER NOW" on the Radar but "WATCH · Quality A · Entry timing Weak" on its own page.

## Root cause (today)

`api/routes/opportunities.py::_full_scan_ticker` calls `_analyze_ticker()` (which already builds the
unified `analysis.decision` via `utils/decision_engine.py`), then **discards it** and instead calls the
legacy `api/utils/verdict.py::_compute_verdict()` — an 8-factor blended composite with its own
verdict/entry-timing/sizing. Two engines → guaranteed drift.

## Principle

**One engine, consumed in two places.** The Radar renders `analysis.decision` (Quality + the 3 horizon
decisions). `_compute_verdict` is removed from the radar/custom-scan path. Clicking a radar entry lands on
`/analysis` showing the *same function output* for the same horizon — no reconciliation, no possibility of
disagreement.

## Backend

### `utils/decision_engine.py` (additions only)
- Add `action_urgency(action: str) -> str`:
  - `"ACT_NOW"` if action in `{"STRONG BUY","BUY"}`
  - `"WATCH"` if action in `{"ACCUMULATE","WATCH"}`
  - `"REST"` otherwise (`AVOID`, `SPECULATIVE`)
- Add `size_cap_pct(conviction: float) -> float`: `round(min(max(conviction,0),10) * 10, 0)` — mirrors the
  single-stock "Timing-scaled … % max" stat (`score * 10`). Horizon-dependent (conviction differs per horizon).

### `api/models/responses.py` — restructure `RadarStock`
Drop the legacy verdict fields. New shape (Quality shared; one entry per horizon so the board re-ranks
client-side with no refetch):

```python
class RadarHorizon(BaseModel):
    action: str                      # STRONG BUY|BUY|ACCUMULATE|WATCH|SPECULATIVE|AVOID
    read: str
    band: Optional[str] = None       # Weak|Fair|Strong|Prime
    percentile: Optional[float] = None
    conviction: float
    direction: str                   # Long|Short|Stand aside
    urgency: str                     # ACT_NOW|WATCH|REST
    size_cap_pct: Optional[float] = None
    horizon_days: Optional[int] = None

class RadarStock(BaseModel):
    ticker: str
    name: Optional[str] = None
    domain: Optional[str] = None
    price: Optional[float] = None
    quality_score: Optional[int] = None
    quality_grade: Optional[str] = None
    default_horizon: str = "swing"
    horizons: dict[str, RadarHorizon]
    # supporting context (horizon-independent; informs, never overrides)
    analyst_upside: Optional[float] = None
    catalyst_event: Optional[str] = None
    catalyst_days: Optional[int] = None
    fair_value_gap_pct: Optional[float] = None   # price vs valuation-tunnel midline
```
`RadarResponse` unchanged (`mode, stocks, total_scanned, shortlist_count, cached_at, scan_duration_seconds`).
Add a `regime: Optional[DecisionRegime]` field to `RadarResponse` so the board can show market mood once
(taken from any stock's `setup.regime`, or `get_market_regime_cached()`).

### `api/routes/opportunities.py`
- Rewrite `_full_scan_ticker` to build `RadarStock` from `analysis.decision`:
  - `quality_score/grade` from `decision.quality`.
  - For each `hkey, hd` in `decision.horizons`: `RadarHorizon(action=hd.action, read=hd.read,
    band=hd.setup.band, percentile=hd.setup.percentile, conviction=hd.setup.score,
    direction=hd.setup.direction, urgency=action_urgency(hd.action),
    size_cap_pct=size_cap_pct(hd.setup.score), horizon_days=hd.setup.horizon_days)`.
  - `default_horizon = decision.default_horizon`.
  - `analyst_upside`: as today.
  - `catalyst_event/days`: reuse `_catalyst_info(analysis.earnings_dates)` (move/import from verdict.py, or
    call the existing helper).
  - `fair_value_gap_pct`: from `analysis.valuation_tunnel.hist_mid[-1]` vs price →
    `(price/mid - 1)*100`, NaN-safe; `None` if no tunnel.
  - If `analysis.decision is None` → return `None` (skip the stock; never fabricate a verdict).
- `_sanitize_radar_dict` / `_RADAR_FLOAT_FIELDS`: update to the new float fields
  (`price`, `analyst_upside`, `fair_value_gap_pct`, and per-horizon `conviction/percentile/size_cap_pct`).
- Ranking: sort stocks by selected-horizon **action rank** then quality then percentile. Since the board
  re-ranks client-side per horizon, the server may sort by `default_horizon` ("swing") for the initial payload.
  Define a shared action-rank order: STRONG BUY > BUY > ACCUMULATE > WATCH > SPECULATIVE > AVOID.
- `get_radar` / `refresh_radar` / `custom_radar`: populate `RadarResponse.regime`.
- **Remove** the `_action_urgency(entry_timing, verdict)` helper in opportunities.py (replaced by
  `decision_engine.action_urgency`). Leave `_compute_verdict` in verdict.py (other callers/tests) but it is no
  longer used by the radar.

> Performance: no extra fetches — `analysis.decision` is already computed. Conviction/percentile lookups are
> in-memory. Two-pass scan flow (quick-scan top 100 → full decision) is unchanged.

## Frontend

### `frontend/src/lib/types.ts`
Replace `RadarStock` with the new shape (`quality_score/grade`, `horizons: Record<string, RadarHorizon>`,
context fields); add `RadarHorizon`; add `regime` to `RadarResponse`.

### `frontend/src/components/stocks/DecisionParts.tsx`
Already exports `ACTION_COLOR`, `BAND_COLOR`, `GRADE_COLOR`, `DIR_COLOR`, `BAND_GLOSS`. Reuse as-is — no
changes. (Radar imports them for pixel-consistency with the cockpit.)

### `frontend/src/pages/Radar.tsx` — redesign
- **Horizon toggle** (Day · Swing · Long), default from `default_horizon`. Selecting re-derives every stock's
  `hd = stock.horizons[horizon]` → re-positions quadrant dots and re-sorts the list instantly (all precomputed).
- **Regime banner**: one line at top from `data.regime` (label + multiplier), styled like the cockpit.
- **Hero: Quality × Entry-timing quadrant** — recharts `ScatterChart` (already a dependency):
  - Y = `quality_score` (0–100); X = `hd.percentile` (0–100).
  - Reference lines: vertical at the Fair→Strong percentile cutoff; horizontal at the B/C quality cutoff →
    four quadrants. Top-right = high quality + strong entry.
  - Each dot colored by `ACTION_COLOR[hd.action]`; dim/desaturate `REST`. Tooltip = mini card
    (ticker, grade, band+gloss, action, read). Click → `navigate('/analysis?ticker=…')`.
  - Stocks with no percentile (no calibration) render in a thin "uncalibrated" strip below the chart, not the plot.
- **Ranked list** below the quadrant, sorted by action rank → quality → percentile, each row reusing cockpit
  language: grade chip (`GRADE_COLOR`), Entry-timing band + `BAND_GLOSS` ("Strong — good entry"), action
  verdict (`ACTION_COLOR`), the `read` line, and context chips: catalyst ⏱ (`catalyst_event`, red if
  `catalyst_days≤7`), analyst upside, fair-value gap (over/under), size cap (`size_cap_pct`).
  - Keep the ACT_NOW / WATCH / REST grouping as section headers (drive from `hd.urgency`), so the action-first
    triage you have today survives — now backed by the unified verdict.
- Keep **domain-filter pills** and **My List** custom mode (custom flows through the same builder).
- Warming/loading/empty states retained.

## Edge cases
- `decision is None` (no calibration / thin history) → stock omitted from radar (logged), never shown with a
  fabricated verdict.
- Horizon missing in `horizons` → fall back to `swing`, else omit the stock.
- `percentile`/`band` null for a horizon → dot goes to the uncalibrated strip; list row shows "—" band, no gloss.
- `fair_value_gap_pct` null when no tunnel → chip hidden.
- Custom-scan stocks have `domain=None` → "All" pill only.

## Consistency guarantees (the whole point)
Same `decision_engine` functions, same calibration table, same `quality_grade`, same band/percentile, same
`decide_action`/`read_line`, same `ACTION_COLOR`/`BAND_GLOSS`/`GRADE_COLOR`. A radar entry and the Analysis
page cannot disagree for the same ticker+horizon — they are the same object.

## Testing
- pytest (new `tests/test_radar_decision.py`): `action_urgency` mapping for all 6 actions; `size_cap_pct`
  bounds (0, 5, 10 → 0/50/100, capped); a `_full_scan_ticker`-shape unit on a synthetic `FullStockAnalysis`
  with a known `decision` → asserts `RadarStock.horizons` mirrors `decision.horizons` (action/band/urgency) and
  `quality_*` matches. No network.
- Manual on :8011: `/api/radar` returns stocks with `quality_grade` + 3 horizons; pick a ticker, confirm its
  radar action+band == the `/analysis` Decision for the same horizon (e.g. INTU swing). Toggle horizons →
  board re-ranks. Click a dot → lands on its analysis with the matching verdict. 0 console errors.
- Re-run not required (no calibration change). Deploy via `./deploy.sh`; verify prod + public 200.

## Constraints
- python3 (py3.9-safe); never bind :8001 (verify on :8011); single `/radar` payload precomputes all horizons.
- Additions only to `decision_engine`; no change to single-stock decision logic or calibration.
- Keep dark palette + cockpit tokens. Branch + screenshots + review. Commit/push only when asked.
