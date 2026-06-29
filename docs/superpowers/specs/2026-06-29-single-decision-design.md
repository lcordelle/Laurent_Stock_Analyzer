# Single-Source Decision — Design Spec

**Date:** 2026-06-29
**Status:** Approved design, pending implementation plan
**Branch:** `feature/single-decision` (off main @ 9e13b84)

## Problem

The Analysis page shows FOUR independent verdict/score surfaces that disagree (live, INTU):
1. `VerdictBanner` (top) — its OWN `/verdict` fetch via `verdictApi.get` (`_compute_verdict`,
   horizon-weighted) → stale "VF 74/100 · enter now".
2. "Tech Signal" sidebar (left of chart) — raw `trading_signals.signal` → "STRONG BUY · 100".
3. Decision panel — Quality×Setup → "Setup Weak · watchlist".
4. ScoreCard/ScoreGauge — `score.total` = 100.
Four engines, separate fetches, different timing → contradictions; the user can't tell what to follow.

## Solution: one computed action, rendered once, inputs demoted to "why"

### Single action verdict (backend, pure)
`decide_action(grade, band, direction) -> str` maps Quality grade × Setup band × direction to one word:

| Setup ↓ \ Quality → | A / B | C | D / F |
|---|---|---|---|
| Prime | STRONG BUY | BUY | SPECULATIVE |
| Strong | BUY | BUY | SPECULATIVE |
| Fair | ACCUMULATE | WATCH | AVOID |
| Weak | WATCH | WATCH | AVOID |

- `direction == "Short"` → **AVOID** (long-biased tool); `direction == "Stand aside"` → **WATCH**.
- `grade is None` or `band is None` → **WATCH** (insufficient data).
The existing `read_line(grade, band, direction)` stays as the aligned plain-English instruction
(it keys off the same inputs, so action + instruction never contradict).

`Decision` gains `action: str`. Everything is computed from the single `/analyze` response.

### Frontend — collapse 4 surfaces into 1
- **Remove** `<VerdictBanner>` from `Analysis.tsx` (and its import) — eliminates the separate
  `/verdict` fetch and the stale 74. (Backend `_compute_verdict` and the `/verdict` route stay —
  alerts/opportunities use them. The `VerdictBanner.tsx` component file is deleted if unused elsewhere;
  `verdictApi` left in `services/api.ts`, harmless.)
- **Remove the "Tech Signal" verdict** from the chart sidebar (the big `{signal}` headline, the
  `computeTier` tier, and the `computeWhyNow` text — they are a competing verdict). KEEP the
  **trade levels** in that column (entry / stop / TP1-3 / RSI / S-R) but under a neutral header
  like "Trade levels" — execution data, not a verdict.
- **Decision panel = the hero**, single source of truth, at the top:
  - Big colored **action word** (STRONG BUY/BUY/ACCUMULATE/WATCH/SPECULATIVE/AVOID) + the `read`
    instruction beside it.
  - Then the two axes (Quality | Setup), setup drivers, regime, EV, calibration, sizing — all
    supporting "why".
  - Action color: STRONG BUY/BUY `#00e676`, ACCUMULATE `#84cc16`, WATCH `#ffab00`,
    SPECULATIVE `#ff7043`, AVOID `#ff1744`.
- All of action / quality / setup / levels now derive from ONE `/analyze` response → no 74-vs-100,
  no contradictions.

## Components touched
- `utils/decision_engine.py`: add `decide_action` (pure).
- `api/models/responses.py`: `Decision` gains `action: str`.
- `api/routes/stocks.py`: set `action=decide_action(quality.grade, band, setup_raw["direction"])`.
- `frontend/src/lib/types.ts`: `Decision.action: string`.
- `frontend/src/components/stocks/DecisionPanel.tsx`: hero action header.
- `frontend/src/pages/Analysis.tsx`: remove VerdictBanner + the sidebar verdict; relabel trade levels.

## Edge cases
- Missing grade/band → action "WATCH", instruction falls back (read_line already handles None).
- `decision` is None (build failed) → panel not rendered (existing gate); no verdict shown anywhere
  else now, so the page simply omits the call rather than showing a wrong one.
- Sidebar with no trading signals → trade-levels section shows "—" as today.

## Testing
- pytest `tests/test_decision_engine.py`: `decide_action` covers every matrix cell + Short→AVOID +
  Stand-aside→WATCH + None→WATCH.
- Route: verify on :8011 that INTU returns `decision.action == "WATCH"` and no separate verdict.
- Frontend: build passes; the page shows exactly ONE verdict (the action); VerdictBanner and the
  Tech-Signal verdict are gone; trade levels remain. Manual UI verification (single source confirmed).

## Constraints
- python3 (py3.9-safe); never bind/disturb :8001 (use :8011); branch + review flow; single `/analyze`
  fetch drives the page (no new endpoint). Do not remove backend `_compute_verdict`.
