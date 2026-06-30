# Horizon-Aware Decision — Design Spec

**Date:** 2026-06-30
**Status:** Approved design, pending implementation plan

## Goal

Add a Day-trade / Swing / Long-term horizon toggle to the Decision section that **recomputes the
recommendation** for the selected horizon (weights, forward window, action, track record, and the
"why"), so the same stock reads correctly per trading style. Adds richer rationale + a clearer
recommendation. The current Decision is effectively the "Swing" horizon.

## Horizon profiles

| Horizon | key | window (d) | Setup weights Tech/Trend/Valuation | Quality's role in action |
|---|---|---|---|---|
| Day-trade | `day`   | 5   | 0.6 / 0.3 / 0.1 | ignored — setup is the call |
| Swing     | `swing` | 30  | 0.4 / 0.3 / 0.3 | balanced (today's matrix)   |
| Long-term | `long`  | 120 | 0.2 / 0.3 / 0.5 | dominant — quality is the call |

`HORIZON_PROFILES` in `decision_engine.py`: `{key: {"window": int, "weights": {"Technical","Trend","Valuation"}, "label": str}}`. Default = `swing`.

## Backend

### `utils/decision_engine.py`
- `HORIZON_PROFILES` constant (above). Setup conviction per horizon = `compute_conviction(score=None,
  signals, forecast, tunnel, regime, weights=profile.weights)` — `compute_conviction` already takes `weights`
  (renormalizes over the non-None Technical/Trend/Valuation).
- `decide_action(grade, band, direction, horizon)` — horizon-aware:
  - **day**: from SETUP only (quality ignored). Short→AVOID; Stand aside→WATCH; band Prime→STRONG BUY,
    Strong→BUY, Fair→WATCH, Weak→AVOID.
  - **swing**: the existing matrix (unchanged).
  - **long**: QUALITY-led. Short→AVOID; A/B → Prime/Strong→STRONG BUY/BUY, Fair/Weak→ACCUMULATE;
    C → good setup→BUY else WATCH; D/F→AVOID. (Weak entry on a quality name → ACCUMULATE, not WATCH.)
  - grade/band None → WATCH.
- `read_line(grade, band, direction, horizon)` — horizon-specific phrasing (day: intraday-edge framing;
  swing: entry-timing framing; long: compounder/scale-in framing).

### `utils/calibration.py` + `scripts/build_calibration.py`
- `bar_conviction(..., weights=None)` and `observations_for_history(hist, vix, horizon, weights=None)`
  accept horizon weights so calibration is recomputed with the matching profile + window.
- Batch loops the 3 horizons; `data/calibration.json` becomes:
  `{"generated_at", "universe", "universe_size", "horizons": {"day": {"horizon_days":5,"total_obs","buckets","conviction_percentiles"}, "swing": {...30}, "long": {...120}}}`.
  Re-run required (a few minutes, cached fetches).
- `load_table`/`lookup`/`percentile_of`/`band_for` unchanged; the route selects `table["horizons"][key]`.

### `api/routes/stocks.py` + `api/models/responses.py`
- Response restructure: `Decision { quality: Quality, default_horizon: str, horizons: dict[str, HorizonDecision] }`
  where `HorizonDecision { action: str, read: str, setup: Setup }`. `Quality` shared (horizon-independent).
  `Setup` shape unchanged (per-horizon values: score/band/percentile/hit/avg/n/window/factors/regime/EV).
- Route: for each horizon key, compute setup conviction (profile weights), look up that horizon's calibration
  (percentile/band/hit/avg/n/window), `decide_action(grade, band, dir, key)`, `read_line(...)`, assemble
  `HorizonDecision`. Build `horizons` map + `default_horizon="swing"`. Wrap in try/except (never 500).

## Frontend
- `types.ts`: `Decision { quality; default_horizon; horizons: Record<string, HorizonDecision> }`,
  `HorizonDecision { action; read; setup: Setup }`.
- **Lift horizon state to `Analysis.tsx`** (`const [horizon, setHorizon] = useState(data.decision?.default_horizon ?? 'swing')`),
  derive `const hd = data.decision?.horizons[horizon]`, pass `hd` (and `setHorizon`/options) to `DecisionBar`
  and pass `hd.setup` to the rail's `SetupDrivers` / `PositionSizing`.
- `DecisionBar`: render a 3-way toggle (Day · Swing · Long) + the selected `action`/quality/setup band/
  percentile (with its window) + the `read`. Toggle is instant (all horizons precomputed).
- Add an expanded **rationale** line under the bar (the horizon's `read` + the top drivers for that horizon).
- Keep dark palette + action colors.

## Edge cases
- `data.decision` absent → bar hidden (existing gate). A horizon missing in `horizons` → fall back to `swing`,
  else hide. Calibration table without a horizon key → that horizon shows band/hit as "—" (no crash).
- Per-horizon calibration window needs ≥ `60 + window` bars; long (120) needs ~180 bars — the batch already
  guards short history (skips), and `observations_for_history` returns [] when insufficient.

## Testing
- pytest `tests/test_decision_engine.py`: `decide_action` per horizon (day vs long divergence on A-quality/weak-setup:
  day→AVOID, long→ACCUMULATE, swing→WATCH); `HORIZON_PROFILES` weights sum/keys; `read_line` horizon phrasing.
- pytest `tests/test_calibration.py`: `observations_for_history` honors `weights` + `horizon`; batch table shape
  has all 3 horizon keys (unit-test the assembly on synthetic obs, not network).
- Route: verify on :8011 INTU returns `decision.horizons.{day,swing,long}` with differing actions; default swing.
- Frontend: build passes; toggle switches action/setup/read live; screenshot all 3 horizons; 0 console errors.
- Re-run `scripts/build_calibration.py`; confirm `calibration.json` has the 3-horizon structure.

## Constraints
- python3 (py3.9-safe); never :8001 (use :8011); single `/analyze` fetch precomputes all horizons (instant toggle).
- Keep single-Decision / Quality×Setup / cockpit layout. Deploy via `./deploy.sh` after merge. Branch + review.
