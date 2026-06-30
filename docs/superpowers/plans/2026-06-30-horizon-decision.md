# Horizon-Aware Decision Implementation Plan

> **For agentic workers:** Execute INLINE (multi-file + calibration re-run + visual toggle; screenshot/verify each milestone on :8011). Checkbox tracking.

**Goal:** A Day/Swing/Long horizon toggle that recomputes the Decision (weights, window, action, track record, rationale) per horizon; all three precomputed server-side for instant toggling.

**Architecture:** `decision_engine` gains horizon profiles + horizon-aware `decide_action`/`read_line`; `compute_conviction` already takes `weights`. Calibration recomputes per horizon (batch emits 3 windows). The route builds `decision.horizons.{day,swing,long}` (shared `quality`). Frontend lifts a horizon state into `Analysis.tsx` and feeds the selected `HorizonDecision` to the bar + rail.

**Tech Stack:** Python (pure + pytest), FastAPI/Pydantic, React/TS.

## Global Constraints
- python3 (py3.9-safe). NEVER :8001 — verify on :8011. Single `/analyze` fetch precomputes all 3 horizons (instant toggle).
- Profiles: day{window 5, Tech .6/Trend .3/Val .1}, swing{30, .4/.3/.3}, long{120, .2/.3/.5}; default `swing`.
- `decide_action` horizon-aware: day=setup-only, swing=current matrix, long=quality-led (A/B + weak setup → ACCUMULATE).
- Keep single-Decision / cockpit layout / dark palette. Re-run `scripts/build_calibration.py`. Deploy via `./deploy.sh`.

---

### Task 1: Horizon profiles + horizon-aware action/read + tests

**Files:** Modify `utils/decision_engine.py`; Test `tests/test_decision_engine.py`.

**Interfaces — Produces:** `HORIZON_PROFILES: dict`; `decide_action(grade, band, direction, horizon="swing") -> str`; `read_line(grade, band, direction, horizon="swing") -> str`.

- [ ] **Step 1** Add `HORIZON_PROFILES = {"day": {"window":5,"label":"Day-trade","weights":{"Technical":0.6,"Trend":0.3,"Valuation":0.1}}, "swing": {"window":30,"label":"Swing","weights":{"Technical":0.4,"Trend":0.3,"Valuation":0.3}}, "long": {"window":120,"label":"Long-term","weights":{"Technical":0.2,"Trend":0.3,"Valuation":0.5}}}` (weights also carry `Fundamentals` key irrelevant since setup uses score=None — include `"Fundamentals":0.0` to satisfy the renorm? No: `compute_conviction` only sums weights for *available* factors, Fundamentals is None → excluded; so weights need only the 3 keys, but include `Fundamentals: 0.30` is harmless/ignored. Use just the 3 keys.)
- [ ] **Step 2** Make `decide_action` accept a `horizon` arg (default "swing"). Keep the current body as the `swing` branch. Add `day` (setup-only: Prime→STRONG BUY, Strong→BUY, Fair→WATCH, Weak→AVOID; Short→AVOID; Stand aside→WATCH) and `long` (quality-led: Short→AVOID; A/B→ Prime/Strong→STRONG BUY/BUY, Fair/Weak→ACCUMULATE; C→ Prime/Strong→BUY else WATCH; D/F→AVOID; grade None→WATCH).
- [ ] **Step 3** Make `read_line` accept `horizon` and branch phrasing (day: "no intraday edge"/"momentum setup"; swing: current; long: "quality compounder; entry soft but minor over months — scale in").
- [ ] **Step 4** Tests: `decide_action("A","Weak","Long","day")=="AVOID"`, `("A","Weak","Long","long")=="ACCUMULATE"`, `("A","Weak","Long","swing")=="WATCH"`; `("A","Prime","Long","day")=="STRONG BUY"`; profiles weights present for 3 keys. Update existing `decide_action` tests to pass `"swing"` (or rely on default). Run `python3 -m pytest tests/test_decision_engine.py -v` → pass.
- [ ] **Step 5** Commit `feat: horizon profiles + horizon-aware action/read`.

---

### Task 2: Per-horizon calibration + batch + tests

**Files:** Modify `utils/calibration.py`, `scripts/build_calibration.py`; Test `tests/test_calibration.py`.

- [ ] **Step 1** `bar_conviction(rsi, macd_hist, sma20, sma50, sma200, adx, close, vix, weights=None)` → pass `weights` to `compute_conviction`. `observations_for_history(hist, vix_series, horizon=HORIZON_DAYS, weights=None)` → use given `horizon` for the forward window and pass `weights` to `bar_conviction`.
- [ ] **Step 2** Batch: import `HORIZON_PROFILES` from `decision_engine`; for each horizon key compute `obs = observations_for_history(h, vix, profile["window"], profile["weights"])` accumulated per horizon; emit `table = {"generated_at","universe","universe_size","failed","horizons": {key: {"horizon_days":window,"total_obs":len,"buckets":bucketize(obs),"conviction_percentiles":conviction_percentiles(obs)}}}`.
- [ ] **Step 3** Tests: `observations_for_history` with custom `weights`+`horizon` returns obs with conviction reflecting the weights (e.g. day weights → different conviction than swing on the same bar); a synthetic batch-assembly test builds the 3-key `horizons` structure. Run `python3 -m pytest tests/test_calibration.py -v` → pass.
- [ ] **Step 4** Re-run `python3 scripts/build_calibration.py`; verify `data/calibration.json` has `horizons.day/swing/long` each with buckets + percentiles. Commit `feat: per-horizon calibration (5/30/120d) + batch`.

---

### Task 3: Response models + route (all horizons)

**Files:** Modify `api/models/responses.py`, `api/routes/stocks.py`.

- [ ] **Step 1** Models: add `class HorizonDecision(BaseModel): action: str; read: str; setup: Setup`; change `Decision` to `{ quality: Quality; default_horizon: str; horizons: dict[str, HorizonDecision] }` (drop top-level `setup`/`read`/`action`).
- [ ] **Step 2** Route: import `HORIZON_PROFILES`, `decide_action`, `read_line`. Build `quality` once. For each key,profile in `HORIZON_PROFILES`: `setup_raw = compute_conviction(score=None, signals=sig, forecast=raw_forecast, tunnel=..., regime=..., weights=profile["weights"])`; from `table["horizons"][key]` (cached) get percentile/band/bucket via `percentile_of`/`band_for`/`cal_lookup`; build `Setup(...)` (with `horizon_days=table_h["horizon_days"]`); `HorizonDecision(action=decide_action(grade,band,dir,key), read=read_line(grade,band,dir,key), setup=setup)`. Assemble `Decision(quality=quality, default_horizon="swing", horizons={...})`. try/except → decision None.
- [ ] **Step 3** Verify on :8011: INTU `decision.horizons.{day,swing,long}` actions differ (day AVOID-ish, long ACCUMULATE-ish), `default_horizon=="swing"`. Commit `feat: serve per-horizon decisions`.

---

### Task 4: Frontend toggle + rationale

**Files:** Modify `frontend/src/lib/types.ts`, `frontend/src/components/stocks/DecisionParts.tsx`, `frontend/src/pages/Analysis.tsx`.

- [ ] **Step 1** Types: `HorizonDecision { action: string; read: string; setup: Setup }`; `Decision { quality: Quality; default_horizon: string; horizons: Record<string, HorizonDecision> }`.
- [ ] **Step 2** Lift state in `Analysis.tsx`: `const [horizon, setHorizon] = useState('swing')`; reset to `data.decision.default_horizon` when data changes (useEffect). `const hd = data.decision?.horizons[horizon] ?? data.decision?.horizons['swing']`. Pass `decision`, `horizon`, `setHorizon`, `hd` to `<DecisionBar>`; pass `hd.setup` to rail `<SetupDrivers setup={hd.setup}/>` and `score={hd.setup.score}` to `<PositionSizing>`.
- [ ] **Step 3** `DecisionBar({ decision, horizon, setHorizon, hd })`: render a 3-seg toggle (Day·Swing·Long from `decision.horizons` keys / labels) that calls `setHorizon`; show `hd.action` (ACTION_COLOR), quality (shared), `hd.setup` band·dir·percentile + `({hd.setup.horizon_days}d)`, and `hd.read`. Add a rationale line (the read + top 2 drivers of `hd.setup`).
- [ ] **Step 4** `npm run build` passes. Screenshot INTU toggling Day/Swing/Long on :8011 → action/setup/read change; default Swing; 0 console errors. Commit `feat: horizon toggle + rationale in Decision`.

---

### Task 5: Review, merge, deploy
- [ ] Final opus review (contract alignment py↔ts across the new nested shape; no lost content; calibration 3-horizon honored). Merge to main, `./deploy.sh`, verify prod (toggle live, public 200), push.

---

## Self-Review
**Spec coverage:** profiles+weights (T1); horizon-aware action/read (T1); per-horizon calibration+batch+rerun (T2); response restructure {quality,default_horizon,horizons} + HorizonDecision (T3); route builds 3 (T3); frontend toggle+lifted state+rationale (T4); tests (T1,T2); deploy (T5). ✓
**Placeholders:** none — signatures + matrices + JSON shape given; exact bodies filled at execution from current code (decide_action swing body reused).
**Consistency:** `HORIZON_PROFILES` keys day/swing/long used in engine, batch, route, frontend; `decide_action(...,horizon)`/`read_line(...,horizon)` signatures consistent; `Decision{quality,default_horizon,horizons}` ↔ `HorizonDecision{action,read,setup}` py↔ts; calibration `table["horizons"][key]` consistent T2↔T3.
