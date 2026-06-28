# Valuation Tunnel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "blue tunnel" overlay to the candlestick chart showing a fair-value channel across history that projects forward as a widening forecast cone, with the price trend overlaid so a pro sees instantly whether price is above/below/inside fair value and where it's heading.

**Architecture:** Pure tunnel math lives in a new isolated module `utils/valuation_tunnel.py` (regression channel for history, drift±k·σ·√t GBM cone for the forecast, blended drift from analyst target + regression slope + mean-reversion + momentum). The FastAPI analyze endpoint computes it and returns a new `valuation_tunnel` object. The React chart (`lightweight-charts`) renders it as blue line series — historical solid, forecast dashed — extending the time axis into the future, behind a toggle chip.

**Tech Stack:** Python 3 / FastAPI / pandas / numpy (backend), pytest (math unit tests), React + TypeScript + Vite + lightweight-charts (frontend).

## Global Constraints

- Port **8001 is permanent** and runs the live production service via macOS LaunchAgent `com.virtualfusion.stock-analyzer` (public URL `https://laurent.ngrok.io`). NEVER bind to 8001, kill, or restart that process during development. Use port **8011** for any local test server.
- Use `python3`, not `python`.
- No hardcoded secrets — env vars / `config.py` only.
- Backend band/forecast arrays must align 1:1 with `ohlcv`, which is `hist.tail(252)`. Compute tunnel history from `hist.tail(252)`.
- Follow existing NaN-safety patterns (`_series_to_list`, NaN-safe JSON encoder already in the app).
- Frontend bands match the existing Bollinger pattern: `lightweight-charts` line series (no Area fill). Tunnel = blue line series.
- **Testing deviation (deliberate):** CLAUDE.md says "no automated tests; manual via UI." This plan adds pytest unit tests for the **pure math only** (`utils/valuation_tunnel.py`) because the math is pure, pytest 8.2.0 is already installed, and silent math errors here would mislead a trader. All frontend + integration verification stays manual per CLAUDE.md.

---

### Task 1: Pure tunnel math module + unit tests

**Files:**
- Create: `utils/valuation_tunnel.py`
- Create: `tests/__init__.py` (empty)
- Test: `tests/test_valuation_tunnel.py`

**Interfaces:**
- Produces: `build_valuation_tunnel(closes: list[float], dates: list[str], target_price: float | None = None, horizon_days: int = 30, k: float = 2.0, weights: dict | None = None) -> dict | None`
  returning keys: `hist_mid, hist_upper, hist_lower` (list[float], len == len(closes)), `future_dates` (list[str], len == horizon_days), `fc_mid, fc_upper, fc_lower` (list[float], len == horizon_days), `horizon_days` (int), `k` (float), `drift_annual` (float), `sigma_annual` (float). Returns `None` when `len(closes) < 30`.
- Also produces helpers used by tests: `log_regression_channel`, `forecast_cone`, `next_trading_days`, `blended_annual_drift`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_valuation_tunnel.py
import math
import numpy as np
from utils.valuation_tunnel import (
    build_valuation_tunnel,
    log_regression_channel,
    forecast_cone,
    next_trading_days,
    blended_annual_drift,
)


def _exp_series(n=120, daily=0.001, start=100.0):
    return [start * math.exp(daily * i) for i in range(n)]


def test_returns_none_on_insufficient_data():
    assert build_valuation_tunnel([100.0] * 10, ["2026-01-01"] * 10) is None


def test_regression_channel_brackets_price():
    closes = np.array(_exp_series())
    mid, upper, lower, slope, sigma = log_regression_channel(closes, k=2.0)
    assert len(mid) == len(closes)
    assert np.all(upper >= mid) and np.all(mid >= lower)
    assert slope > 0  # rising exponential -> positive log slope
    # near-perfect exponential -> tiny residual band
    assert (upper[-1] - lower[-1]) / mid[-1] < 0.05


def test_forecast_cone_widens_monotonically():
    mid, upper, lower = forecast_cone(p0=100.0, drift_annual=0.10,
                                      sigma_daily=0.02, horizon_days=30, k=2.0)
    assert len(mid) == len(upper) == len(lower) == 30
    widths = [u - l for u, l in zip(upper, lower)]
    assert all(b >= a for a, b in zip(widths, widths[1:]))  # non-decreasing
    assert mid[-1] > mid[0]  # positive drift


def test_next_trading_days_skips_weekends():
    days = next_trading_days("2026-06-26", 5)  # Fri 2026-06-26
    assert days == ["2026-06-29", "2026-06-30", "2026-07-01",
                    "2026-07-02", "2026-07-03"]


def test_blended_drift_clamps():
    closes = _exp_series()
    d = blended_annual_drift(closes, target_price=10_000.0, mid_last=closes[-1],
                             reg_slope_daily=0.5)  # absurd inputs
    assert -0.5 <= d <= 0.5


def test_build_shapes_and_keys():
    closes = _exp_series(120)
    dates = next_trading_days("2026-01-01", 120)
    out = build_valuation_tunnel(closes, dates, target_price=closes[-1] * 1.1)
    assert out is not None
    for key in ("hist_mid", "hist_upper", "hist_lower"):
        assert len(out[key]) == len(closes)
    for key in ("fc_mid", "fc_upper", "fc_lower", "future_dates"):
        assert len(out[key]) == 30
    assert out["horizon_days"] == 30 and out["k"] == 2.0
    assert "drift_annual" in out and "sigma_annual" in out
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/laurentcordelle/Projects/VirtualFusion_Stock_Analyzer && python3 -m pytest tests/test_valuation_tunnel.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'utils.valuation_tunnel'`

- [ ] **Step 3: Write the module**

```python
# utils/valuation_tunnel.py
"""Valuation Tunnel: regression fair-value channel (history) + GBM forecast cone."""
import math
from datetime import datetime, timedelta
from typing import Optional

import numpy as np

DEFAULT_WEIGHTS = {"analyst": 0.35, "regression": 0.30,
                   "mean_reversion": 0.20, "momentum": 0.15}
DRIFT_CLAMP = 0.5     # ±50% annual drift cap
BAND_CLAMP = 0.6      # cone half-width capped at ±60% of price


def log_regression_channel(closes: np.ndarray, k: float = 2.0):
    """Least-squares line on log(price); band = line ± k·std(residuals)."""
    n = len(closes)
    x = np.arange(n, dtype=float)
    y = np.log(closes)
    slope, intercept = np.polyfit(x, y, 1)
    fit = slope * x + intercept
    resid = y - fit
    sigma = float(resid.std(ddof=1)) if n > 2 else 0.0
    mid = np.exp(fit)
    upper = np.exp(fit + k * sigma)
    lower = np.exp(fit - k * sigma)
    return mid, upper, lower, float(slope), sigma


def daily_sigma(closes: np.ndarray) -> float:
    lr = np.diff(np.log(closes))
    return float(lr.std(ddof=1)) if len(lr) > 1 else 0.0


def blended_annual_drift(closes, target_price, mid_last, reg_slope_daily,
                         weights=None) -> float:
    """Weighted annual drift from available signals, renormalized + clamped."""
    weights = weights or DEFAULT_WEIGHTS
    current = closes[-1]
    comps, used_w = {}, {}

    if target_price and current and target_price > 0:
        comps["analyst"] = target_price / current - 1.0
        used_w["analyst"] = weights["analyst"]

    comps["regression"] = math.exp(reg_slope_daily * 252) - 1.0
    used_w["regression"] = weights["regression"]

    if mid_last and current:
        comps["mean_reversion"] = -(current / mid_last - 1.0)
        used_w["mean_reversion"] = weights["mean_reversion"]

    if len(closes) >= 21 and closes[-21] > 0:
        m = closes[-1] / closes[-21] - 1.0
        comps["momentum"] = m * (252 / 20)
        used_w["momentum"] = weights["momentum"]

    total_w = sum(used_w.values()) or 1.0
    drift = sum(comps[k] * used_w[k] for k in comps) / total_w
    return max(-DRIFT_CLAMP, min(DRIFT_CLAMP, drift))


def forecast_cone(p0, drift_annual, sigma_daily, horizon_days, k=2.0):
    mid, upper, lower = [], [], []
    for t in range(1, horizon_days + 1):
        center = p0 * (1 + drift_annual * t / 252.0)
        band = min(k * sigma_daily * math.sqrt(t), BAND_CLAMP)
        mid.append(center)
        upper.append(center * (1 + band))
        lower.append(center * (1 - band))
    return mid, upper, lower


def next_trading_days(last_date_str: str, n: int) -> list[str]:
    d = datetime.strptime(last_date_str[:10], "%Y-%m-%d")
    out: list[str] = []
    while len(out) < n:
        d += timedelta(days=1)
        if d.weekday() < 5:  # Mon-Fri (holidays ignored)
            out.append(d.strftime("%Y-%m-%d"))
    return out


def build_valuation_tunnel(closes, dates, target_price: Optional[float] = None,
                           horizon_days: int = 30, k: float = 2.0,
                           weights=None) -> Optional[dict]:
    if closes is None or len(closes) < 30:
        return None
    arr = np.asarray(closes, dtype=float)
    if np.any(arr <= 0) or np.any(np.isnan(arr)):
        return None

    mid, upper, lower, slope, _ = log_regression_channel(arr, k=k)
    sig_d = daily_sigma(arr)
    drift = blended_annual_drift(arr, target_price, float(mid[-1]), slope, weights)
    p0 = float(arr[-1])
    fc_mid, fc_up, fc_lo = forecast_cone(p0, drift, sig_d, horizon_days, k)
    future = next_trading_days(dates[-1], horizon_days)

    return {
        "hist_mid": [float(v) for v in mid],
        "hist_upper": [float(v) for v in upper],
        "hist_lower": [float(v) for v in lower],
        "future_dates": future,
        "fc_mid": fc_mid,
        "fc_upper": fc_up,
        "fc_lower": fc_lo,
        "horizon_days": horizon_days,
        "k": k,
        "drift_annual": drift,
        "sigma_annual": sig_d * math.sqrt(252),
    }
```

Also create empty `tests/__init__.py`:

```python
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/laurentcordelle/Projects/VirtualFusion_Stock_Analyzer && python3 -m pytest tests/test_valuation_tunnel.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit** (only if the user has approved committing — see Execution Handoff)

```bash
git add utils/valuation_tunnel.py tests/__init__.py tests/test_valuation_tunnel.py
git commit -m "feat: valuation tunnel math (regression channel + forecast cone)"
```

---

### Task 2: Backend response model + route wiring

**Files:**
- Modify: `api/models/responses.py` (add `ValuationTunnel`; add field on `FullStockAnalysis` near line 166)
- Modify: `api/routes/stocks.py` (import model + builder; build tunnel; pass to `FullStockAnalysis`)

**Interfaces:**
- Consumes: `build_valuation_tunnel(...)` from Task 1.
- Produces: `FullStockAnalysis.valuation_tunnel: Optional[ValuationTunnel]` on the analyze endpoint JSON.

- [ ] **Step 1: Add the Pydantic model**

In `api/models/responses.py`, immediately after the `IndicatorData` class (it ends before line ~75), add:

```python
class ValuationTunnel(BaseModel):
    hist_mid: list[Optional[float]]
    hist_upper: list[Optional[float]]
    hist_lower: list[Optional[float]]
    future_dates: list[str]
    fc_mid: list[float]
    fc_upper: list[float]
    fc_lower: list[float]
    horizon_days: int
    k: float
    drift_annual: float
    sigma_annual: float
```

- [ ] **Step 2: Add the field to `FullStockAnalysis`**

In `api/models/responses.py`, find (line ~166):

```python
    indicators: Optional[IndicatorData] = None
```

Add directly below it:

```python
    valuation_tunnel: Optional["ValuationTunnel"] = None
```

- [ ] **Step 3: Import the model and builder in the route**

In `api/routes/stocks.py`, the model import block starts at line 15 with `IndicatorData, TradingSignals, ...`. Add `ValuationTunnel` to that import list. Then add a new import near the other `utils` imports at the top of the file:

```python
from utils.valuation_tunnel import build_valuation_tunnel
```

- [ ] **Step 4: Build the tunnel in the analyze endpoint**

In `api/routes/stocks.py`, just before the `return FullStockAnalysis(` (around line 757), add:

```python
    valuation_tunnel = None
    try:
        if hist is not None and len(hist) >= 30:
            h = hist.tail(252)
            tun = build_valuation_tunnel(
                closes=[float(c) for c in h["Close"].tolist()],
                dates=[
                    idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]
                    for idx in h.index
                ],
                target_price=raw_metrics.get("Target Price") if raw_metrics else None,
            )
            if tun:
                valuation_tunnel = ValuationTunnel(**tun)
    except Exception as e:
        logger.debug("Valuation tunnel failed for %s: %s", ticker, e)
```

Then inside the `FullStockAnalysis(` call, directly after the `indicators=...` line (line 760), add:

```python
        valuation_tunnel=valuation_tunnel,
```

- [ ] **Step 5: Verify on the safe test port (never 8001)**

Start a throwaway server on **8011** and curl it (do NOT touch 8001):

```bash
cd /Users/laurentcordelle/Projects/VirtualFusion_Stock_Analyzer
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8011 &
sleep 4
curl -s "http://127.0.0.1:8011/api/stocks/AAPL/analysis?period=1y" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); t=d.get('valuation_tunnel'); print('keys:', list(t.keys()) if t else None); print('hist_mid len:', len(t['hist_mid']) if t else 0, 'fc len:', len(t['fc_mid']) if t else 0, 'future[0]:', t['future_dates'][0] if t else None)"
kill %1
```

(The exact analysis route path may differ; confirm with `grep -n '@router' api/routes/stocks.py`. Use whatever path the analyze endpoint registers.)
Expected: prints the 11 tunnel keys, `hist_mid len: <=252`, `fc len: 30`, and a future date after today.

- [ ] **Step 6: Commit** (user-gated)

```bash
git add api/models/responses.py api/routes/stocks.py
git commit -m "feat: serve valuation_tunnel from analyze endpoint"
```

---

### Task 3: Frontend type + chart rendering + toggle

**Files:**
- Modify: `frontend/src/lib/types.ts` (add `ValuationTunnel`; add field on `FullStockAnalysis`)
- Modify: `frontend/src/pages/Analysis.tsx:825-833` (pass the prop)
- Modify: `frontend/src/components/charts/CandlestickChart.tsx` (prop, state, render, toggle, effect dep)

**Interfaces:**
- Consumes: `data.valuation_tunnel` from Task 2.
- Produces: blue tunnel overlay on the main chart, toggled by a "TUN" chip, default ON.

- [ ] **Step 1: Add the TypeScript type**

In `frontend/src/lib/types.ts`, after the `IndicatorData` interface (ends line 34), add:

```ts
export interface ValuationTunnel {
  hist_mid: (number|null)[]; hist_upper: (number|null)[]; hist_lower: (number|null)[]
  future_dates: string[]
  fc_mid: number[]; fc_upper: number[]; fc_lower: number[]
  horizon_days: number; k: number; drift_annual: number; sigma_annual: number
}
```

Then in the `FullStockAnalysis` interface, after the `forecast?: ForecastResult; indicators?: IndicatorData` line (line 79), add:

```ts
  valuation_tunnel?: ValuationTunnel
```

- [ ] **Step 2: Pass the prop at the call site**

In `frontend/src/pages/Analysis.tsx`, in the `<CandlestickChart ... />` block (line 825), add a prop after `indicators={data.indicators}`:

```tsx
                    valuationTunnel={data.valuation_tunnel}
```

- [ ] **Step 3: Extend the chart's Props + signature + state**

In `frontend/src/components/charts/CandlestickChart.tsx`:

3a. Add to the `import type` line (line 6) so it reads:
```tsx
import type { OHLCVRow, IndicatorData, FullStockAnalysis, EarningsDate, ValuationTunnel } from '../../lib/types'
```

3b. In the `Props` interface (after `indicators?: IndicatorData`, line 17) add:
```tsx
  valuationTunnel?: ValuationTunnel
```

3c. In the component destructure (line 140) add `valuationTunnel` to the params:
```tsx
export default function CandlestickChart({ ohlcv, indicators, valuationTunnel, tradingSignals, earningsDates, relativeStrength, patterns, period, onPeriodChange }: Props) {
```

3d. After the `showRS` state (line 149) add:
```tsx
  const [showTunnel, setShowTunnel] = useState(true)
```

- [ ] **Step 4: Render the tunnel as blue line series**

In `frontend/src/components/charts/CandlestickChart.tsx`, inside the `import('lightweight-charts').then(...)` block, directly after the Bollinger Bands block (ends line 353), add:

```tsx
      // Valuation Tunnel — fair-value channel (history) + forecast cone (dashed)
      if (showTunnel && valuationTunnel) {
        const vt = valuationTunnel
        const histLen = Math.min(vt.hist_mid.length, ohlcv.length)
        const offset = ohlcv.length - histLen   // align tail-252 arrays to ohlcv tail
        type LinePt = { time: import('lightweight-charts').Time; value: number }
        const mkHist = (arr: (number | null)[]): LinePt[] =>
          arr.slice(0, histLen).map((v, i) => ({
            time: ohlcv[offset + i].date.slice(0, 10) as import('lightweight-charts').Time,
            value: v as number,
          })).filter(d => d.value != null)
        const mkFc = (arr: number[]): LinePt[] =>
          arr.map((v, i) => ({ time: vt.future_dates[i] as import('lightweight-charts').Time, value: v }))

        const BLUE = '#3b82f6'
        const addLine = (color: string, width: 1 | 2, dashed: boolean, title: string) =>
          mainChart.addLineSeries({
            color, lineWidth: width,
            lineStyle: dashed ? LineStyle.Dashed : LineStyle.Solid,
            title, lastValueVisible: false, priceLineVisible: false,
          })

        // historical channel (solid, faint edges + brighter mid)
        addLine(BLUE + '40', 1, false, 'Tunnel Upper').setData(mkHist(vt.hist_upper))
        addLine(BLUE + '40', 1, false, 'Tunnel Lower').setData(mkHist(vt.hist_lower))
        addLine(BLUE + '99', 1, false, 'Fair Value').setData(mkHist(vt.hist_mid))
        // forecast cone (dashed, continues into the future)
        addLine(BLUE + '66', 1, true, 'Forecast Upper').setData(mkFc(vt.fc_upper))
        addLine(BLUE + '66', 1, true, 'Forecast Lower').setData(mkFc(vt.fc_lower))
        addLine(BLUE + 'cc', 2, true, 'Forecast').setData(mkFc(vt.fc_mid))

        // "now" handoff marker on the last real candle
        const lastT = ohlcv[ohlcv.length - 1].date.slice(0, 10) as import('lightweight-charts').Time
        candleSeries.setMarkers([
          ...(candleSeries as unknown as { markers?: () => unknown[] }).markers?.() ?? [],
        ] as never)
        mainChart.addLineSeries({ color: '#64748b', lineWidth: 1, lineStyle: LineStyle.Dotted, lastValueVisible: false, priceLineVisible: false, title: 'now' })
          .setData([{ time: lastT, value: ohlcv[ohlcv.length - 1].close }])
      }
```

Note: lightweight-charts has no native vertical line; the solid→dashed transition at `future_dates[0]` is the visual handoff. Keep the implementation to the line series above; do not attempt a custom vertical-line plugin.

- [ ] **Step 5: Add `showTunnel` to the effect dependency array**

In `frontend/src/components/charts/CandlestickChart.tsx`, line 508, change:

```tsx
  }, [ohlcv, indicators, tradingSignals, earningsDates, relativeStrength, patterns, showRS])
```
to:
```tsx
  }, [ohlcv, indicators, valuationTunnel, tradingSignals, earningsDates, relativeStrength, patterns, showRS, showTunnel])
```

- [ ] **Step 6: Add the toggle chip**

In `frontend/src/components/charts/CandlestickChart.tsx`, in the controls block, directly after the RS `<button>` (closing tag at line ~577) and before the closing `</div>`, add:

```tsx
          <button
            onClick={() => setShowTunnel(s => !s)}
            className="px-2.5 py-1 rounded text-xs font-semibold transition-colors"
            style={{
              backgroundColor: showTunnel ? '#3b82f6' : 'transparent',
              color: showTunnel ? '#0a0e1a' : '#475569',
            }}
          >
            TUN
          </button>
```

- [ ] **Step 7: Typecheck + build**

Run:
```bash
cd /Users/laurentcordelle/Projects/VirtualFusion_Stock_Analyzer/frontend && npm run build
```
Expected: build succeeds, no TypeScript errors. (If `tsc` flags the markers re-set line, simplify Step 4's handoff marker to only the dotted line-series `setData` and drop the `candleSeries.setMarkers` re-set — markers are already set earlier in the effect.)

- [ ] **Step 8: Manual UI verification (per CLAUDE.md)**

Point the Vite dev proxy at the safe test backend and dogfood (do NOT use 8001):
```bash
cd /Users/laurentcordelle/Projects/VirtualFusion_Stock_Analyzer
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8011 &
# temporarily set the vite proxy target to http://127.0.0.1:8011 (frontend/vite.config.ts),
# then:
cd frontend && npm run dev
```
Open the dev URL, load a ticker (e.g. AAPL), confirm: blue channel hugs price across history, dashed cone fans out to the right past the last candle, "TUN" chip toggles it on/off. Revert the vite.config proxy change and `kill %1` afterwards.
Use the `/browse` skill to capture a before/after screenshot if available.

- [ ] **Step 9: Commit** (user-gated)

```bash
git add frontend/src/lib/types.ts frontend/src/pages/Analysis.tsx frontend/src/components/charts/CandlestickChart.tsx
git commit -m "feat: render valuation tunnel overlay with toggle"
```

---

### Task 4: Production cutover (USER-GATED — touches the permanent service)

**Files:** none (operational).

- [ ] **Step 1: Build the production bundle**

```bash
cd /Users/laurentcordelle/Projects/VirtualFusion_Stock_Analyzer/frontend && npm run build
```
This writes `frontend/dist/`, which FastAPI serves in prod.

- [ ] **Step 2: Confirm with the user before reloading the live service**

The backend changes only take effect when the `com.virtualfusion.stock-analyzer` LaunchAgent process reloads. Ask the user whether/when to reload it. Do NOT kill or restart port 8001 autonomously. The app's existing stale-bundle no-cache logic will serve the new frontend on next load once the backend is current.

- [ ] **Step 3: Post-cutover smoke check**

After the user confirms the reload, load `https://laurent.ngrok.io`, open a ticker, and verify the tunnel renders against the live service.

---

## Self-Review

**Spec coverage:**
- Historical regression channel → Task 1 `log_regression_channel`, rendered Task 3 Step 4. ✓
- Forecast drift±σ·√t cone, widening → Task 1 `forecast_cone` (test asserts monotonic widening). ✓
- Upgraded blended drift (analyst/regression/mean-reversion/momentum, renormalized, clamped) → Task 1 `blended_annual_drift` + test. ✓
- Data contract (`valuation_tunnel` object, aligned hist arrays + future-dated arrays) → Task 2 model + Task 1 return. ✓
- Future-row axis extension → Task 3 Step 4 `mkFc` uses `future_dates` as lightweight-charts times. ✓
- Toggle, default on → Task 3 Steps 3d/6. ✓
- "today" handoff → solid→dashed transition + dotted marker, Task 3 Step 4. ✓
- Edge cases (insufficient history, NaN, clamps) → Task 1 guards + Task 2 try/except. ✓
- Ops: never touch 8001, rebuild frontend, user-gated reload → Global Constraints + Task 4. ✓
- Tests for drift + tunnel geometry → Task 1 Step 1. ✓

**Placeholder scan:** No TBD/TODO; all steps carry real code or exact commands. ✓

**Type consistency:** `build_valuation_tunnel` return keys ↔ `ValuationTunnel` (py) ↔ `ValuationTunnel` (ts) ↔ chart `vt.*` accessors all use the same 11 names. `valuation_tunnel` (snake) on the wire/models, `valuationTunnel` (camel) as the React prop. ✓
