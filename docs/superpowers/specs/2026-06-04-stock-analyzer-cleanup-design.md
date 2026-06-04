# Stock Analyzer — Cleanup & Consolidated Verdict Engine
**Date:** 2026-06-04
**Status:** Approved

## Objective

Clean up the app to four core features (Dashboard, Analysis, Opportunities, Penny Buys) plus supporting features (Watchlist, Screener, Alerts, Reports). Remove unused standalone features. Add a consolidated BUY/SELL/HOLD decision engine surfaced as a verdict banner at the top of the Analysis page.

---

## 1. Removals

### Pages deleted
| File | Route |
|---|---|
| `frontend/src/pages/AiPredictor.tsx` | `/ai-predictor` |
| `frontend/src/pages/Journal.tsx` | `/journal` |
| `frontend/src/pages/Backtest.tsx` | `/backtest` |
| `frontend/src/pages/Advanced.tsx` | `/advanced` |
| `frontend/src/pages/Batch.tsx` | `/batch` |

### API routes deleted
| File | Notes |
|---|---|
| `api/routes/ai_predictor.py` | Page-facing only; underlying AI logic in `ai_research.py` is kept |
| `api/routes/journal.py` | |
| `api/routes/backtest_route.py` | |
| `api/routes/advanced.py` | |

### App.tsx
Remove imports and `<Route>` entries for all 5 deleted pages.

### TopNav
NAV_LINKS trimmed to 8 entries in order:
1. `/` — Dashboard
2. `/analysis` — Analysis
3. `/opportunities` — ⚡ Opportunities
4. `/watchlist` — ★ Watchlist
5. `/penny-stocks` — 💎 Penny Buys
6. `/screener` — Screener
7. `/alerts` — 🔔 Alerts
8. `/reports` — Reports

---

## 2. DecisionEngine — New API Endpoint

**Endpoint:** `GET /api/stocks/{ticker}/verdict`
Added to `api/routes/stocks.py`. Reuses already-cached stock data — no double-fetch.

### Response schema
```json
{
  "verdict": "STRONG BUY | BUY | HOLD | SELL | STRONG SELL",
  "confidence": 78,
  "vf_score": 84,
  "signals": {
    "technical":   { "label": "Bullish",  "weight": 0.25, "score": 82 },
    "fundamental": { "label": "Strong",   "weight": 0.25, "score": 88 },
    "ai_outlook":  { "label": "Bullish",  "weight": 0.20, "score": 76 },
    "analyst":     { "label": "Buy",      "weight": 0.15, "score": 80 },
    "momentum":    { "label": "Positive", "weight": 0.10, "score": 71 },
    "risk":        { "label": "Moderate", "weight": 0.05, "score": 55 }
  },
  "price_target": 215.0,
  "stop_loss": 178.0,
  "why": "Strong fundamentals and bullish technicals outweigh moderate valuation risk."
}
```

### Signal sources
| Signal | Source | Weight |
|---|---|---|
| Technical | RSI, MACD, momentum from `stocks.py` | 25% |
| Fundamental | Profitability, FCF, ROE, growth from `stocks.py` | 25% |
| AI Outlook | `ai_research.py` structured signal | 20% |
| Analyst | Analyst rating/target from `stocks.py` | 15% |
| Momentum | Price momentum score from `stocks.py` | 10% |
| Risk | Beta/volatility inverted score from `stocks.py` | 5% |

### Verdict thresholds (weighted composite)
| Range | Verdict |
|---|---|
| ≥ 75 | STRONG BUY |
| 60–74 | BUY |
| 45–59 | HOLD |
| 30–44 | SELL |
| < 30 | STRONG SELL |

### Confidence
Percentage of signals above their neutral threshold (score > 60). A 5-of-6 bullish result = ~83% confidence.

---

## 3. Verdict Banner — Analysis Page

### Placement
Rendered immediately after the ticker search bar, before the candlestick chart and tabs. Loads async via a separate query so chart/tabs are not blocked.

### Layout
```
┌─────────────────────────────────────────────────────────────────────┐
│  STRONG BUY          VF Score  Price Target  Stop Loss              │
│  78% confidence      84/100    $215          $178                   │
│  5 of 6 signals      ────────────────────────────────────────────── │
│  bullish             "Strong fundamentals and bullish technicals…"  │
├─────────────────────────────────────────────────────────────────────┤
│ ● Technical Bullish 82  ● Fundamentals Strong 88  ● AI Outlook 76  │
│ ● Analyst Buy 80        ● Momentum Positive 71    ○ Risk Moderate 55│
└─────────────────────────────────────────────────────────────────────┘
```

### Color coding
- BUY / STRONG BUY → green (`#00e676`) border and text
- HOLD → amber (`#ffab00`)
- SELL / STRONG SELL → red (`#ff1744`)
- Each signal pill matches its own signal direction

### Loading state
Skeleton banner while verdict fetches. If verdict API fails, banner is hidden silently — rest of Analysis page unaffected.

---

## 4. AI Predictor — Integration (not removal)

`api/routes/ai_research.py` is **kept entirely**. It continues to power:
1. The **AI Outlook signal** in the verdict engine (score extracted from existing structured response)
2. The **AI Research tab** inside the Analysis page (unchanged — full narrative still shown)

The only change: the `/ai-predictor` standalone page and route are removed. All AI capability remains accessible through Analysis.

---

## 5. Files Changed Summary

### Deleted
- `frontend/src/pages/AiPredictor.tsx`
- `frontend/src/pages/Journal.tsx`
- `frontend/src/pages/Backtest.tsx`
- `frontend/src/pages/Advanced.tsx`
- `frontend/src/pages/Batch.tsx`
- `api/routes/ai_predictor.py`
- `api/routes/journal.py`
- `api/routes/backtest_route.py`
- `api/routes/advanced.py`

### Modified
- `frontend/src/App.tsx` — remove 5 routes and imports
- `frontend/src/components/layout/TopNav.tsx` — trim NAV_LINKS to 8
- `api/main.py` — remove router registrations for deleted routes
- `api/routes/stocks.py` — add `/verdict` endpoint
- `frontend/src/services/api.ts` — add `verdictApi.get(ticker)`
- `frontend/src/pages/Analysis.tsx` — add `VerdictBanner` component above chart

### Added
- `frontend/src/components/stocks/VerdictBanner.tsx` — new component
