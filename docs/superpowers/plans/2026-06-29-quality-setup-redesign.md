# Quality × Setup Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the single misleading conviction number with two honest axes — QUALITY (VF score + grade) and SETUP (ex-fundamentals timing conviction, shown as a calibration percentile + band) — plus an explanatory "Read" line.

**Architecture:** Setup = `compute_conviction(score=None,…)` (drops fundamentals → matches calibration). The batch additionally emits the conviction distribution; the API maps the live setup to a percentile/band and composes a Read sentence. The Decision response becomes nested {quality, setup, read}; the panel renders two axes.

**Tech Stack:** Python (pure + pytest), pandas/numpy, FastAPI/Pydantic, React/TS.

## Global Constraints
- python3, py3.9-safe (no `X | None` unions in .py — use Optional).
- NEVER bind/disturb port 8001; use port 8011 for any test server.
- Setup conviction reuses `compute_conviction(score=None, …)`; do NOT reimplement conviction math.
- Band cutoffs by percentile: Weak <50, Fair 50–80, Strong 80–95, Prime ≥95.
- Quality grade: A ≥80, B 65–79, C 50–64, D 35–49, F <35.
- Setup-driver breakdown excludes Fundamentals (that's the Quality axis).
- Degrade gracefully: no calibration table → percentile/band/hit None, never crash/500.
- Commit only on this branch (`feature/conviction-calibration`); regenerate `data/calibration.json`.

---

### Task 1: Calibration percentile + band (pure) + tests

**Files:** Modify `utils/calibration.py`; Test `tests/test_calibration.py`

**Interfaces — Produces:**
- `conviction_percentiles(observations: list) -> list[dict]` → `[{"p": int, "value": float}, …]` for p in 0,5,…,100 over directional observations' conviction values (empty list if none).
- `percentile_of(breakpoints: list, conviction: float) -> Optional[float]` → interpolated percentile [0,100], None if breakpoints empty.
- `band_for(percentile: Optional[float]) -> Optional[str]` → "Weak"/"Fair"/"Strong"/"Prime" or None.

- [ ] **Step 1: Write failing tests**

```python
# append to tests/test_calibration.py
from utils.calibration import conviction_percentiles, percentile_of, band_for


def test_conviction_percentiles_span_and_monotonic():
    obs = [{"conviction": float(i % 11), "direction": "Long", "fwd_return": 0.01} for i in range(500)]
    bp = conviction_percentiles(obs)
    assert bp[0]["p"] == 0 and bp[-1]["p"] == 100
    vals = [b["value"] for b in bp]
    assert all(b >= a for a, b in zip(vals, vals[1:]))  # non-decreasing


def test_percentile_of_interpolates_and_clamps():
    obs = [{"conviction": float(i) / 100 * 10, "direction": "Long", "fwd_return": 0.0} for i in range(101)]
    bp = conviction_percentiles(obs)
    assert abs(percentile_of(bp, 5.0) - 50) < 12      # mid value ~mid percentile
    assert percentile_of(bp, -1) == 0.0
    assert percentile_of(bp, 99) == 100.0
    assert percentile_of([], 5.0) is None


def test_band_for_cutoffs():
    assert band_for(49) == "Weak"
    assert band_for(50) == "Fair"
    assert band_for(80) == "Strong"
    assert band_for(95) == "Prime"
    assert band_for(None) is None
```

- [ ] **Step 2: Run → fail** — `cd <root> && python3 -m pytest tests/test_calibration.py -k "percentile or band" -v` → ImportError.

- [ ] **Step 3: Implement (append to `utils/calibration.py`)**

```python
def conviction_percentiles(observations: list) -> list:
    vals = sorted(o["conviction"] for o in observations if o["direction"] in ("Long", "Short"))
    if not vals:
        return []
    out = []
    for p in range(0, 101, 5):
        idx = int(round((p / 100.0) * (len(vals) - 1)))
        out.append({"p": p, "value": round(float(vals[idx]), 4)})
    return out


def percentile_of(breakpoints: list, conviction: float) -> Optional[float]:
    if not breakpoints:
        return None
    c = float(conviction)
    if c <= breakpoints[0]["value"]:
        return 0.0
    if c >= breakpoints[-1]["value"]:
        return 100.0
    for i in range(1, len(breakpoints)):
        lo, hi = breakpoints[i - 1], breakpoints[i]
        if c <= hi["value"]:
            span = hi["value"] - lo["value"]
            frac = 0.0 if span <= 0 else (c - lo["value"]) / span
            return round(lo["p"] + frac * (hi["p"] - lo["p"]), 1)
    return 100.0


def band_for(percentile: Optional[float]) -> Optional[str]:
    if percentile is None:
        return None
    if percentile < 50:
        return "Weak"
    if percentile < 80:
        return "Fair"
    if percentile < 95:
        return "Strong"
    return "Prime"
```

- [ ] **Step 4: Run → pass.** **Step 5: Commit** `git add utils/calibration.py tests/test_calibration.py && git commit -m "feat: calibration percentile + band helpers"`

---

### Task 2: Quality grade + Read line (pure) + tests

**Files:** Modify `utils/decision_engine.py`; Test `tests/test_decision_engine.py`

**Interfaces — Produces:**
- `quality_grade(score: Optional[float]) -> Optional[str]` (A/B/C/D/F or None)
- `read_line(grade: Optional[str], setup_band: Optional[str], direction: str) -> str`

- [ ] **Step 1: Write failing tests**

```python
# append to tests/test_decision_engine.py
from utils.decision_engine import quality_grade, read_line


def test_quality_grade_cutoffs():
    assert quality_grade(85) == "A"
    assert quality_grade(70) == "B"
    assert quality_grade(55) == "C"
    assert quality_grade(40) == "D"
    assert quality_grade(20) == "F"
    assert quality_grade(None) is None


def test_read_line_quality_strong_setup_weak():
    s = read_line("A", "Weak", "Long")
    assert "watchlist" in s.lower() or "wait" in s.lower()
    assert "compan" in s.lower() or "quality" in s.lower()


def test_read_line_aligned_strong():
    s = read_line("A", "Prime", "Long")
    assert "buy" in s.lower() or "align" in s.lower() or "strong" in s.lower()


def test_read_line_low_quality():
    s = read_line("F", "Strong", "Long")
    assert "weak" in s.lower() or "poor" in s.lower() or "caution" in s.lower()
```

- [ ] **Step 2: Run → fail.**

- [ ] **Step 3: Implement (append to `utils/decision_engine.py`)**

```python
def quality_grade(score) -> Optional[str]:
    if score is None:
        return None
    s = float(score)
    if s >= 80:
        return "A"
    if s >= 65:
        return "B"
    if s >= 50:
        return "C"
    if s >= 35:
        return "D"
    return "F"


def read_line(grade: Optional[str], setup_band: Optional[str], direction: str) -> str:
    q_strong = grade in ("A", "B")
    q_weak = grade in ("D", "F")
    s_good = setup_band in ("Strong", "Prime")
    s_poor = setup_band in ("Weak", "Fair")
    if grade is None or setup_band is None:
        return f"{direction} setup; full read needs both quality and calibration data."
    if q_strong and s_good:
        return f"High-quality company and a strong {direction.lower()} setup — the two align."
    if q_strong and s_poor:
        return ("High-quality company, but a weak entry right now — "
                "watchlist candidate, not a buy here.")
    if q_weak and s_good:
        return ("Strong setup on a weak-quality company — a trade, not an investment; "
                "keep size and stops tight.")
    if q_weak and s_poor:
        return "Weak on both quality and setup — little here; likely avoid."
    # mixed quality (C)
    if s_good:
        return f"Average quality with a strong {direction.lower()} setup — a timing trade."
    return "Average quality and a soft setup — no edge; wait for a better entry."
```

- [ ] **Step 4: Run → pass.** **Step 5: Commit** `git add utils/decision_engine.py tests/test_decision_engine.py && git commit -m "feat: quality grade + read-line helpers"`

---

### Task 3: Batch emits conviction distribution + regenerate

**Files:** Modify `scripts/build_calibration.py`; regenerate `data/calibration.json`

**Interfaces — Consumes:** `conviction_percentiles` (Task 1).

- [ ] **Step 1: Add import + field.** In `scripts/build_calibration.py` change the calibration import to include `conviction_percentiles`, and add it to the table dict:

```python
from utils.calibration import (SP100, observations_for_history, bucketize,
                               conviction_percentiles, HORIZON_DAYS)
```
In the `table = {…}` dict, add:
```python
        "conviction_percentiles": conviction_percentiles(all_obs),
```

- [ ] **Step 2: Regenerate (network; cache makes it fast).**

Run: `cd <root> && python3 scripts/build_calibration.py`
Expected: rewrites `data/calibration.json` now containing a non-empty `conviction_percentiles` array. If yfinance is blocked, the per-ticker cache from the earlier full run is reused — verify:
`python3 -c "import json; d=json.load(open('data/calibration.json')); print('pcts', len(d.get('conviction_percentiles',[])), 'obs', d['total_obs'])"`
(Expect `pcts 21 obs ~120000`.)

- [ ] **Step 3: Commit** `git add scripts/build_calibration.py data/calibration.json && git commit -m "feat: calibration emits conviction distribution percentiles"`

---

### Task 4: Response model restructure (two-axis Decision)

**Files:** Modify `api/models/responses.py`

**Interfaces — Produces:** nested `Decision { quality, setup, read }` with `Quality` and `Setup` models; `DecisionFactor`/`DecisionRegime` reused; the standalone `Calibration` model and the `calibration` field on `FullStockAnalysis` are REMOVED (folded into `setup`).

- [ ] **Step 1: Replace the `Decision` model.** In `api/models/responses.py`, replace the existing `class Decision(BaseModel): …` block with:

```python
class Quality(BaseModel):
    score: Optional[int] = None
    grade: Optional[str] = None


class Setup(BaseModel):
    score: float
    direction: str
    percentile: Optional[float] = None
    band: Optional[str] = None
    hit_rate: Optional[float] = None
    avg_forward_return: Optional[float] = None
    n: Optional[int] = None
    low_sample: Optional[bool] = None
    as_of: Optional[str] = None
    horizon_days: Optional[int] = None
    expected_value_r: Optional[float] = None
    factors: list[DecisionFactor]
    regime: DecisionRegime


class Decision(BaseModel):
    quality: Quality
    setup: Setup
    read: str
```

- [ ] **Step 2: Remove the standalone `Calibration` model** (the `class Calibration(BaseModel): …` block) and the `calibration: Optional["Calibration"] = None` line on `FullStockAnalysis`. Keep `decision: Optional["Decision"] = None`.

- [ ] **Step 3: Verify import** — `cd <root> && python3 -c "import api.models.responses; print('ok')"` → `ok`.

- [ ] **Step 4: Commit** `git add api/models/responses.py && git commit -m "refactor: two-axis Decision model (quality+setup+read), fold calibration into setup"`

---

### Task 5: Route assembly (two-axis)

**Files:** Modify `api/routes/stocks.py`

**Interfaces — Consumes:** Tasks 1,2,4 + existing `compute_conviction`, `_calibration_table`, `cal_lookup`, `get_market_regime_cached`, `trading_signals_obj`, `raw_score`, `raw_forecast`, `cur_vs_fair`.

- [ ] **Step 1: Update imports.** Add to the calibration import: `from utils.calibration import load_table, lookup as cal_lookup, percentile_of, band_for`. Add to the decision-engine import: `from utils.decision_engine import compute_conviction, quality_grade, read_line`. Add `Quality, Setup` to the responses import; drop `Calibration` from it.

- [ ] **Step 2: Replace the decision + calibration build blocks** (the existing `dec = compute_conviction(score=…)` / `decision = Decision(**dec)` block AND the separate `calibration = Calibration(…)` block) with one two-axis assembly:

```python
    decision = None
    try:
        sig = trading_signals_obj.model_dump()
        setup_raw = compute_conviction(                       # SETUP = ex-fundamentals
            score=None, signals=sig, forecast=raw_forecast,
            tunnel={"current_vs_fair_pct": cur_vs_fair} if cur_vs_fair is not None else None,
            regime=get_market_regime_cached(),
        )
        q_score = int(raw_score["total_score"]) if raw_score and raw_score.get("total_score") is not None else None
        quality = Quality(score=q_score, grade=quality_grade(q_score))

        table = _calibration_table()
        pct = band = hit = avg = n = low = as_of = horizon = None
        if table and table.get("conviction_percentiles"):
            pct = percentile_of(table["conviction_percentiles"], setup_raw["conviction"])
            band = band_for(pct)
            as_of = table.get("generated_at"); horizon = table.get("horizon_days")
            b = cal_lookup(table.get("buckets", []), setup_raw["conviction"])
            if b and b.get("n"):
                hit, avg, n = b["hit_rate"], b["avg_forward_return"], b["n"]
                low = b["n"] < 100
        setup = Setup(
            score=setup_raw["conviction"], direction=setup_raw["direction"],
            percentile=pct, band=band, hit_rate=hit, avg_forward_return=avg, n=n,
            low_sample=low, as_of=as_of, horizon_days=horizon,
            expected_value_r=setup_raw["expected_value_r"],
            factors=setup_raw["factors"], regime=setup_raw["regime"],
        )
        decision = Decision(quality=quality, setup=setup,
                            read=read_line(quality.grade, band, setup_raw["direction"]))
    except Exception as e:
        logger.debug("Decision build failed for %s: %s", ticker, e)
        decision = None
```
Then in `FullStockAnalysis(`, keep `decision=decision,` and REMOVE the `calibration=calibration,` argument.

- [ ] **Step 3: Verify on :8011 (never 8001).**

```bash
cd <root> && python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8011 &
sleep 5
# login, then INTU:
curl -s -X POST http://127.0.0.1:8011/api/analyze -H "Content-Type: application/json" \
 -H "Authorization: Bearer $TOKEN" -d '{"ticker":"INTU","period":"1y"}' \
 | python3 -c "import sys,json; d=json.load(sys.stdin)['decision']; print('quality',d['quality']); print('setup band',d['setup']['band'],'pct',d['setup']['percentile'],'dir',d['setup']['direction'],'factors',[f['label'] for f in d['setup']['factors']]); print('read',d['read'])"
kill %1
```
Expected: quality `{score, grade:"A"|...}`, setup band/percentile/direction, factors = Technical/Trend/Valuation (NO "Fundamentals"), and a sensible Read line.

- [ ] **Step 4: Commit** `git add api/routes/stocks.py && git commit -m "feat: assemble two-axis decision (quality + setup + read)"`

---

### Task 6: Frontend redesign

**Files:** Modify `frontend/src/lib/types.ts`, `frontend/src/components/stocks/DecisionPanel.tsx`, `frontend/src/pages/Analysis.tsx`

- [ ] **Step 1: Replace the TS types.** In `frontend/src/lib/types.ts`, replace the `Decision` interface (and remove the `Calibration` interface + `calibration?` field on FullStockAnalysis) with:

```ts
export interface DecisionFactor {
  label: string; subscore: number | null; weight: number
  contribution: number | null; detail: string
}
export interface Quality { score: number | null; grade: string | null }
export interface Setup {
  score: number
  direction: 'Long' | 'Short' | 'Stand aside'
  percentile: number | null; band: string | null
  hit_rate: number | null; avg_forward_return: number | null; n: number | null
  low_sample: boolean | null; as_of: string | null; horizon_days: number | null
  expected_value_r: number | null
  factors: DecisionFactor[]
  regime: { label: string; vix: number | null; multiplier: number }
}
export interface Decision { quality: Quality; setup: Setup; read: string }
```
Keep `decision?: Decision` on `FullStockAnalysis`; remove the `calibration?` line.

- [ ] **Step 2: Rewrite `DecisionPanel.tsx`** to the two-axis layout. Replace the whole file with:

```tsx
import { useState } from 'react'
import type { Decision } from '../../lib/types'
import { computeSizing } from '../../lib/sizing'

interface Props {
  decision: Decision
  entry: number | null
  stop: number | null
  currentPrice: number | null
}

const GRADE_COLOR: Record<string, string> = { A: '#00e676', B: '#84cc16', C: '#ffab00', D: '#ff7043', F: '#ff1744' }
const BAND_COLOR: Record<string, string> = { Prime: '#00e676', Strong: '#84cc16', Fair: '#ffab00', Weak: '#ff7043' }
const DIR_COLOR: Record<string, string> = { Long: '#00e676', Short: '#ff1744', 'Stand aside': '#ffab00' }

function num(v: string, fallback: number): number {
  const n = parseFloat(v.replace(/[^0-9.]/g, '')); return isNaN(n) ? fallback : n
}

export default function DecisionPanel({ decision, entry, stop, currentPrice }: Props) {
  const [equity, setEquity] = useState<number>(() => num(localStorage.getItem('decision.accountSize') ?? '', 100000))
  const [maxRisk, setMaxRisk] = useState<number>(() => num(localStorage.getItem('decision.maxRiskPct') ?? '', 1))
  const saveEquity = (v: number) => { setEquity(v); localStorage.setItem('decision.accountSize', String(v)) }
  const saveRisk = (v: number) => { setMaxRisk(v); localStorage.setItem('decision.maxRiskPct', String(v)) }

  const { quality, setup, read } = decision
  const gColor = GRADE_COLOR[quality.grade ?? ''] ?? '#94a3b8'
  const bColor = BAND_COLOR[setup.band ?? ''] ?? '#94a3b8'
  const dColor = DIR_COLOR[setup.direction] ?? '#94a3b8'
  const eff = entry ?? currentPrice
  const sizing = computeSizing({ equity, maxRiskPct: maxRisk, conviction: setup.score, entry: eff, stop })
  const usd = (n: number) => `$${Math.round(n).toLocaleString()}`

  return (
    <div className="rounded-xl border p-5 flex flex-col gap-4" style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
      <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: '#475569' }}>Decision</span>

      {/* Two axes */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Quality */}
        <div className="flex flex-col gap-1 px-4 py-3 rounded-xl" style={{ backgroundColor: '#0a0e1a' }}>
          <span className="text-xs uppercase tracking-wide" style={{ color: '#475569' }}>Quality (company)</span>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black" style={{ color: gColor }}>{quality.grade ?? '—'}</span>
            <span className="text-sm tabular-nums" style={{ color: '#94a3b8' }}>{quality.score ?? '—'}/100</span>
          </div>
        </div>
        {/* Setup */}
        <div className="flex flex-col gap-1 px-4 py-3 rounded-xl" style={{ backgroundColor: '#0a0e1a' }}>
          <span className="text-xs uppercase tracking-wide" style={{ color: '#475569' }}>Setup (entry timing)</span>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black" style={{ color: bColor }}>{setup.band ?? '—'}</span>
            <span className="text-sm font-bold px-2 py-0.5 rounded" style={{ backgroundColor: dColor + '22', color: dColor }}>{setup.direction}</span>
          </div>
          {setup.percentile != null && (
            <div className="flex items-center gap-2 mt-1">
              <div className="flex-1 h-1.5 rounded-full" style={{ backgroundColor: 'rgba(255,255,255,0.06)' }}>
                <div className="h-1.5 rounded-full" style={{ width: `${setup.percentile}%`, backgroundColor: bColor }} />
              </div>
              <span className="text-xs tabular-nums" style={{ color: '#475569' }}>top {Math.round(100 - setup.percentile)}%</span>
            </div>
          )}
          {setup.hit_rate != null && (
            <span className="text-xs mt-0.5" style={{ color: '#94a3b8' }}>
              {setup.hit_rate}% up · {(setup.avg_forward_return ?? 0) >= 0 ? '+' : ''}{setup.avg_forward_return}%/{setup.horizon_days}d
              <span style={{ color: '#475569' }}> (n={setup.n}{setup.low_sample ? ', small' : ''}, {setup.as_of})</span>
            </span>
          )}
        </div>
      </div>

      {/* Read */}
      <div className="text-sm flex items-start gap-2" style={{ color: '#cbd5e1' }}>
        <span style={{ color: '#475569' }}>▸</span><span>{read}</span>
      </div>

      {/* Setup drivers */}
      <div className="flex flex-col gap-1.5">
        <span className="text-xs uppercase tracking-wide" style={{ color: '#475569' }}>Setup drivers</span>
        {setup.factors.map(f => {
          const c = f.contribution ?? 0; const pos = c >= 0
          return (
            <div key={f.label} className="flex items-center gap-2 text-xs">
              <span className="w-24 shrink-0" style={{ color: '#94a3b8' }}>{f.label}</span>
              <div className="flex-1 h-2 rounded-full relative" style={{ backgroundColor: 'rgba(255,255,255,0.05)' }}>
                <div className="absolute top-0 h-2 rounded-full" style={{ left: '50%', width: `${Math.min(Math.abs(c) * 200, 50)}%`, transform: pos ? 'none' : 'translateX(-100%)', backgroundColor: f.subscore == null ? '#475569' : pos ? '#00e676' : '#ff1744' }} />
              </div>
              <span className="w-40 shrink-0 text-right truncate" style={{ color: '#475569' }}>{f.subscore == null ? 'n/a' : f.detail}</span>
            </div>
          )
        })}
        <div className="flex items-center gap-2 text-xs mt-1">
          <span className="w-24 shrink-0" style={{ color: '#94a3b8' }}>Regime</span>
          <span style={{ color: '#cbd5e1' }}>{setup.regime.label}{setup.regime.vix != null ? ` · VIX ${setup.regime.vix}` : ''} · ×{setup.regime.multiplier}</span>
        </div>
        {setup.expected_value_r != null && (
          <div className="flex items-center gap-2 text-xs">
            <span className="w-24 shrink-0" style={{ color: '#94a3b8' }}>Expected value</span>
            <span style={{ color: setup.expected_value_r >= 0 ? '#00e676' : '#ff1744' }}>{setup.expected_value_r >= 0 ? '+' : ''}{setup.expected_value_r}R</span>
          </div>
        )}
        <span className="text-xs mt-1" style={{ color: '#334155' }}>Setup ex-fundamentals · percentile vs S&P 100 history · overlapping windows</span>
      </div>

      {/* Sizing */}
      <div className="border-t pt-3 mt-1" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
        <div className="flex items-center gap-3 flex-wrap mb-2">
          <label className="text-xs flex items-center gap-1" style={{ color: '#475569' }}>Account $
            <input type="text" defaultValue={String(equity)} onBlur={e => saveEquity(num(e.target.value, equity))} className="w-28 px-2 py-1 rounded text-xs tabular-nums" style={{ backgroundColor: '#0a0e1a', color: '#e2e8f0', border: '1px solid rgba(255,255,255,0.08)' }} />
          </label>
          <label className="text-xs flex items-center gap-1" style={{ color: '#475569' }}>Max risk %
            <input type="text" defaultValue={String(maxRisk)} onBlur={e => saveRisk(num(e.target.value, maxRisk))} className="w-16 px-2 py-1 rounded text-xs tabular-nums" style={{ backgroundColor: '#0a0e1a', color: '#e2e8f0', border: '1px solid rgba(255,255,255,0.08)' }} />
          </label>
        </div>
        {sizing.ok ? (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <SizeStat label="Shares" value={sizing.shares.toLocaleString()} />
            <SizeStat label="Position" value={usd(sizing.positionDollars)} sub={`${sizing.pctOfEquity.toFixed(1)}% of acct`} />
            <SizeStat label="At risk" value={usd(sizing.riskDollars)} sub={`${sizing.riskPct.toFixed(2)}% risk`} />
            <SizeStat label="Setup-scaled" value={`${(setup.score * 10).toFixed(0)}% of max`} sub={sizing.capped ? 'capped' : ''} />
          </div>
        ) : (<div className="text-xs" style={{ color: '#ffab00' }}>{sizing.reason}</div>)}
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

- [ ] **Step 3: Update the call site.** In `frontend/src/pages/Analysis.tsx`, the `<DecisionPanel>` block: keep `decision={data.decision}`, `entry`, `stop`, `currentPrice`; REMOVE the `calibration={data.calibration}` line.

- [ ] **Step 4: Build.** `cd <root>/frontend && npm install && npm run build` → `tsc -b && vite build` passes, 0 TS errors.

- [ ] **Step 5: Commit** `git add frontend/src/lib/types.ts frontend/src/components/stocks/DecisionPanel.tsx frontend/src/pages/Analysis.tsx && git commit -m "feat: two-axis Decision panel (Quality x Setup + Read)"`

---

## Self-Review

**Spec coverage:** Setup=ex-fundamentals conviction (T5 score=None); Quality+grade (T2,T5); percentile+band from distribution (T1,T3,T5); band cutoffs 50/80/95 (T1); grade cutoffs (T2); setup-driver breakdown excludes Fundamentals (inherent in score=None → no Fundamentals factor); Read line matrix (T2,T5); nested Decision model + fold calibration (T4); panel two-axis + percentile bar + read + drivers + sizing off setup (T6); batch emits percentiles + regen (T3); degrade gracefully (T5 None-guards); tests (T1,T2). ✓

**Placeholder scan:** none.

**Type consistency:** `setup_raw` keys (`conviction`,`direction`,`expected_value_r`,`factors`,`regime`) from `compute_conviction` → `Setup` fields; `Quality{score,grade}`; `Decision{quality,setup,read}` ↔ TS `Quality/Setup/Decision` ↔ panel `decision.quality/.setup/.read`. `conviction_percentiles`/`percentile_of`/`band_for`/`quality_grade`/`read_line` names match across tasks. Old `Calibration` model + `calibration` field removed in both py (T4) and ts (T6). ✓
