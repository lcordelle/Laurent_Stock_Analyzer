# Stock Analyzer Cleanup & Verdict Engine — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove 5 unused pages and 4 API routes, trim the nav to 8 items, and add a prominent full-width verdict banner (BUY/SELL/HOLD with 6-signal breakdown) at the top of the Analysis page.

**Architecture:** A new `GET /api/stocks/{ticker}/verdict` endpoint in `stocks.py` derives the 6-signal weighted verdict from existing `_analyze_ticker()` data (no extra network calls). The React `VerdictBanner` component fetches it as a parallel query so the chart and tabs render immediately while the verdict computes. The existing sidebar verdict card remains but the new banner is the primary decision surface.

**Tech Stack:** FastAPI (Python), Pydantic, React 18, TypeScript, TanStack Query, Tailwind CSS

---

## File Map

| Action | File |
|---|---|
| Delete | `frontend/src/pages/AiPredictor.tsx` |
| Delete | `frontend/src/pages/Journal.tsx` |
| Delete | `frontend/src/pages/Backtest.tsx` |
| Delete | `frontend/src/pages/Advanced.tsx` |
| Delete | `frontend/src/pages/Batch.tsx` |
| Delete | `api/routes/ai_predictor.py` |
| Delete | `api/routes/journal.py` |
| Delete | `api/routes/backtest_route.py` |
| Delete | `api/routes/advanced.py` |
| Modify | `frontend/src/App.tsx` — remove 5 routes + imports |
| Modify | `frontend/src/components/layout/TopNav.tsx` — trim NAV_LINKS to 8, switch to marketPulseApi |
| Modify | `api/routes/market_pulse.py` — absorb /market-breadth endpoint from advanced.py |
| Modify | `api/main.py` — remove 4 router imports + registrations |
| Modify | `frontend/src/services/api.ts` — remove dead api objects, add marketBreadth to marketPulseApi, add verdictApi |
| Modify | `frontend/src/lib/types.ts` — add VerdictResponse type |
| Modify | `api/routes/stocks.py` — add VerdictResponse model + endpoint |
| Modify | `frontend/src/pages/Analysis.tsx` — remove advancedApi usages, add VerdictBanner, remove dead quick-action links |
| Create | `frontend/src/components/stocks/VerdictBanner.tsx` |

---

## Task 1: Delete dead frontend pages + update App.tsx and TopNav

**Files:**
- Delete: `frontend/src/pages/AiPredictor.tsx`
- Delete: `frontend/src/pages/Journal.tsx`
- Delete: `frontend/src/pages/Backtest.tsx`
- Delete: `frontend/src/pages/Advanced.tsx`
- Delete: `frontend/src/pages/Batch.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/layout/TopNav.tsx`

- [ ] **Step 1: Delete the five unused page files**

```bash
rm frontend/src/pages/AiPredictor.tsx \
   frontend/src/pages/Journal.tsx \
   frontend/src/pages/Backtest.tsx \
   frontend/src/pages/Advanced.tsx \
   frontend/src/pages/Batch.tsx
```

- [ ] **Step 2: Replace App.tsx with cleaned-up version**

Replace the entire content of `frontend/src/App.tsx` with:

```tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuth } from './hooks/useAuth'
import TopNav from './components/layout/TopNav'
import Login from './pages/Login'
import Home from './pages/Home'
import Analysis from './pages/Analysis'
import Screener from './pages/Screener'
import Reports from './pages/Reports'
import Opportunities from './pages/Opportunities'
import Watchlist from './pages/Watchlist'
import PennyStocks from './pages/PennyStocks'
import Alerts from './pages/Alerts'
import './index.css'

const qc = new QueryClient({ defaultOptions: { queries: { retry: 1, staleTime: 5 * 60 * 1000 } } })

function AuthGate({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/*" element={
            <AuthGate>
              <TopNav />
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/analysis" element={<Analysis />} />
                <Route path="/screener" element={<Screener />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="/opportunities" element={<Opportunities />} />
                <Route path="/watchlist" element={<Watchlist />} />
                <Route path="/penny-stocks" element={<PennyStocks />} />
                <Route path="/alerts" element={<Alerts />} />
              </Routes>
            </AuthGate>
          } />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
```

- [ ] **Step 3: Update NAV_LINKS in TopNav.tsx**

In `frontend/src/components/layout/TopNav.tsx`, replace the `NAV_LINKS` array:

```ts
const NAV_LINKS = [
  { to: '/', label: 'Dashboard' },
  { to: '/analysis', label: 'Analysis' },
  { to: '/opportunities', label: '⚡ Opportunities' },
  { to: '/watchlist', label: '★ Watchlist' },
  { to: '/penny-stocks', label: '💎 Penny Buys' },
  { to: '/screener', label: 'Screener' },
  { to: '/alerts', label: '🔔 Alerts' },
  { to: '/reports', label: 'Reports' },
]
```

- [ ] **Step 4: Verify TypeScript compiles cleanly**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```

Expected: no errors referencing the deleted pages.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.tsx frontend/src/components/layout/TopNav.tsx
git commit -m "feat: remove unused pages (AI Predictor, Journal, Backtest, Advanced, Batch), trim nav to 8 items"
```

---

## Task 2: Remove dead API routes from backend

**Files:**
- Delete: `api/routes/ai_predictor.py`
- Delete: `api/routes/journal.py`
- Delete: `api/routes/backtest_route.py`
- Delete: `api/routes/advanced.py`
- Modify: `api/main.py`
- Modify: `frontend/src/services/api.ts`

- [ ] **Step 1: Delete the four unused route files**

```bash
rm api/routes/ai_predictor.py \
   api/routes/journal.py \
   api/routes/backtest_route.py \
   api/routes/advanced.py
```

- [ ] **Step 2: Update the import line in api/main.py**

Find this line (line 15):
```python
from api.routes import auth, stocks, screener, portfolio, reports, opportunities, market_pulse, ai_research, watchlist, penny_stocks, ai_predictor, grades, advanced, journal, alerts_route, backtest_route
```

Replace with:
```python
from api.routes import auth, stocks, screener, portfolio, reports, opportunities, market_pulse, ai_research, watchlist, penny_stocks, grades, alerts_route
```

- [ ] **Step 3: Remove the four router registrations in api/main.py**

Remove these four lines:
```python
app.include_router(ai_predictor.router, prefix="/api")
app.include_router(advanced.router, prefix="/api")
app.include_router(journal.router, prefix="/api")
app.include_router(backtest_route.router, prefix="/api")
```

- [ ] **Step 4: Remove dead API client objects from frontend/src/services/api.ts**

Remove the following exported objects entirely:

```ts
export const aiPredictorApi = {
  predict: (ticker: string) => api.get(`/ai-predictor/${ticker}`).then(r => r.data),
}

export const advancedApi = {
  options: (ticker: string) => api.get(`/advanced/options/${ticker}`).then(r => r.data),
  insider: (ticker: string) => api.get(`/advanced/insider/${ticker}`).then(r => r.data),
  shortInterest: (ticker: string) => api.get(`/advanced/short-interest/${ticker}`).then(r => r.data),
  institutional: (ticker: string) => api.get(`/advanced/institutional/${ticker}`).then(r => r.data),
  patterns: (ticker: string) => api.get(`/advanced/patterns/${ticker}`).then(r => r.data),
  marketBreadth: () => api.get('/market-breadth').then(r => r.data),
}

export const journalApi = {
  open: () => api.get('/journal/open').then(r => r.data),
  closed: () => api.get('/journal/closed').then(r => r.data),
  summary: () => api.get('/journal/summary').then(r => r.data),
  add: (body: {
    ticker: string; direction: string; entry_date: string;
    entry_price: number; shares: number; notes?: string; tags?: string
  }) => api.post('/journal/add', body).then(r => r.data),
  close: (id: number, exit_date: string, exit_price: number) =>
    api.post(`/journal/${id}/close`, { exit_date, exit_price }).then(r => r.data),
  delete: (id: number) => api.delete(`/journal/${id}`).then(r => r.data),
}

export const backtestApi = {
  strategies: () => api.get('/backtest/strategies').then(r => r.data),
  run: (ticker: string, strategy: string, period: string, initial_capital: number) =>
    api.post('/backtest/run', { ticker, strategy, period, initial_capital }).then(r => r.data),
}
```

- [ ] **Step 5: Verify backend starts cleanly**

```bash
python3 -m uvicorn api.main:app --port 8001 --reload &
sleep 3 && curl -s http://localhost:8001/api/health
```

Expected: `{"status":"ok","version":"2.0"}`

Kill the test server: `kill %1`

- [ ] **Step 6: Verify TypeScript compiles cleanly**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```

Expected: no errors.

- [ ] **Step 7: Commit**

```bash
git add api/main.py frontend/src/services/api.ts
git commit -m "feat: remove dead API routes (ai_predictor, journal, backtest, advanced)"
```

---

## Task 2b: Move /market-breadth and clean up advancedApi usages in Analysis.tsx

**Files:**
- Modify: `api/routes/market_pulse.py`
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/components/layout/TopNav.tsx`
- Modify: `frontend/src/pages/Analysis.tsx`

The `/market-breadth` endpoint lives in `advanced.py` (which we're deleting) and powers the market regime chip in TopNav. It must be moved to `market_pulse.py` before `advanced.py` is deleted. Additionally, `Analysis.tsx` uses `advancedApi` for 7 query calls (Options & Patterns tab and Smart Money tab) — these must be removed since `advancedApi` is being deleted.

- [ ] **Step 1: Add /market-breadth to market_pulse.py**

In `api/routes/market_pulse.py`, at the end of the file, add:

```python
from utils.market_breadth import get_market_regime

@router.get("/market-breadth")
async def market_breadth(_: str = Depends(verify_token)):
    return get_market_regime()
```

- [ ] **Step 2: Add marketBreadth to marketPulseApi in services/api.ts**

In `frontend/src/services/api.ts`, update `marketPulseApi`:

```ts
export const marketPulseApi = {
  get: () => api.get('/market-pulse').then(r => r.data),
  marketBreadth: () => api.get('/market-breadth').then(r => r.data),
}
```

- [ ] **Step 3: Update TopNav.tsx to use marketPulseApi**

In `frontend/src/components/layout/TopNav.tsx`, replace:

```ts
import { advancedApi } from '../../services/api'
```

with:

```ts
import { marketPulseApi } from '../../services/api'
```

And replace:

```ts
queryFn: advancedApi.marketBreadth,
```

with:

```ts
queryFn: marketPulseApi.marketBreadth,
```

- [ ] **Step 4: Remove advancedApi import and Options/SmartMoney tabs from Analysis.tsx**

In `frontend/src/pages/Analysis.tsx`:

**a)** Replace the import line (line ~5):

```ts
import { stockApi, advancedApi } from '../services/api'
```

with:

```ts
import { stockApi } from '../services/api'
```

**b)** Remove the `Tab` union type entries and update the type (line ~277):

```ts
type Tab = 'fundamentals' | 'earnings' | 'news' | 'ai' | 'valuation' | 'catalysts'
```

**c)** In the `DeepTabs` function, remove the two tab entries from the `tabs` array (lines ~292-293):

Remove these two entries:
```ts
    { id: 'optpatterns',  label: '🎯 Options & Patterns' },
    { id: 'smartmoney',   label: '🏦 Smart Money' },
```

**d)** Remove the five `useQuery` hooks that use `advancedApi` (lines ~296-325, the ones with queryKeys `options-flow`, `patterns`, `short`, `insider`, `institutional`).

**e)** Remove the two tab rendering blocks: the entire `{tab === 'optpatterns' && (...)}` block and the entire `{tab === 'smartmoney' && (...)}` block from inside `DeepTabs`'s return JSX.

**f)** Remove the `chartPatterns` query from the main `Analysis` component (lines ~631-636):

Remove:
```ts
  const { data: chartPatterns } = useQuery({
    queryKey: ['patterns', ticker],
    queryFn: () => advancedApi.patterns(ticker),
    enabled: !!ticker && !!data && !data.error,
    staleTime: 5 * 60_000,
  })
```

**g)** Remove the `patterns` prop from `CandlestickChart` (line ~1072):

Change:
```tsx
                    patterns={chartPatterns?.patterns}
```

to nothing (delete that line).

- [ ] **Step 5: Verify TypeScript compiles cleanly**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```

Expected: no errors.

- [ ] **Step 6: Commit**

```bash
git add api/routes/market_pulse.py frontend/src/services/api.ts \
        frontend/src/components/layout/TopNav.tsx \
        frontend/src/pages/Analysis.tsx
git commit -m "feat: move /market-breadth to market_pulse, remove advancedApi usages from Analysis.tsx"
```

---

## Task 3: Add verdict endpoint to stocks.py

**Files:**
- Modify: `api/routes/stocks.py`

The verdict is computed from an existing `FullStockAnalysis` object — no extra network calls.

- [ ] **Step 1: Add VerdictSignal and VerdictResponse models after the existing router declaration (line ~22)**

In `api/routes/stocks.py`, after the line `router = APIRouter(tags=["stocks"])`, add:

```python
from pydantic import BaseModel

class VerdictSignalDetail(BaseModel):
    label: str
    score: int
    weight: float

class VerdictResponse(BaseModel):
    verdict: str
    confidence: int
    vf_score: int
    signals: dict[str, VerdictSignalDetail]
    price_target: Optional[float]
    stop_loss: Optional[float]
    why: str
```

- [ ] **Step 2: Add _compute_verdict() function at the end of stocks.py, before the route handlers**

Add this function immediately before the `@router.post("/analyze")` line (line 783):

```python
def _compute_verdict(analysis: FullStockAnalysis) -> VerdictResponse:
    sig = analysis.trading_signals
    score = analysis.score
    fct = analysis.forecast
    rat = analysis.analyst_rating
    rsk = analysis.risk_profile
    price = analysis.metrics.current_price if analysis.metrics else None

    # ── Technical signal (25%) ────────────────────────────────────────────
    tech_score = sig.confidence if sig and sig.confidence is not None else 50
    tech_signal = sig.signal or "HOLD" if sig else "HOLD"
    tech_label = (
        "Strong Bullish" if "STRONG BUY" in tech_signal else
        "Bullish"        if "BUY" in tech_signal else
        "Strong Bearish" if "STRONG SELL" in tech_signal else
        "Bearish"        if "SELL" in tech_signal else
        "Neutral"
    )

    # ── Fundamental signal (25%) ──────────────────────────────────────────
    fund_score = score.total if score else 50
    fund_label = (
        "Exceptional" if fund_score >= 80 else
        "Strong"      if fund_score >= 65 else
        "Moderate"    if fund_score >= 50 else
        "Weak"
    )

    # ── AI Outlook signal (20%) ───────────────────────────────────────────
    if fct and fct.probability is not None and fct.forecast_change_pct is not None:
        if fct.forecast_change_pct > 0:
            ai_score = int(min(100, 50 + fct.probability * 50))
        else:
            ai_score = int(max(0, 50 - fct.probability * 50))
    else:
        ai_score = 50
    ai_label = (
        "Bullish"  if ai_score >= 65 else
        "Neutral"  if ai_score >= 45 else
        "Bearish"
    )

    # ── Analyst signal (15%) ─────────────────────────────────────────────
    if rat and rat.mean is not None:
        # mean: 1=Strong Buy → 5=Strong Sell; map to 0-100
        analyst_score = int(max(0, min(100, (5 - rat.mean) / 4 * 100)))
        if rat.target_mean and price and price > 0:
            upside = (rat.target_mean - price) / price * 100
            if upside > 20:   analyst_score = min(100, analyst_score + 10)
            elif upside > 10: analyst_score = min(100, analyst_score + 5)
    else:
        analyst_score = 50
    analyst_label = (
        "Strong Buy" if analyst_score >= 80 else
        "Buy"        if analyst_score >= 60 else
        "Hold"       if analyst_score >= 40 else
        "Sell"
    )

    # ── Momentum signal (10%) ─────────────────────────────────────────────
    trend = sig.trend_strength if sig else None
    momentum_score = (
        85 if trend == "STRONG UPTREND" else
        70 if trend == "UPTREND" else
        50 if trend == "MIXED" else
        30 if trend == "DOWNTREND" else
        50
    )
    momentum_label = (
        "Strong Uptrend" if momentum_score >= 80 else
        "Uptrend"        if momentum_score >= 65 else
        "Neutral"        if momentum_score >= 45 else
        "Downtrend"
    )

    # ── Risk signal (5%) — inverted: low risk → high score ────────────────
    if rsk and rsk.sharpe_ratio is not None:
        risk_score = (
            80 if rsk.sharpe_ratio >= 1.0 else
            65 if rsk.sharpe_ratio >= 0.5 else
            45 if rsk.sharpe_ratio >= 0.0 else
            25
        )
    elif rsk and rsk.volatility is not None:
        risk_score = int(max(0, min(100, 100 - rsk.volatility)))
    else:
        risk_score = 50
    risk_label = (
        "Low Risk"      if risk_score >= 70 else
        "Moderate Risk" if risk_score >= 45 else
        "High Risk"
    )

    # ── Weighted composite ────────────────────────────────────────────────
    weights = {"technical": 0.25, "fundamental": 0.25, "ai_outlook": 0.20,
               "analyst": 0.15, "momentum": 0.10, "risk": 0.05}
    scores_map = {
        "technical": tech_score, "fundamental": fund_score,
        "ai_outlook": ai_score, "analyst": analyst_score,
        "momentum": momentum_score, "risk": risk_score,
    }
    composite = sum(scores_map[k] * w for k, w in weights.items())

    verdict = (
        "STRONG BUY"  if composite >= 75 else
        "BUY"         if composite >= 60 else
        "HOLD"        if composite >= 45 else
        "SELL"        if composite >= 30 else
        "STRONG SELL"
    )

    bullish_count = sum(1 for s in scores_map.values() if s > 60)
    confidence = int(round(bullish_count / len(scores_map) * 100))

    # ── Price target + stop loss ──────────────────────────────────────────
    price_target = None
    if rat and rat.target_mean:
        price_target = round(rat.target_mean, 2)
    elif sig and sig.tp1:
        price_target = sig.tp1

    stop_loss = round(sig.stop_loss, 2) if sig and sig.stop_loss else None

    # ── Why text ──────────────────────────────────────────────────────────
    if fund_score >= 80 and tech_score >= 70:
        why = "Elite fundamentals aligned with bullish technicals — rare high-conviction setup"
    elif analyst_score >= 75 and fund_score >= 65:
        why = f"Analyst consensus and strong fundamentals align — meaningful upside potential"
    elif ai_score >= 70 and tech_score >= 65:
        why = "AI forecast and technical momentum both point higher — improving risk/reward"
    elif risk_score >= 70 and fund_score >= 65:
        why = "Low-volatility compounder with strong fundamentals — quality at acceptable risk"
    elif composite >= 60:
        why = "Multiple signals confirm bullish bias — monitor for optimal entry"
    elif composite >= 45:
        why = "Mixed signals — wait for a clearer technical or fundamental catalyst"
    else:
        why = "Bearish signal convergence across multiple dimensions — risk management priority"

    return VerdictResponse(
        verdict=verdict,
        confidence=confidence,
        vf_score=fund_score,
        signals={
            "technical":   VerdictSignalDetail(label=tech_label,      score=tech_score,     weight=0.25),
            "fundamental": VerdictSignalDetail(label=fund_label,      score=fund_score,     weight=0.25),
            "ai_outlook":  VerdictSignalDetail(label=ai_label,        score=ai_score,       weight=0.20),
            "analyst":     VerdictSignalDetail(label=analyst_label,   score=analyst_score,  weight=0.15),
            "momentum":    VerdictSignalDetail(label=momentum_label,  score=momentum_score, weight=0.10),
            "risk":        VerdictSignalDetail(label=risk_label,      score=risk_score,     weight=0.05),
        },
        price_target=price_target,
        stop_loss=stop_loss,
        why=why,
    )
```

- [ ] **Step 3: Add the verdict route handler at the end of stocks.py**

After the existing `@router.post("/batch")` handler, add:

```python
@router.get("/stocks/{ticker}/verdict", response_model=VerdictResponse)
async def get_verdict(ticker: str, period: str = "1y", _: str = Depends(verify_token)):
    loop = asyncio.get_event_loop()
    analysis = await loop.run_in_executor(None, _analyze_ticker, ticker.upper(), period)
    if analysis.error:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=analysis.error)
    return _compute_verdict(analysis)
```

- [ ] **Step 4: Test the endpoint manually**

Start the server and test:

```bash
python3 -m uvicorn api.main:app --port 8001 &
sleep 3
# Get a token first
TOKEN=$(curl -s -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
# Call verdict
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8001/api/stocks/AAPL/verdict" | python3 -m json.tool | head -40
```

Expected: JSON with `verdict`, `confidence`, `vf_score`, `signals` (6 keys), `price_target`, `stop_loss`, `why`.

Kill server: `kill %1`

- [ ] **Step 5: Commit**

```bash
git add api/routes/stocks.py
git commit -m "feat: add /api/stocks/{ticker}/verdict endpoint with 6-signal weighted decision engine"
```

---

## Task 4: Add VerdictResponse type to types.ts and verdictApi to api.ts

**Files:**
- Modify: `frontend/src/lib/types.ts`
- Modify: `frontend/src/services/api.ts`

- [ ] **Step 1: Add VerdictSignalDetail and VerdictResponse to types.ts**

In `frontend/src/lib/types.ts`, append at the end of the file:

```ts
export interface VerdictSignalDetail {
  label: string
  score: number
  weight: number
}

export interface VerdictResponse {
  verdict: string
  confidence: number
  vf_score: number
  signals: {
    technical: VerdictSignalDetail
    fundamental: VerdictSignalDetail
    ai_outlook: VerdictSignalDetail
    analyst: VerdictSignalDetail
    momentum: VerdictSignalDetail
    risk: VerdictSignalDetail
  }
  price_target?: number
  stop_loss?: number
  why: string
}
```

- [ ] **Step 2: Add verdictApi to frontend/src/services/api.ts**

In `frontend/src/services/api.ts`, add after the `gradesApi` export:

```ts
export const verdictApi = {
  get: (ticker: string, period = '1y') =>
    api.get<import('../lib/types').VerdictResponse>(`/stocks/${ticker}/verdict`, { params: { period } }).then(r => r.data),
}
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/types.ts frontend/src/services/api.ts
git commit -m "feat: add VerdictResponse type and verdictApi client"
```

---

## Task 5: Create VerdictBanner component

**Files:**
- Create: `frontend/src/components/stocks/VerdictBanner.tsx`

- [ ] **Step 1: Create the component**

Create `frontend/src/components/stocks/VerdictBanner.tsx`:

```tsx
import { useQuery } from '@tanstack/react-query'
import { verdictApi } from '../../services/api'
import type { VerdictResponse } from '../../lib/types'
import { fmt } from '../../lib/formatters'

function verdictColor(verdict: string): string {
  if (verdict.includes('BUY'))  return '#00e676'
  if (verdict.includes('SELL')) return '#ff1744'
  return '#ffab00'
}

function signalKey(key: string): string {
  return key === 'ai_outlook' ? 'AI Outlook' : key.charAt(0).toUpperCase() + key.slice(1)
}

function SignalPill({ name, detail }: { name: string; detail: VerdictResponse['signals']['technical'] }) {
  const bullish = detail.score > 60
  const neutral  = detail.score >= 40 && detail.score <= 60
  const color = bullish ? '#00e676' : neutral ? '#ffab00' : '#ff1744'
  return (
    <div
      className="flex items-center gap-2 rounded-lg px-3 py-1.5"
      style={{
        background: `${color}0d`,
        border: `1px solid ${color}30`,
      }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full shrink-0"
        style={{ backgroundColor: color }}
      />
      <span className="text-xs font-semibold" style={{ color: '#e2e8f0' }}>
        {signalKey(name)}
      </span>
      <span className="text-xs font-bold" style={{ color }}>
        {detail.label}
      </span>
      <span className="text-xs tabular-nums" style={{ color: '#475569' }}>
        {detail.score}
      </span>
    </div>
  )
}

function VerdictSkeleton() {
  return (
    <div
      className="rounded-xl border p-5 animate-pulse"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
    >
      <div className="h-8 w-48 rounded" style={{ backgroundColor: 'rgba(255,255,255,0.06)' }} />
      <div className="mt-3 flex gap-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-7 w-24 rounded-lg" style={{ backgroundColor: 'rgba(255,255,255,0.04)' }} />
        ))}
      </div>
    </div>
  )
}

export default function VerdictBanner({ ticker, period }: { ticker: string; period?: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ['verdict', ticker, period ?? '1y'],
    queryFn: () => verdictApi.get(ticker, period ?? '1y'),
    staleTime: 5 * 60 * 1000,
  })

  if (isLoading) return <VerdictSkeleton />
  if (!data) return null

  const vc = verdictColor(data.verdict)

  return (
    <div
      className="rounded-xl border p-5 flex flex-col gap-4"
      style={{
        backgroundColor: '#111827',
        borderColor: `${vc}35`,
        background: `linear-gradient(135deg, ${vc}0a, #111827 60%)`,
      }}
    >
      {/* Top row: verdict + key numbers */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-5">
          <div>
            <div
              className="text-3xl font-black tracking-wide leading-none"
              style={{ color: vc }}
            >
              {data.verdict}
            </div>
            <div className="text-xs mt-1" style={{ color: '#64748b' }}>
              {data.confidence}% confidence · {Object.values(data.signals).filter(s => s.score > 60).length} of 6 signals bullish
            </div>
          </div>

          <div className="w-px h-10 shrink-0" style={{ backgroundColor: 'rgba(255,255,255,0.08)' }} />

          <div className="flex gap-5">
            <div>
              <div className="text-2xl font-black tabular-nums leading-none" style={{ color: '#e2e8f0' }}>
                {data.vf_score}
                <span className="text-sm font-normal" style={{ color: '#475569' }}>/100</span>
              </div>
              <div className="text-xs mt-0.5 uppercase tracking-wide" style={{ color: '#64748b' }}>VF Score</div>
            </div>
            {data.price_target != null && (
              <div>
                <div className="text-2xl font-black tabular-nums leading-none" style={{ color: '#00d4ff' }}>
                  {fmt.price(data.price_target)}
                </div>
                <div className="text-xs mt-0.5 uppercase tracking-wide" style={{ color: '#64748b' }}>Price Target</div>
              </div>
            )}
            {data.stop_loss != null && (
              <div>
                <div className="text-2xl font-black tabular-nums leading-none" style={{ color: '#ff1744' }}>
                  {fmt.price(data.stop_loss)}
                </div>
                <div className="text-xs mt-0.5 uppercase tracking-wide" style={{ color: '#64748b' }}>Stop Loss</div>
              </div>
            )}
          </div>
        </div>

        <p className="text-xs italic max-w-xs leading-relaxed" style={{ color: '#94a3b8' }}>
          "{data.why}"
        </p>
      </div>

      {/* Signal pills */}
      <div className="flex flex-wrap gap-2">
        {(Object.entries(data.signals) as [keyof VerdictResponse['signals'], VerdictResponse['signals']['technical']][]).map(
          ([key, detail]) => <SignalPill key={key} name={key} detail={detail} />
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/stocks/VerdictBanner.tsx
git commit -m "feat: add VerdictBanner component with 6-signal pill layout"
```

---

## Task 6: Wire VerdictBanner into Analysis.tsx + remove dead quick-action links

**Files:**
- Modify: `frontend/src/pages/Analysis.tsx`

- [ ] **Step 1: Add VerdictBanner import at the top of Analysis.tsx**

In `frontend/src/pages/Analysis.tsx`, add the import after the existing component imports (around line 22):

```tsx
import VerdictBanner from '../components/stocks/VerdictBanner'
```

- [ ] **Step 2: Remove the three quick-action links for Journal, Backtest (keep Alerts)**

Find this block in `Analysis.tsx` (around lines 782–795):

```tsx
{data && !data.error && ticker && (
  <div className="flex gap-2 flex-wrap">
    {[
      { to: `/alerts?ticker=${ticker}`,   label: '🔔 Set Alert',  bg: '#ffab0015', border: 'rgba(255,171,0,0.25)',  color: '#ffab00' },
      { to: `/journal?ticker=${ticker}`,  label: '📒 Log Trade',  bg: '#00e67615', border: 'rgba(0,230,118,0.25)',  color: '#00e676' },
      { to: `/backtest?ticker=${ticker}`, label: '📊 Backtest',   bg: '#00d4ff15', border: 'rgba(0,212,255,0.25)',  color: '#00d4ff' },
    ].map(({ to, label, bg, border, color }) => (
      <Link key={to} to={to}
        className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-opacity hover:opacity-80"
        style={{ backgroundColor: bg, border: `1px solid ${border}`, color }}>
        {label}
      </Link>
    ))}
  </div>
)}
```

Replace with (only the Alerts link remains):

```tsx
{data && !data.error && ticker && (
  <div className="flex gap-2 flex-wrap">
    <Link
      to={`/alerts?ticker=${ticker}`}
      className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-opacity hover:opacity-80"
      style={{ backgroundColor: '#ffab0015', border: '1px solid rgba(255,171,0,0.25)', color: '#ffab00' }}
    >
      🔔 Set Alert
    </Link>
  </div>
)}
```

- [ ] **Step 3: Insert VerdictBanner as the first element inside the data block**

Find this line in `Analysis.tsx` (around line 819):

```tsx
{data && !data.error && (
  <div className="flex flex-col gap-4">

    {/* ── Company description ────────────────────────────────────────── */}
```

Replace with:

```tsx
{data && !data.error && (
  <div className="flex flex-col gap-4">

    {/* ── Verdict banner ─────────────────────────────────────────────── */}
    {ticker && <VerdictBanner ticker={ticker} period={period} />}

    {/* ── Company description ────────────────────────────────────────── */}
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: no errors.

- [ ] **Step 5: Build the frontend and verify it runs**

```bash
cd frontend && npm run build 2>&1 | tail -10
```

Expected: `built in Xs` with no errors.

- [ ] **Step 6: Start the full app and visually verify**

```bash
# Terminal 1 — backend
python3 -m uvicorn api.main:app --port 8001 --reload &

# Terminal 2 — frontend dev server
cd frontend && npm run dev
```

Open `http://localhost:5173`, log in, navigate to Analysis, search AAPL.

Verify:
- Verdict banner appears at top (skeleton while loading, then STRONG BUY / BUY / HOLD etc.)
- 6 signal pills render with correct colors
- Price target and stop loss show
- No links to Journal or Backtest exist
- Nav has exactly 8 items: Dashboard, Analysis, Opportunities, Watchlist, Penny Buys, Screener, Alerts, Reports
- All 8 nav links navigate correctly

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pages/Analysis.tsx
git commit -m "feat: wire VerdictBanner into Analysis page, remove dead quick-action links"
```

---

## Task 7: Final cleanup — remove .gitignore noise and verify build

**Files:**
- Modify: `.gitignore` (add `.superpowers/`)

- [ ] **Step 1: Add .superpowers to .gitignore**

```bash
echo '.superpowers/' >> .gitignore
git add .gitignore
```

- [ ] **Step 2: Final full build verification**

```bash
cd frontend && npm run build 2>&1 | tail -5
```

Expected: build succeeds.

- [ ] **Step 3: Verify no dead imports remain**

```bash
grep -r "AiPredictor\|Journal\|Backtest\|Advanced\|Batch\|ai_predictor\|backtest_route\|journal\b" \
  frontend/src api/main.py api/routes/ \
  --include="*.ts" --include="*.tsx" --include="*.py" \
  | grep -v "node_modules\|\.superpowers\|specs\|plans" | grep -v "^Binary"
```

Expected: empty output (no references to deleted features).

- [ ] **Step 4: Final commit**

```bash
git add .gitignore
git commit -m "chore: add .superpowers to gitignore, verify final cleanup"
```
