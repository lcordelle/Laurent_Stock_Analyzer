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
Managed by **two** macOS LaunchAgents, each KeepAlive-supervised & run at login:
- `com.virtualfusion.stock-analyzer.api` — execs uvicorn on :8001 (auto-restarts if it crashes)
- `com.virtualfusion.stock-analyzer.tunnel` — execs ngrok → laurent.ngrok.io
They are independent, so a restart of one never drops the other.

## Run / Deploy
```bash
# Deploy code changes (rebuild frontend + cleanly reload backend) — the normal path:
./deploy.sh

# Restart just the backend (loads new Python code, deterministic, no race):
launchctl kickstart -k "gui/$(id -u)/com.virtualfusion.stock-analyzer.api"

# Manual all-in-one fallback (NOT the supervised path):
./start-permanent.sh

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
