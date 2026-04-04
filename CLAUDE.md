# VirtualFusion Stock Analyzer Pro

## Stack
- Python / Streamlit (port 8501)
- Data: yfinance (primary, free), Alpha Vantage (optional)
- Charts: Plotly | Reports: ReportLab (PDF), openpyxl (Excel)

## Run
```bash
streamlit run main.py        # or ./run_app.sh
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
