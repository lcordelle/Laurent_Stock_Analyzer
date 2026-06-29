# Decision Panel Redesign: Quality × Setup — Design Spec

**Date:** 2026-06-29
**Status:** Approved design, pending implementation plan
**Branch:** extends `feature/conviction-calibration` (not yet merged)

## Problem (diagnosed live)

The current panel shows one blended `conviction` 0–10 next to the VF score 0–100, and they
contradict: INTU = VF 100/100 but conviction 2.7/10. Root causes, confirmed on live data:
- The headline conviction **blends company quality with entry timing** into one number, shown
  beside the quality score as if comparable.
- Conviction = `|weighted-avg of [-1,1] factors| × regime(≤1) × 10`, so its **upper range is
  unreachable** — the 120k-obs calibration shows ~97% of observations fall in bands 0–4.
- Regime dampening is **baked invisibly** into the headline.
- The panel **contradicts itself**: headline conviction includes fundamentals (2.7) while the
  track-record proxy excludes them (1.0).

## Solution: two honest axes + distribution-relative setup

### Axis 1 — QUALITY (absolute, company)
- The existing VF fundamental score (0–100), with a letter grade:
  A ≥ 80, B 65–79, C 50–64, D 35–49, F < 35.

### Axis 2 — SETUP (relative, entry timing)
- **Setup score = `compute_conviction(score=None, …)`** — the ex-fundamentals timing conviction
  (Technical + Trend + Valuation + regime, renormalized over those three). This is exactly what
  the calibration measures, so headline and track record now agree.
- Expressed by **percentile + band**, not a bare 0–10:
  - The batch emits the conviction **distribution** (percentile breakpoints over all obs).
  - API maps the live setup score → percentile → band: **Weak <50th / Fair 50–80 / Strong 80–95
    / Prime ≥95** (cutoffs are percentiles of the real distribution, not arbitrary).
  - Raw 0–10 is retained but de-emphasized (small, secondary).
- Carries **direction** (Long / Short / Stand aside) and the calibration bucket's
  **hit-rate / avg forward return / n / as-of / low_sample**.
- **Setup-driver breakdown** = Technical / Trend / Valuation / regime (NO fundamentals — that's
  the Quality axis now).

### The "Read" line
A single explanatory sentence (not a Buy/Sell verdict score) generated from
(quality tier × setup band × direction), e.g. high-quality + weak-setup + long →
*"A-grade company, weak entry right now (downtrend + Risk-Off) — watchlist, not buy."*
Quality tiers: Strong (A/B), Mixed (C), Weak (D/F). Setup tiers: poor (Weak/Fair) vs good
(Strong/Prime). A small, documented sentence matrix; no new numeric score.

### Sizing
Unchanged mechanically; scales off the **Setup score** (entry timing is what sizing reflects).

## Architecture / components

### Calibration engine — `utils/calibration.py` (extend)
- `conviction_percentiles(observations) -> list[dict]`: percentile breakpoints
  `[{"p": 0, "value": 0.0}, {"p": 5, "value": ...}, … {"p": 100, "value": ...}]` (every 5th pct)
  built from the directional observations' conviction values.
- `percentile_of(breakpoints, conviction) -> float`: linear-interpolate a conviction to its
  percentile [0,100]; clamps at the ends.
- `band_for(percentile) -> str`: "Weak"/"Fair"/"Strong"/"Prime" by the 50/80/95 cutoffs.
- Batch (`scripts/build_calibration.py`) writes `conviction_percentiles` into `calibration.json`
  alongside the existing `buckets`. Re-run to regenerate the artifact.

### Quality grade — `utils/decision_engine.py` (small addition)
- `quality_grade(score) -> str` (A/B/C/D/F by the cutoffs above). Pure.

### Read sentence — `utils/decision_engine.py` (small addition)
- `read_line(quality_grade, setup_band, direction) -> str` from a documented matrix. Pure.

### Response model — `api/models/responses.py` (restructure)
Replace the flat `decision`/`calibration` with a two-axis `decision` object:
```
Decision {
  quality:  Quality { score: int, grade: str }
  setup:    Setup {
    score: float                 # raw 0–10 (secondary)
    direction: str
    percentile: float|None       # vs calibration distribution
    band: str|None               # Weak/Fair/Strong/Prime (None if no calibration)
    hit_rate: float|None; avg_forward_return: float|None; n: int|None
    low_sample: bool|None; as_of: str|None; horizon_days: int|None
    factors: list[DecisionFactor]   # Technical/Trend/Valuation/regime (no Fundamentals)
    regime: DecisionRegime
    expected_value_r: float|None
  }
  read: str                      # the explanatory sentence
}
```
(`DecisionFactor`/`DecisionRegime` reused. The old top-level `calibration` field is folded into
`setup`. Keep `Calibration` model only if still referenced; otherwise remove.)

### Route — `api/routes/stocks.py`
- Build the setup via `compute_conviction(score=None, …)` (drops Fundamentals → factors are the
  3 setup factors). Compute quality grade from `raw_score`. Look up percentile/band/bucket from
  the cached table. Compose `read_line`. Assemble the two-axis `Decision`. Wrap in try/except
  (never 500). Fundamentals no longer appear as a setup factor.

### Frontend — `frontend/src/components/stocks/DecisionPanel.tsx` (redesign)
- Two-axis header: QUALITY (grade + score) | SETUP (band + percentile bar + direction +
  hit/avg/n). De-emphasize the raw 0–10.
- "Read" line beneath the axes.
- Setup-driver breakdown (Technical/Trend/Valuation/regime).
- Sizing block unchanged (uses setup score).
- `types.ts`: mirror the new `Decision`/`Quality`/`Setup` shapes; `Analysis.tsx` passes
  `data.decision` (shape changed — update prop usage).

## Edge cases
- No calibration table → `percentile/band/hit_rate = None`; panel shows setup band as "—" with
  the build hint, still shows direction + drivers. Never crash.
- Stand-aside setup → band still computed from percentile; Read line notes low conviction.
- Missing VF score → quality grade "—"; Read line falls back to setup-only phrasing.
- low_sample bucket → percentile/band still shown (distribution-wide), but hit-rate flagged
  "small sample" as today.

## Testing
- pytest extends `tests/test_calibration.py`: `conviction_percentiles` monotonic & spans [0,100];
  `percentile_of` interpolates and clamps; `band_for` cutoffs (49→Weak, 50→Fair, 80→Strong,
  95→Prime).
- pytest extends `tests/test_decision_engine.py`: `quality_grade` cutoffs; `read_line` matrix
  (high-quality/weak-setup → watchlist phrasing; etc.).
- Route: setup conviction excludes fundamentals (factors have no "Fundamentals" entry);
  verify on :8011 that INTU shows Quality A + Setup band + a sensible Read line.
- Frontend: build passes; panel renders two axes + Read + drivers; manual UI verification.

## Deployment / constraints
- python3 (py3.9-safe, no `X | None` unions in .py); never bind :8001 (use :8011); branch +
  reviewed-subagent flow; regenerate `data/calibration.json` via the batch.
- Honesty preserved: every surfaced setup stat carries n + as-of + ex-fundamentals labeling.
