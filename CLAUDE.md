# VirtualFusion Stock Analyzer Pro

## Stack
- Python FastAPI backend (port **8001** — permanent, do NOT change)
- React + Vite frontend (served from `frontend/dist/` via FastAPI in prod)
- Data: yfinance (primary, free), Alpha Vantage (optional)
- Charts: Plotly/Recharts | Reports: ReportLab (PDF), openpyxl (Excel)

## Port Assignment — CRITICAL
**Port 8001 is permanently reserved for this app.**
Port 8000 is used by LLD Validator and other dev projects — never use 8000 here.
Changing the port will break the LaunchAgent and `laurent.ngrok.io`.

## Public URL
`https://laurent.ngrok.io` → always points to this app (port 8001)
Managed by macOS LaunchAgent `com.virtualfusion.stock-analyzer` — runs at login,
restarts automatically. Even when working on other projects, this stays up.

## Run
```bash
# Production (served via FastAPI):
./start-permanent.sh          # starts FastAPI on 8001 + ngrok tunnel

# Dev mode (hot reload):
cd frontend && npm run dev    # Vite on :3000, proxies /api → :8001
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8001 --reload
```

## No automated tests. Testing is manual via the web UI.

## Key Files
- `main.py` — Streamlit entry point (homepage)
- `config.py` — app settings, scoring weights, ports, cache TTL (3600s)
- `pages/` — multi-page app (Single Analysis, Batch, Screener, Reports)
- `utils/stock_analyzer.py` — main scoring engine (100-point scale)
- `utils/risk_analysis.py` — beta, volatility, portfolio risk
- `utils/visualizations.py` — Plotly charts (candlestick, MACD, RSI, etc.)
- `utils/auth.py` — in-app login/session auth
- `components/` — UI components (dashboard, navigation, styling)

## Scoring System (100 pts)
- Profitability: 25 | ROE: 20 | FCF Margin: 20 | Valuation: 20 | Growth: 15

## Rules
- Use `python3` not `python`
- Format with `black` if available
- Do not hardcode API keys — use environment variables or `config.py`
- `ALPHA_VANTAGE_API_KEY` optional in `.env` (see `.env.example`)
- Max batch: 10 stocks | Max screener: 50 stocks
