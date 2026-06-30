# "Entry timing" Clarity Implementation Plan

> **For agentic workers:** Execute INLINE (frontend copy; screenshot-verify). Checkbox tracking.

**Goal:** Rename the "Setup" axis to "Entry timing" with an inline plain-language band gloss + an ⓘ tooltip.

**Tech Stack:** React + TS + Tailwind. One file: `frontend/src/components/stocks/DecisionParts.tsx`.

## Global Constraints
- Frontend copy only — no logic/data/backend change. Dark palette. Never :8001 (verify :8011). Deploy via `./deploy.sh`.

### Task 1: Entry-timing copy + gloss + tooltip
**Files:** Modify `frontend/src/components/stocks/DecisionParts.tsx`.
- [ ] **Step 1** Add `export const BAND_GLOSS: Record<string,string> = { Weak: 'poor entry right now', Fair: 'below-average timing', Strong: 'good entry', Prime: 'excellent entry' }` near the other color maps.
- [ ] **Step 2** In `DecisionBar`, the Setup `<div>`: rename the label `Setup` → `Entry timing ⓘ` with `cursor-help` + a `title=` tooltip (the full method string from the spec); after `{setup.band ?? '—'}` add `{setup.band && <span className="text-xs" style={{ color: '#475569' }}>{BAND_GLOSS[setup.band] ?? ''}</span>}`.
- [ ] **Step 3** Rename `SetupDrivers` header "Setup drivers" → "Entry-timing drivers"; rename the sizing `SizeStat` label "Setup-scaled" → "Timing-scaled".
- [ ] **Step 4** `npm install` (fresh worktree) + `npm run build` → passes. Screenshot Decision bar on :8011 → "Entry timing · Weak — poor entry right now"; ⓘ tooltip present; horizon toggle still updates gloss. 0 console errors. Commit.

### Task 2: Review, merge, deploy
- [ ] Quick diff review (copy-only, no logic touched); merge to main; `./deploy.sh`; verify prod; push.

## Self-Review
Spec coverage: rename (T1 S2), gloss map+inline (T1 S1,S2), tooltip (T1 S2), drivers header + sizing label (T1 S3), verify+deploy (T1 S4, T2). No placeholders. Consistency: `BAND_GLOSS` keys = band words (Weak/Fair/Strong/Prime) matching `BAND_COLOR`.
