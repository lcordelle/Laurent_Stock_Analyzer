# Analysis Cockpit Redesign Implementation Plan

> **For agentic workers:** Execute INLINE with screenshot iteration (visual layout — not subagent-delegatable, nothing to unit-test). Steps use checkbox tracking. Verify each milestone with a real screenshot on :8011.

**Goal:** Re-lay the Analysis screen into a dense above-the-fold cockpit (compact Decision bar + chart-with-right-rail + tightened tunnel + dense depth tabs), same content, duplicates consolidated.

**Architecture:** Extract the Decision panel's pieces into reusable bits (compact bar + rail sections), restructure `Analysis.tsx` into a 12-col cockpit grid (chart 8 / live rail 4), tighten spacing to one density scale, dedup the metrics strip and double analyst-target. Pure frontend.

**Tech Stack:** React + TypeScript + Tailwind + Vite.

## Global Constraints
- Same content — nothing removed; only true duplicates consolidated (MetricsStrip→MetricsTable; analyst target shown once).
- Keep single-Decision / Quality×Setup / valuation-tunnel logic + all data wiring intact. Dark palette preserved (`#0a0e1a`/`#111827` cards; `#00e676`/`#ff1744`/`#ffab00` semantics).
- Responsive: 12-col cockpit collapses to single column under `lg` (rail below chart); no horizontal PAGE scroll (wide elements scroll internally).
- NEVER bind :8001; verify on :8011. `npm run build` (tsc) must pass at every commit.
- Density scale: spacing 4/8/12/16; card padding `p-3`/`p-4`; labels `text-xs uppercase tracking-wide #475569`.

---

### Task 1: Extract reusable Decision pieces

**Files:** Create `frontend/src/components/stocks/DecisionBar.tsx`; modify `DecisionPanel.tsx` (extract `SetupDrivers` + `PositionSizing` as exported sub-components reused by both panel and rail).

- [ ] **Step 1** Extract from `DecisionPanel.tsx` two exported components — `SetupDrivers({ setup })` (the drivers list + regime + EV rows) and `PositionSizing({ score, entry, stop, currentPrice })` (the account inputs + sizing grid). Keep `computeSizing`/`ACTION_COLOR`/maps. `DecisionPanel` itself may remain (used nowhere after redesign) or be deleted at the end.
- [ ] **Step 2** Create `DecisionBar.tsx`: a compact full-width horizontal row consuming `decision: Decision` — `[action badge] [Quality grade·score] [Setup band·direction·percentile] [read instruction]`, using `ACTION_COLOR`/`GRADE_COLOR`/`BAND_COLOR`. No drivers/sizing (those go to the rail).
- [ ] **Step 3** `cd frontend && npm run build` → passes. Commit `feat: extract DecisionBar + SetupDrivers + PositionSizing`.

---

### Task 2: Cockpit grid (chart + live rail) in Analysis.tsx

**Files:** Modify `frontend/src/pages/Analysis.tsx`.

- [ ] **Step 1** Replace the `<DecisionPanel .../>` usage with `<DecisionBar decision={data.decision} />` placed as the full-width band directly under the header.
- [ ] **Step 2** Restructure the cockpit grid from `lg:grid-cols-[300px_1fr]` (sidebar-left/chart-right) to `lg:grid-cols-12`: chart card in `lg:col-span-8`, a new **live rail** in `lg:col-span-4`. Rail stacks below chart under `lg`.
- [ ] **Step 3** Populate the rail (in this order), reusing existing pieces: Trade levels card (`PriceLadder` + R:R, already present), `<SetupDrivers setup={data.decision.setup} />`, `<PositionSizing .../>` (entry/stop/currentPrice as today), Analyst-target mini (`AnalystTargetChart` compact). Move the existing market-context / S-R / RSI mini rows into the rail too (they were in the old sidebar).
- [ ] **Step 4** `npm run build` → passes. Screenshot `/analysis?ticker=INTU` on :8011 → confirm decision bar + chart + rail sit together above the fold. Commit `feat: cockpit grid — chart + live rail`.

---

### Task 3: Tighten tunnel + dedup + dense depth tabs

**Files:** Modify `frontend/src/pages/Analysis.tsx` (+ minor component padding).

- [ ] **Step 1** Valuation Tunnel band: keep, reduce chart height (~300px) and card padding for a tighter footprint.
- [ ] **Step 2** Dedup: remove the standalone `<MetricsStrip>` (its KPIs live in header/rail + the Overview `MetricsTable`); remove the second full-width `<AnalystTargetChart>` band (kept once in the rail).
- [ ] **Step 3** Depth tabs Overview: wrap Score + ScoreGauge + FactorGrades + DividendScorecard + MetricsTable + RiskProfile in a dense `grid lg:grid-cols-2`/`xl:grid-cols-3` so they fill horizontally (kills the half-empty score-gauge row). Other tabs (Catalysts/News/AI) get consistent padding.
- [ ] **Step 4** `npm run build` → passes. Screenshot full page → confirm materially shorter, no half-empty rows, all sections still present. Commit `feat: tighten tunnel, dedup metrics/analyst, dense overview grid`.

---

### Task 4: Density pass + responsive + polish

**Files:** Modify the touched components/`Analysis.tsx`.

- [ ] **Step 1** Apply the one density scale across the new/edited cards: consistent `p-3`/`p-4`, `gap-3`, label style, rounded-xl borders. Remove leftover dead locals/imports (e.g. `MetricsStrip` import if unused) — let `tsc` flag them.
- [ ] **Step 2** Responsive check: screenshot at a narrow width (resize to ~700px) → rail stacks under chart, no horizontal page scroll. Screenshot at lg.
- [ ] **Step 3** `npm run build` → passes, 0 TS errors. Final full-page before/after screenshots. Commit `polish: density scale + responsive`.

---

### Task 5: Review, merge, deploy

- [ ] **Step 1** Final whole-branch review (opus) of the layout diff for regressions / lost content / dead refs.
- [ ] **Step 2** Merge to main, `./deploy.sh`, verify production (decision bar + cockpit live, public 200). Push.

---

## Self-Review

**Spec coverage:** header (existing, kept) + Decision bar (T1,T2) + cockpit chart/rail (T2) + tunnel tighten (T3) + depth tabs dense grid (T3) + dedup metrics & analyst (T3) + density system & responsive (T4) + same-content/no-removal (constraints + dedup-only) + verify screenshots (each task) + review/deploy (T5). ✓

**Placeholder scan:** none — steps name exact files/components/classes and the screenshot gate. JSX is assembled inline during execution with screenshot feedback (visual task), reusing named existing components (`PriceLadder`, `AnalystTargetChart`, `MetricsTable`, `FactorGrades`, etc.) and the Task-1 extracted `DecisionBar`/`SetupDrivers`/`PositionSizing`.

**Consistency:** `DecisionBar`/`SetupDrivers`/`PositionSizing` defined in T1, consumed in T2; `data.decision.setup`/`data.decision.action` per the current `Decision` shape; grid `lg:grid-cols-12` chart `col-span-8` / rail `col-span-4` consistent across T2.
