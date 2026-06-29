# Analysis Screen Cockpit Redesign — Design Spec

**Date:** 2026-06-29
**Status:** Approved design, pending implementation plan

## Goal

Redesign the stock Analysis screen for space efficiency and a best-in-class dense "cockpit"
layout — same content, far less wasted space and scrolling. Today the page is a ~6–7 screen
vertical stack of full-width bands with poor horizontal use (half-empty rows, cramped sidebar
vs wide chart, key data buried below the fold).

## Layout (12-col grid, desktop-first; stacks on < lg)

1. **Header bar** (slim, full-width): ticker badge · company · sector | price + %change + 52w
   position | data-source/stale badges | Watchlist + quick actions. One row.
2. **Decision bar** (full-width, compact horizontal — replaces the tall stacked panel top):
   big **action** verdict · **Quality** (grade + score) · **Setup** (band · direction · percentile)
   · the **read** instruction. The drivers/regime/EV/sizing move to the rail (below).
3. **Cockpit row** (the hero, above the fold):
   - **Chart** (≈8/12): existing `CandlestickChart` (candles + RSI + MACD, period + RS/TUN toggles).
   - **Live rail** (≈4/12), stacked compact cards: **Trade levels** (`PriceLadder` + R:R),
     **Setup drivers + regime + EV**, **Position sizing**, **Analyst target** (mini).
4. **Valuation Tunnel** (full-width band, tightened height) — kept (hero feature).
5. **Depth tabs** (dense 2–3 col grids, not full-width stacks): Overview (Score + Score gauge +
   factor grades + financial metrics packed multi-col), Financials, Risk, Catalysts, News, AI.

## Component structure
- **New** `frontend/src/components/stocks/DecisionBar.tsx`: compact horizontal verdict (consumes
  `data.decision`) — action + quality + setup + read.
- **Refactor** `DecisionPanel.tsx` into rail-friendly pieces, or **new** rail sections that reuse
  its parts: `SetupDrivers`, `PositionSizing` (extract the drivers list + the sizing calculator so
  both the bar and the rail can use them without duplication). Keep `computeSizing`/types intact.
- **Cockpit + rail** assembled in `Analysis.tsx` via a CSS grid (`lg:grid-cols-12`); the chart card
  spans 8, the rail spans 4; rail stacks under the chart below `lg`.
- `PriceLadder` (already in Analysis.tsx) moves into the rail.

## Consolidation (same content, no duplication)
- **Metrics**: `MetricsStrip` and the Overview `MetricsTable` show overlapping numbers → keep ONE
  canonical metrics presentation (the dense `MetricsTable` in Overview); drop the redundant strip
  (its few headline KPIs already appear in the header/rail).
- **Analyst target**: shown twice today (rail-area + a full-width band) → show ONCE (rail mini),
  with the full target range available in Overview if needed.
- No information removed — only de-duplicated.

## Design system (applied across all panels)
- Spacing scale 4/8/12/16px; tighter card padding (`p-3`/`p-4`), consistent `gap-3`/`gap-4`.
- One type scale: section labels `text-xs uppercase tracking-wide #475569`; values `text-sm`/`tabular-nums`;
  hero numbers `text-2xl/3xl font-black`. Existing dark palette (`#0a0e1a`/`#111827` cards,
  `#00e676`/`#ff1744`/`#ffab00` semantics) preserved.
- Cards share one rounded-xl border style; consistent section headers.
- Responsive: 12-col cockpit → single column under `lg` (rail below chart); tabs scroll-x on narrow.

## Edge cases
- `data.decision` absent → Decision bar hidden, rail shows trade levels/metrics only (existing gates).
- No trade signals → trade-levels card shows "No trade setup" (existing PriceLadder behavior).
- Narrow viewport → everything stacks; no horizontal page scroll (wide elements scroll internally).

## Testing / verification
- No unit tests (pure layout). `npm run build` (tsc) passes. Manual + screenshot verification:
  full-page screenshot before/after; confirm above-the-fold shows decision + chart + rail; confirm
  total page height materially reduced; confirm no content lost (every prior section still present);
  responsive check at lg and a narrow width; 0 console errors.
- Verify on :8011 (never :8001); deploy via `./deploy.sh` after merge.

## Constraints
- Same content (nothing removed; duplicates consolidated). Keep single-Decision/Quality×Setup/tunnel
  logic + all data wiring. Dark theme. py n/a (frontend only). Branch + screenshot-iterate + review.
