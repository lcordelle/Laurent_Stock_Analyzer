# Decision Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Decision Panel that fuses the analyzer's existing signals into a 0–10 conviction call (with direction + transparent factor breakdown), conditions it on the live market regime, and turns it into a concrete risk-based position size.

**Architecture:** A pure, unit-tested backend conviction engine (`utils/decision_engine.py`) consumes the already-computed score/signals/forecast/tunnel + a cached market regime and returns a `decision` object on the analyze response. Position sizing is a pure client-side TS helper (`frontend/src/lib/sizing.ts`) driven by user-entered account inputs in a new `DecisionPanel.tsx`.

**Tech Stack:** Python (pure functions + pytest), FastAPI/Pydantic, React + TypeScript + Vite.

## Global Constraints
- Use `python3`. Run pytest from repo/worktree root.
- NEVER bind/disturb port 8001 (production); use port 8011 for any test server.
- Backend conviction engine is PURE (no I/O, no yfinance) — regime is passed in.
- Decision build in the route must be wrapped so it can never 500 the analysis (mirror the valuation_tunnel try/except).
- Default conviction weights: Fundamentals 0.30, Technical 0.30, Trend 0.20, Valuation 0.20; renormalized over available factors.
- Regime multipliers (applied to the aligned direction): Risk-On 1.0, Neutral/Risk-Off 0.85/0.65, Danger 0.45, Unknown 1.0.
- Sizing is client-side and must never invent a number when there is no valid stop.
- Commit only on a feature branch; do not push or deploy as part of the plan.

---

### Task 1: Conviction engine (pure) + regime cache

**Files:**
- Create: `utils/decision_engine.py`
- Modify: `utils/market_breadth.py` (add a ~5-min TTL cache wrapper)
- Test: `tests/test_decision_engine.py`

**Interfaces:**
- Produces: `compute_conviction(score, signals, forecast, tunnel, regime, weights=None) -> dict` with keys `conviction` (float 0–10), `direction` ("Long"|"Short"|"Stand aside"), `factors` (list of `{label, subscore, weight, contribution, detail}`), `regime` (`{label, vix, multiplier}`), `expected_value_r` (float|None), `rationale` (str).
- Produces: `get_market_regime_cached() -> dict` in `market_breadth.py` (same shape as `get_market_regime()`).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_decision_engine.py
from utils.decision_engine import compute_conviction

BULL_SIG = {"signal": "STRONG BUY", "confidence": 80, "signal_quality": "PRIME",
            "trend_strength": "STRONG UPTREND", "adx": 30,
            "optimal_entry": 100.0, "stop_loss": 90.0, "tp1": 120.0, "risk_reward": 2.0}
FCAST_UP = {"forecast_change_pct": 8.0, "trend": "Bullish"}
TUN = {"current_vs_fair_pct": -5.0}  # 5% below fair value (bullish)
RISK_ON = {"regime": "Risk-On", "vix": 14.0}
DANGER  = {"regime": "Danger", "vix": 40.0}


def test_strong_bull_is_long_high_conviction():
    d = compute_conviction(85, BULL_SIG, FCAST_UP, TUN, RISK_ON)
    assert d["direction"] == "Long"
    assert d["conviction"] >= 7.0
    assert 0 <= d["conviction"] <= 10


def test_regime_danger_dampens_long():
    on = compute_conviction(85, BULL_SIG, FCAST_UP, TUN, RISK_ON)["conviction"]
    dg = compute_conviction(85, BULL_SIG, FCAST_UP, TUN, DANGER)["conviction"]
    assert dg < on


def test_higher_fundamentals_raise_conviction():
    lo = compute_conviction(55, BULL_SIG, FCAST_UP, TUN, RISK_ON)["conviction"]
    hi = compute_conviction(95, BULL_SIG, FCAST_UP, TUN, RISK_ON)["conviction"]
    assert hi >= lo


def test_conflict_is_stand_aside():
    bear_sig = {**BULL_SIG, "signal": "SELL", "trend_strength": "WEAK DOWNTREND"}
    d = compute_conviction(50, bear_sig, {"forecast_change_pct": 0.5}, {"current_vs_fair_pct": 0.0}, RISK_ON)
    assert d["direction"] in ("Stand aside", "Short")


def test_weights_renormalize_when_factor_missing():
    # no forecast / tunnel -> valuation factor dropped, still bounded, still Long
    d = compute_conviction(85, BULL_SIG, None, None, RISK_ON)
    assert 0 <= d["conviction"] <= 10
    assert d["direction"] == "Long"


def test_ev_r_present_with_stop_absent_without():
    d = compute_conviction(85, BULL_SIG, FCAST_UP, TUN, RISK_ON)
    assert d["expected_value_r"] is not None
    no_stop = {**BULL_SIG, "stop_loss": None}
    d2 = compute_conviction(85, no_stop, FCAST_UP, TUN, RISK_ON)
    assert d2["expected_value_r"] is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd <root> && python3 -m pytest tests/test_decision_engine.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'utils.decision_engine'`

- [ ] **Step 3: Write the engine**

```python
# utils/decision_engine.py
"""Fuse existing per-stock signals + market regime into a conviction + sizing-ready decision."""
from typing import Optional

DEFAULT_WEIGHTS = {"Fundamentals": 0.30, "Technical": 0.30, "Trend": 0.20, "Valuation": 0.20}
REGIME_MULT = {"Risk-On": 1.0, "Neutral": 0.85, "Risk-Off": 0.65, "Danger": 0.45, "Unknown": 1.0}
_SIGNAL_MAP = {"STRONG BUY": 1.0, "BUY": 0.6, "HOLD": 0.0, "NEUTRAL": 0.0,
               "SELL": -0.6, "STRONG SELL": -1.0}
_QUALITY_MAP = {"PRIME": 1.0, "CONFIRMED": 0.75, "STANDARD": 0.5, "WEAK": 0.25}


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def _fundamentals(score) -> Optional[float]:
    if score is None:
        return None
    return _clamp((float(score) - 50.0) / 50.0, -1.0, 1.0)


def _technical(signals) -> Optional[float]:
    if not signals:
        return None
    sig = _SIGNAL_MAP.get((signals.get("signal") or "").upper())
    if sig is None:
        return None
    conf = (signals.get("confidence") or 50) / 100.0          # 0..1
    qual = _QUALITY_MAP.get((signals.get("signal_quality") or "STANDARD").upper(), 0.5)
    # scale the signed signal by how strong/clean it is
    return _clamp(sig * (0.5 + 0.5 * conf) * (0.5 + 0.5 * qual), -1.0, 1.0)


def _trend(signals) -> Optional[float]:
    if not signals:
        return None
    ts = (signals.get("trend_strength") or "").upper()
    if not ts:
        return None
    sign = 1.0 if "UP" in ts else -1.0 if "DOWN" in ts else 0.0
    mag = 1.0 if "STRONG" in ts else 0.4 if "WEAK" in ts else 0.6
    return _clamp(sign * mag, -1.0, 1.0)


def _valuation(forecast, tunnel) -> Optional[float]:
    parts = []
    if tunnel and tunnel.get("current_vs_fair_pct") is not None:
        # below fair value (negative %) is bullish -> invert sign
        parts.append(_clamp(-(tunnel["current_vs_fair_pct"]) / 15.0, -1.0, 1.0))
    if forecast and forecast.get("forecast_change_pct") is not None:
        chg = forecast["forecast_change_pct"]
        parts.append(_clamp(chg / 10.0, -1.0, 1.0))
    if not parts:
        return None
    return sum(parts) / len(parts)


def _expected_value_r(signals, raw, mult) -> Optional[float]:
    if not signals:
        return None
    entry = signals.get("optimal_entry")
    stop = signals.get("stop_loss")
    tp1 = signals.get("tp1")
    if entry is None or stop is None or tp1 is None:
        return None
    risk = abs(entry - stop)
    if risk <= 0:
        return None
    r = abs(tp1 - entry) / risk
    p = _clamp(0.5 + raw * mult * 0.4, 0.05, 0.95)
    return round(p * r - (1 - p) * 1.0, 2)


def compute_conviction(score, signals, forecast, tunnel, regime, weights=None) -> dict:
    weights = weights or DEFAULT_WEIGHTS
    subs = {
        "Fundamentals": _fundamentals(score),
        "Technical": _technical(signals),
        "Trend": _trend(signals),
        "Valuation": _valuation(forecast, tunnel),
    }
    details = {
        "Fundamentals": f"Score {score}" if score is not None else "no score",
        "Technical": f"{(signals or {}).get('signal','?')} / {(signals or {}).get('signal_quality','?')}",
        "Trend": (signals or {}).get("trend_strength") or "no trend",
        "Valuation": "fair-value & forecast",
    }
    avail = {k: v for k, v in subs.items() if v is not None}
    total_w = sum(weights[k] for k in avail) or 1.0
    raw = sum(subs[k] * weights[k] for k in avail) / total_w  # [-1,1]

    regime_label = (regime or {}).get("regime") or "Unknown"
    mult = REGIME_MULT.get(regime_label, 1.0)

    conviction = round(_clamp(abs(raw) * mult, 0.0, 1.0) * 10.0, 1)
    direction = "Long" if raw > 0.15 else "Short" if raw < -0.15 else "Stand aside"

    factors = [{
        "label": k,
        "subscore": round(subs[k], 3) if subs[k] is not None else None,
        "weight": weights[k],
        "contribution": round((subs[k] * weights[k] / total_w), 3) if subs[k] is not None else None,
        "detail": details[k],
    } for k in DEFAULT_WEIGHTS]

    ev_r = _expected_value_r(signals, raw, mult)
    rationale = (f"{direction} · conviction {conviction}/10 · regime {regime_label}"
                 f"{'' if mult == 1.0 else f' (×{mult})'}")

    return {
        "conviction": conviction,
        "direction": direction,
        "factors": factors,
        "regime": {"label": regime_label, "vix": (regime or {}).get("vix"), "multiplier": mult},
        "expected_value_r": ev_r,
        "rationale": rationale,
    }
```

Add the regime cache to `utils/market_breadth.py` (append near `get_market_regime`):

```python
import time as _time
_REGIME_CACHE = {"ts": 0.0, "data": None}
_REGIME_TTL = 300  # 5 minutes

def get_market_regime_cached() -> dict:
    now = _time.monotonic()
    if _REGIME_CACHE["data"] is not None and (now - _REGIME_CACHE["ts"]) < _REGIME_TTL:
        return _REGIME_CACHE["data"]
    data = get_market_regime()
    _REGIME_CACHE["ts"] = now
    _REGIME_CACHE["data"] = data
    return data
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd <root> && python3 -m pytest tests/test_decision_engine.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```bash
git add utils/decision_engine.py utils/market_breadth.py tests/test_decision_engine.py
git commit -m "feat: conviction decision engine (pure) + cached market regime"
```

---

### Task 2: Backend model + route wiring

**Files:**
- Modify: `api/models/responses.py` (add `Decision` + `DecisionFactor` models; add `decision` field to `FullStockAnalysis`)
- Modify: `api/routes/stocks.py` (import engine + cached regime; compute `current_vs_fair_pct`; build `decision`)

**Interfaces:**
- Consumes: `compute_conviction(...)` and `get_market_regime_cached()` from Task 1.
- Produces: `FullStockAnalysis.decision: Optional[Decision]` on the analyze endpoint.

- [ ] **Step 1: Add Pydantic models**

In `api/models/responses.py`, after the `ValuationTunnel` class add:

```python
class DecisionFactor(BaseModel):
    label: str
    subscore: Optional[float] = None
    weight: float
    contribution: Optional[float] = None
    detail: str


class DecisionRegime(BaseModel):
    label: str
    vix: Optional[float] = None
    multiplier: float


class Decision(BaseModel):
    conviction: float
    direction: str
    factors: list[DecisionFactor]
    regime: DecisionRegime
    expected_value_r: Optional[float] = None
    rationale: str
```

- [ ] **Step 2: Add the field to `FullStockAnalysis`**

In `api/models/responses.py`, directly after the `valuation_tunnel: Optional["ValuationTunnel"] = None` line add:

```python
    decision: Optional["Decision"] = None
```

- [ ] **Step 3: Import in the route**

In `api/routes/stocks.py`: add `Decision` to the `from api.models.responses import (...)` list, and near the other utils imports add:

```python
from utils.decision_engine import compute_conviction
from utils.market_breadth import get_market_regime_cached
```

- [ ] **Step 4: Build the decision before `return FullStockAnalysis(`**

In `api/routes/stocks.py`, just before the `return FullStockAnalysis(` (after the `valuation_tunnel` block), add:

```python
    decision = None
    try:
        sig_dict = ts_obj.model_dump() if (ts_obj := (locals().get("trading_signals_obj"))) else None
        # trading signals are built inline in the FullStockAnalysis(...) call; recompute a dict here:
    except Exception:
        decision = None
```

Note for the implementer: the analyze route builds `trading_signals=...` inline. To feed the
engine, capture that object into a local FIRST. Refactor the inline
`trading_signals=_compute_trading_signals(...)` so the result is assigned to a local
`trading_signals_obj = _compute_trading_signals(...)` ABOVE the return, pass
`trading_signals=trading_signals_obj` in the constructor, and build the decision from it:

```python
    # (above the return) capture trading signals once
    trading_signals_obj = _compute_trading_signals(...same args as before...) \
        if raw_metrics and raw_metrics.get("Current Price") else TradingSignals()

    decision = None
    try:
        sig = trading_signals_obj.model_dump()
        cur = raw_metrics.get("Current Price") if raw_metrics else None
        cur_vs_fair = None
        if valuation_tunnel is not None and cur:
            mids = [m for m in valuation_tunnel.hist_mid if m is not None]
            if mids:
                cur_vs_fair = (cur / mids[-1] - 1.0) * 100.0
        dec = compute_conviction(
            score=(raw_score.get("total_score") if raw_score else None),
            signals=sig,
            forecast=raw_forecast,
            tunnel={"current_vs_fair_pct": cur_vs_fair} if cur_vs_fair is not None else None,
            regime=get_market_regime_cached(),
        )
        decision = Decision(**dec)
    except Exception as e:
        logger.debug("Decision build failed for %s: %s", ticker, e)
```

Then in the `FullStockAnalysis(` call use `trading_signals=trading_signals_obj` and add `decision=decision,`.

- [ ] **Step 5: Verify on the safe port (never 8001)**

```bash
cd <root> && python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8011 &
sleep 5
# login (NGROK_AUTH_USER/PASS in .env), then:
curl -s -X POST http://127.0.0.1:8011/api/analyze -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" -d '{"ticker":"AAPL","period":"1y"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin)['decision']; print(d['direction'], d['conviction'], d['regime']['label'], 'EV_R=', d['expected_value_r']); [print(' ', f['label'], f['contribution']) for f in d['factors']]"
kill %1
```
Expected: a direction, conviction 0–10, regime label, EV_R, and four factor contributions.

- [ ] **Step 6: Commit**

```bash
git add api/models/responses.py api/routes/stocks.py
git commit -m "feat: serve decision (conviction + regime) from analyze endpoint"
```

---

### Task 3: Frontend — sizing helper, types, DecisionPanel, wiring

**Files:**
- Create: `frontend/src/lib/sizing.ts`
- Create: `frontend/src/components/stocks/DecisionPanel.tsx`
- Modify: `frontend/src/lib/types.ts` (add `Decision`/`DecisionFactor` types + `decision?` on FullStockAnalysis)
- Modify: `frontend/src/pages/Analysis.tsx` (render `<DecisionPanel>` near the top)

**Interfaces:**
- Consumes: `data.decision` from Task 2; `data.trading_signals` (optimal_entry, stop_loss) and `data.metrics.current_price`.
- Produces: `computeSizing(input) -> SizingResult` (pure) and the `DecisionPanel` component.

- [ ] **Step 1: Pure sizing helper**

Create `frontend/src/lib/sizing.ts`:

```ts
export interface SizingInput {
  equity: number
  maxRiskPct: number      // e.g. 1 = 1%
  conviction: number      // 0..10
  entry: number | null
  stop: number | null
}
export interface SizingResult {
  ok: boolean
  reason?: string
  riskPct: number
  riskDollars: number
  shares: number
  positionDollars: number
  pctOfEquity: number
  capped: boolean
}

export function computeSizing(i: SizingInput): SizingResult {
  const base = { riskPct: 0, riskDollars: 0, shares: 0, positionDollars: 0, pctOfEquity: 0, capped: false }
  if (!i.equity || i.equity <= 0) return { ok: false, reason: 'Set account size', ...base }
  if (i.entry == null || i.stop == null) return { ok: false, reason: 'No valid stop — size manually', ...base }
  const stopDist = Math.abs(i.entry - i.stop)
  if (stopDist <= 0) return { ok: false, reason: 'No valid stop — size manually', ...base }
  const riskPct = i.maxRiskPct * (Math.max(0, Math.min(10, i.conviction)) / 10)
  const riskDollars = i.equity * (riskPct / 100)
  let shares = Math.floor(riskDollars / stopDist)
  let positionDollars = shares * i.entry
  let capped = false
  if (positionDollars > i.equity) {          // no leverage
    shares = Math.floor(i.equity / i.entry)
    positionDollars = shares * i.entry
    capped = true
  }
  return {
    ok: shares > 0,
    reason: shares > 0 ? undefined : 'Risk too small for one share',
    riskPct, riskDollars, shares, positionDollars,
    pctOfEquity: i.equity ? (positionDollars / i.equity) * 100 : 0,
    capped,
  }
}
```

- [ ] **Step 2: Add TS types**

In `frontend/src/lib/types.ts`, after the `ValuationTunnel` interface add:

```ts
export interface DecisionFactor {
  label: string; subscore: number | null; weight: number
  contribution: number | null; detail: string
}
export interface Decision {
  conviction: number
  direction: 'Long' | 'Short' | 'Stand aside'
  factors: DecisionFactor[]
  regime: { label: string; vix: number | null; multiplier: number }
  expected_value_r: number | null
  rationale: string
}
```

Add to the `FullStockAnalysis` interface (after `valuation_tunnel?`):

```ts
  decision?: Decision
```

- [ ] **Step 3: Build DecisionPanel.tsx**

Create `frontend/src/components/stocks/DecisionPanel.tsx`:

```tsx
import { useState } from 'react'
import type { Decision, OHLCVRow } from '../../lib/types'
import { computeSizing } from '../../lib/sizing'

interface Props {
  decision: Decision
  entry: number | null
  stop: number | null
  currentPrice: number | null
}

const DIR_COLOR: Record<string, string> = {
  'Long': '#00e676', 'Short': '#ff1744', 'Stand aside': '#ffab00',
}

function num(v: string, fallback: number): number {
  const n = parseFloat(v.replace(/[^0-9.]/g, ''))
  return isNaN(n) ? fallback : n
}

export default function DecisionPanel({ decision, entry, stop, currentPrice }: Props) {
  const [equity, setEquity] = useState<number>(() => num(localStorage.getItem('decision.accountSize') ?? '', 100000))
  const [maxRisk, setMaxRisk] = useState<number>(() => num(localStorage.getItem('decision.maxRiskPct') ?? '', 1))

  const saveEquity = (v: number) => { setEquity(v); localStorage.setItem('decision.accountSize', String(v)) }
  const saveRisk = (v: number) => { setMaxRisk(v); localStorage.setItem('decision.maxRiskPct', String(v)) }

  const eff = entry ?? currentPrice
  const sizing = computeSizing({ equity, maxRiskPct: maxRisk, conviction: decision.conviction, entry: eff, stop })
  const dirColor = DIR_COLOR[decision.direction] ?? '#94a3b8'
  const usd = (n: number) => `$${Math.round(n).toLocaleString()}`

  return (
    <div className="rounded-xl border p-5 flex flex-col gap-4"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: '#475569' }}>Decision</span>
          <span className="text-sm font-black px-3 py-1 rounded-lg"
            style={{ backgroundColor: dirColor + '22', color: dirColor }}>{decision.direction}</span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-black tabular-nums" style={{ color: dirColor }}>{decision.conviction.toFixed(1)}</span>
          <span className="text-xs" style={{ color: '#475569' }}>/ 10 conviction</span>
        </div>
      </div>

      <div className="text-xs" style={{ color: '#94a3b8' }}>{decision.rationale}</div>

      {/* Factor breakdown */}
      <div className="flex flex-col gap-1.5">
        {decision.factors.map(f => {
          const c = f.contribution ?? 0
          const pos = c >= 0
          return (
            <div key={f.label} className="flex items-center gap-2 text-xs">
              <span className="w-24 shrink-0" style={{ color: '#94a3b8' }}>{f.label}</span>
              <div className="flex-1 h-2 rounded-full relative" style={{ backgroundColor: 'rgba(255,255,255,0.05)' }}>
                <div className="absolute top-0 h-2 rounded-full"
                  style={{ left: '50%', width: `${Math.min(Math.abs(c) * 200, 50)}%`,
                    transform: pos ? 'none' : 'translateX(-100%)',
                    backgroundColor: f.subscore == null ? '#475569' : pos ? '#00e676' : '#ff1744' }} />
              </div>
              <span className="w-40 shrink-0 text-right" style={{ color: '#475569' }}>
                {f.subscore == null ? 'n/a' : f.detail}
              </span>
            </div>
          )
        })}
        <div className="flex items-center gap-2 text-xs mt-1">
          <span className="w-24 shrink-0" style={{ color: '#94a3b8' }}>Regime</span>
          <span style={{ color: '#cbd5e1' }}>
            {decision.regime.label}{decision.regime.vix != null ? ` · VIX ${decision.regime.vix}` : ''} · ×{decision.regime.multiplier}
          </span>
        </div>
        {decision.expected_value_r != null && (
          <div className="flex items-center gap-2 text-xs">
            <span className="w-24 shrink-0" style={{ color: '#94a3b8' }}>Expected value</span>
            <span style={{ color: decision.expected_value_r >= 0 ? '#00e676' : '#ff1744' }}>
              {decision.expected_value_r >= 0 ? '+' : ''}{decision.expected_value_r}R
            </span>
          </div>
        )}
      </div>

      {/* Position sizing */}
      <div className="border-t pt-3 mt-1" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
        <div className="flex items-center gap-3 flex-wrap mb-2">
          <label className="text-xs flex items-center gap-1" style={{ color: '#475569' }}>
            Account $
            <input type="text" defaultValue={String(equity)} onBlur={e => saveEquity(num(e.target.value, equity))}
              className="w-28 px-2 py-1 rounded text-xs tabular-nums"
              style={{ backgroundColor: '#0a0e1a', color: '#e2e8f0', border: '1px solid rgba(255,255,255,0.08)' }} />
          </label>
          <label className="text-xs flex items-center gap-1" style={{ color: '#475569' }}>
            Max risk %
            <input type="text" defaultValue={String(maxRisk)} onBlur={e => saveRisk(num(e.target.value, maxRisk))}
              className="w-16 px-2 py-1 rounded text-xs tabular-nums"
              style={{ backgroundColor: '#0a0e1a', color: '#e2e8f0', border: '1px solid rgba(255,255,255,0.08)' }} />
          </label>
        </div>
        {sizing.ok ? (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <SizeStat label="Shares" value={sizing.shares.toLocaleString()} />
            <SizeStat label="Position" value={usd(sizing.positionDollars)} sub={`${sizing.pctOfEquity.toFixed(1)}% of acct`} />
            <SizeStat label="At risk" value={usd(sizing.riskDollars)} sub={`${sizing.riskPct.toFixed(2)}% risk`} />
            <SizeStat label="Conv-scaled" value={`${(decision.conviction * 10).toFixed(0)}% of max`} sub={sizing.capped ? 'capped (no leverage)' : ''} />
          </div>
        ) : (
          <div className="text-xs" style={{ color: '#ffab00' }}>{sizing.reason}</div>
        )}
      </div>
    </div>
  )
}

function SizeStat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="flex flex-col px-3 py-2 rounded-lg" style={{ backgroundColor: '#0a0e1a' }}>
      <span className="text-xs uppercase tracking-wide" style={{ color: '#475569' }}>{label}</span>
      <span className="text-sm font-bold tabular-nums" style={{ color: '#e2e8f0' }}>{value}</span>
      {sub ? <span className="text-xs" style={{ color: '#475569' }}>{sub}</span> : null}
    </div>
  )
}
```
(Drop the unused `OHLCVRow` import if not needed.)

- [ ] **Step 4: Wire into Analysis.tsx**

Import and render the panel near the TOP of the analysis content (before the chart card), only when `data.decision` exists:

```tsx
import DecisionPanel from '../components/stocks/DecisionPanel'
// ...inside the render, near the top of the results section:
{data.decision && (
  <DecisionPanel
    decision={data.decision}
    entry={data.trading_signals?.optimal_entry ?? null}
    stop={data.trading_signals?.stop_loss ?? null}
    currentPrice={data.metrics?.current_price ?? data.ohlcv.at(-1)?.close ?? null}
  />
)}
```

- [ ] **Step 5: Build**

```bash
cd <root>/frontend && npm install && npm run build
```
Expected: `tsc -b && vite build` passes, 0 TS errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/lib/sizing.ts frontend/src/lib/types.ts frontend/src/components/stocks/DecisionPanel.tsx frontend/src/pages/Analysis.tsx
git commit -m "feat: Decision panel (conviction breakdown + regime + risk-based sizing)"
```

---

## Self-Review

**Spec coverage:**
- Conviction engine (fuse score/technical/trend/valuation, weights, renormalize) → Task 1. ✓
- Regime conditioning (multiplier, cached fetch) → Task 1 (`get_market_regime_cached`) + Task 2 wiring. ✓
- Factor breakdown + EV_R + direction + rationale → Task 1 return + Task 3 display. ✓
- `decision` on the analyze response → Task 2. ✓
- Risk-based, conviction-scaled, client-side sizing with account inputs + no-leverage cap + no-stop guard → Task 3 `sizing.ts` + panel. ✓
- localStorage persistence of account inputs → Task 3. ✓
- Panel near top of Analysis page → Task 3 Step 4. ✓
- Tests for conviction monotonicity, regime dampening, direction, renormalization, EV → Task 1 Step 1. ✓
- Never 500 (try/except), never bind 8001, pure engine → Global Constraints + Task 2. ✓

**Placeholder scan:** none — all steps carry real code/commands. The Task 2 Step 4 note explicitly instructs the required refactor (capture trading signals into a local) with full code.

**Type consistency:** `compute_conviction` return keys ↔ `Decision`/`DecisionFactor`/`DecisionRegime` (py) ↔ `Decision`/`DecisionFactor` (ts) ↔ panel accessors all align (conviction, direction, factors[].{label,subscore,weight,contribution,detail}, regime.{label,vix,multiplier}, expected_value_r, rationale). `computeSizing` `SizingInput`/`SizingResult` consistent between `sizing.ts` and the panel.
