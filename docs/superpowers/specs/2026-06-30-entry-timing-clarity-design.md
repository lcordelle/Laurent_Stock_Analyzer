# "Entry timing" Clarity — Design Spec

**Date:** 2026-06-30
**Status:** Approved design, pending implementation plan

## Goal
Make the "Setup" axis self-explanatory. Rename it to **"Entry timing"**, add an always-visible
plain-language gloss of the band, and an ⓘ tooltip with the full method. Frontend copy only — no
logic/data change.

## Changes (all in `frontend/src/components/stocks/DecisionParts.tsx`)
1. **Rename label** "Setup" → **"Entry timing"** in `DecisionBar` (line ~38).
2. **Band gloss** — add `BAND_GLOSS = { Weak: "poor entry right now", Fair: "below-average timing",
   Strong: "good entry", Prime: "excellent entry" }`; render the gloss inline after the band word in
   `DecisionBar`, muted (e.g. `#475569`). So it reads: *"Entry timing · Weak — poor entry right now ·
   Long · 20th pct · 30d"*.
3. **ⓘ tooltip** on the "Entry timing" label: a small `ⓘ` with a native `title=` attribute (zero-dep,
   accessible) carrying:
   *"Is now a good moment to buy? Scored from price action only — trend, momentum, and price vs its
   fair-value channel, adjusted for the market mood — then ranked against ~120k historical setups.
   Excludes company quality (that's the Quality axis)."*
4. **Header rename** in `SetupDrivers` (line ~63): "Setup drivers" → **"Entry-timing drivers"**.
5. **Sizing stat** (line ~129): "Setup-scaled" → **"Timing-scaled"** (it scales off the entry-timing score).

`BAND_GLOSS` is exported/shared so any future surface can reuse it. Gloss shown only when `band` is non-null.

## Non-goals
- No change to backend, scoring, calibration, or the Quality axis. No change to the tunnel's own
  "SETUP (ENTRY TIMING)" chart label (already says entry timing).

## Edge cases
- `band` null (no calibration) → show "—" with no gloss; tooltip still present on the label.

## Testing
- `npm run build` (tsc) passes. Screenshot the Decision bar (Swing) → reads "Entry timing · Weak — poor
  entry right now"; hover ⓘ shows the definition; toggle horizons → gloss/band update. 0 console errors.
- Deploy via `./deploy.sh` after merge.

## Constraints
- Frontend copy only; dark palette; never :8001 (verify :8011); branch + screenshot + review.
