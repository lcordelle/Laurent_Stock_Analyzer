# Decision Panel — Design Spec

**Date:** 2026-06-28
**Status:** Approved design, pending implementation plan

## Purpose

Fuse the signals the analyzer already computes into a single, decision-ready output:
a **conviction call** (0–10 + direction), conditioned on the **live market regime**,
turned into a **concrete position size**. Closes audit gaps #1 (synthesis), #2 (sizing),
#4 (regime conditioning). The trader should get one calibrated answer with its reasoning,
not a wall of separate indicators to integrate by hand.

## Non-goals
- Full portfolio-aware sizing (correlation/concentration vs actual holdings) — that is
  gap #3, a later enhancement. Account size here is a configurable input, not the portfolio.
- New market data sources. Reuse existing signals + `market_breadth.get_market_regime()`.
- No change to the running :8001 service lifecycle beyond the normal deploy.

## Architecture (server = conviction, client = sizing)

### Backend — `utils/decision_engine.py` (new, pure, testable)
Pure function:
```
compute_conviction(score, signals, forecast, tunnel, regime, weights=None) -> dict
```
- `score`: fundamental total (0–100).
- `signals`: the trading_signals dict (signal, signal_quality, confidence, trend_strength, adx, rsi_value, optimal_entry, stop_loss, tp1, risk_reward).
- `forecast`: forecast dict (forecast_change_pct, trend).
- `tunnel`: valuation_tunnel dict (price vs hist_mid fair value, drift).
- `regime`: dict from `get_market_regime()` (`regime`, `vix`).

Returns:
```
{
  "conviction": float,            # 0–10
  "direction": "Long"|"Short"|"Stand aside",
  "factors": [                    # transparent breakdown, each scaled to its weight
    {"label": "Fundamentals", "score": 0-1, "weight": 0.30, "contribution": float, "detail": str},
    {"label": "Technical",    ...},
    {"label": "Trend",        ...},
    {"label": "Valuation",    ...}
  ],
  "regime": {"label": str, "vix": float|None, "multiplier": float},
  "expected_value_r": float|None, # conviction-weighted EV in R-multiples (see below)
  "rationale": str                # one-line summary
}
```

**Conviction math (transparent, retunable):**
- Each factor produces a signed sub-score in [-1, +1] (positive = bullish):
  - Fundamentals: `(score-50)/50`.
  - Technical: from signal (STRONG BUY=+1 … STRONG SELL=-1) blended with `confidence/100` and `signal_quality`.
  - Trend: ADX-confirmed trend_strength mapped to sign×strength (STRONG=±1, WEAK=±0.4, none=0).
  - Valuation: combine price-vs-fair-value (below fair value = +, above = −, scaled) with `sign(forecast_change_pct)·min(|chg|/10,1)`.
- Default weights: Fundamentals 0.30, Technical 0.30, Trend 0.20, Valuation 0.20.
- `raw = Σ weight_i · subscore_i` ∈ [-1,+1].
- **Regime multiplier** applied to the directional strength: Risk-On 1.0, Neutral 0.85,
  Risk-Off 0.65, Danger 0.45 for the *aligned* direction (a long in Danger is dampened;
  a short in Danger is not dampened — and vice-versa). Unknown regime → 1.0.
- `conviction = round(|raw| · regime_mult · 10, 1)` clamped [0,10].
- `direction`: Long if raw>+0.15, Short if raw<−0.15, else "Stand aside" (conviction shown but flagged low/conflicted).
- `expected_value_r`: if entry/stop/tp1 present, `R = (tp1−entry)/(entry−stop)` (long; mirror for short);
  `p = 0.5 + raw·regime_mult·0.4` (clamped [0.05,0.95]); `EV_R = p·R − (1−p)·1`. Null if no stop.

The function is pure — no I/O, no yfinance. Regime is passed in.

### Route wiring — `api/routes/stocks.py`
- Fetch regime via `get_market_regime()` **cached ~5 min** (add a tiny module-level TTL cache
  in `market_breadth.py`, or cache in the route) so it doesn't add a live VIX call per analysis.
- Build the `decision` object from the already-computed score/signals/forecast/tunnel + regime.
- Wrap in try/except (never 500 the analysis if decision fails) — mirror the tunnel pattern.
- Add `decision: Optional[Decision]` to `FullStockAnalysis` (new Pydantic model in responses.py).

### Frontend
- Type `Decision` in `frontend/src/lib/types.ts` mirroring the response; `decision?` on FullStockAnalysis.
- New `frontend/src/components/stocks/DecisionPanel.tsx`:
  - **Conviction gauge** (0–10) + **direction badge** (Long green / Short red / Stand aside amber).
  - **Factor breakdown**: one row per factor with its contribution bar + detail; a **regime line**
    showing regime, VIX, and the multiplier applied.
  - **EV readout**: expected value in R + the forecast expected move.
  - **Position sizing calculator** (client-side, reactive):
    - Inputs: account size + max risk-per-trade % (defaults $100k / 1%), persisted in `localStorage`
      (keys e.g. `decision.accountSize`, `decision.maxRiskPct`).
    - `riskPct = maxRiskPct · conviction/10`; `riskDollars = equity·riskPct/100`;
      `stopDist = |entry − stop|` (entry = optimal_entry or current price; stop = stop_loss);
      `shares = floor(riskDollars / stopDist)`; `positionDollars = shares·entry`;
      cap `positionDollars ≤ equity` (no leverage) and recompute shares if capped (note it);
      show **shares, $ position, % of equity, $ at risk, R:R**.
    - If no valid stop or `stopDist ≤ 0`: show "No valid stop — size manually", do not invent a number.
  - Rendered near the TOP of the Analysis page (above the chart/verdict area), full width.

## Edge cases
- Missing signals/score/forecast/tunnel: factors that lack data are dropped and weights
  renormalized over available factors (same pattern as the tunnel drift blend).
- Regime fetch fails: multiplier 1.0, regime label "Unknown".
- No stop loss: conviction still shown; sizing shows the manual-size message.
- Conflicting signals: low `|raw|` → "Stand aside" with rationale naming the conflict.

## Testing
- pytest `tests/test_decision_engine.py`:
  - conviction monotonic in each factor (raising fundamentals raises conviction, etc.);
  - regime multiplier dampens the aligned direction (long conviction lower in Danger);
  - direction thresholds (Long/Short/Stand aside);
  - weight renormalization when a factor is missing;
  - EV_R sign/with-and-without stop;
  - bounds [0,10].
- Sizing math: a small pytest or inline TS reasoning — since sizing is client-side TS, cover the
  formula logic with a pure helper `computeSizing(...)` in a `frontend/src/lib/sizing.ts` module so
  it is unit-testable (and the panel imports it). (Backend pytest covers conviction; the sizing
  helper is pure TS — verify via build + manual UI per the repo norm, plus keep the helper pure.)

## Deployment / constraints
- Use python3; never bind/disturb :8001 (use :8011 for test server); commit only on a branch;
  frontend rebuild + service restart per the established deploy (see memory: backend has no --reload).
