# VirtualFusion Stock Analyzer Pro - Configuration File
# Customize application behavior and settings

import os

# ===========================================
# APPLICATION SETTINGS
# ===========================================

APP_TITLE = "Laurent Stock Analyzer Pro"
APP_ICON = "📈"
DEFAULT_PORT = 8501

# ===========================================
# DATA SETTINGS
# ===========================================

# Default time period for analysis
DEFAULT_TIME_PERIOD = "1y"  # Options: 1mo, 3mo, 6mo, 1y, 2y, 5y, max

# Data refresh interval (in seconds)
DATA_CACHE_TTL = 3600  # 1 hour

# Maximum stocks for batch comparison
MAX_COMPARISON_STOCKS = 10

# Maximum stocks for screening
MAX_SCREENER_STOCKS = 50

# ===========================================
# SCORING WEIGHTS (Total: 100 points)
# ===========================================

SCORE_WEIGHTS = {
    'profitability': 25,  # Gross Margin score
    'roe': 20,            # Return on Equity score
    'fcf_margin': 20,     # Free Cash Flow Margin score
    'valuation': 20,      # P/E Ratio score
    'growth': 15          # Revenue Growth score
}

# ===========================================
# SCORING THRESHOLDS
# ===========================================

# Profitability (Gross Margin %)
GROSS_MARGIN_EXCELLENT = 60
GROSS_MARGIN_GOOD = 40
GROSS_MARGIN_FAIR = 20

# ROE (Return on Equity %)
ROE_EXCELLENT = 20
ROE_GOOD = 15
ROE_FAIR = 10

# FCF Margin (%)
FCF_MARGIN_EXCELLENT = 15
FCF_MARGIN_GOOD = 10
FCF_MARGIN_FAIR = 5

# P/E Ratio
PE_RATIO_MIN_IDEAL = 10
PE_RATIO_MAX_IDEAL = 25
PE_RATIO_MIN_GOOD = 5
PE_RATIO_MAX_GOOD = 35
PE_RATIO_MAX_FAIR = 50

# Revenue Growth (%)
REVENUE_GROWTH_EXCELLENT = 20
REVENUE_GROWTH_GOOD = 10
REVENUE_GROWTH_FAIR = 0

# ===========================================
# TECHNICAL INDICATOR SETTINGS
# ===========================================

# Moving Averages
SMA_PERIODS = [20, 50, 200]

# RSI Settings
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# MACD Settings
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Bollinger Bands
BB_PERIOD = 20
BB_STD_DEV = 2

# ===========================================
# VISUALIZATION SETTINGS
# ===========================================

# Chart height (in pixels)
CHART_HEIGHT_MAIN = 500
CHART_HEIGHT_SECONDARY = 300
CHART_HEIGHT_SMALL = 250

# Color scheme
COLOR_POSITIVE = '#00c853'
COLOR_NEGATIVE = '#ff1744'
COLOR_NEUTRAL = '#ffa726'
COLOR_PRIMARY = '#1f77b4'

# Chart template
CHART_TEMPLATE = 'plotly_white'  # Options: plotly, plotly_white, plotly_dark, ggplot2, seaborn

# ===========================================
# EXPORT SETTINGS
# ===========================================

# PDF Report Settings
PDF_PAGE_SIZE = 'letter'  # Options: letter, A4
PDF_FONT_SIZE_TITLE = 24
PDF_FONT_SIZE_HEADER = 16
PDF_FONT_SIZE_BODY = 11

# Excel Export Settings
EXCEL_ENGINE = 'xlsxwriter'  # Options: xlsxwriter, openpyxl

# ===========================================
# SCREENER DEFAULT SETTINGS
# ===========================================

SCREENER_DEFAULTS = {
    'pe_min': 0,
    'pe_max': 100,
    'margin_min': 20,
    'roe_min': 10,
    'revenue_growth_min': 0,
    'market_cap_min': 1000000  # 1 Million
}

# ===========================================
# RISK METRICS
# ===========================================

# Annualised risk-free rate used for Sharpe and Sortino ratios.
# Approximates the US 3-month T-Bill yield as of mid-2025; update periodically.
RISK_FREE_RATE = 0.043  # 4.3 %

# ===========================================
# API SETTINGS
# ===========================================

# Yahoo Finance settings
YF_TIMEOUT = 30  # seconds
YF_MAX_RETRIES = 3
YF_RETRY_DELAY = 2  # seconds

# AI provider endpoints (overridable via env vars)
GROQ_API_URL = os.environ.get("GROQ_API_URL", "https://api.groq.com/openai/v1")
OLLAMA_API_URL = os.environ.get("OLLAMA_API_URL", "http://localhost:11434/v1")
OLLAMA_TAGS_URL = os.environ.get("OLLAMA_TAGS_URL", "http://localhost:11434/api/tags")

# Penny stock screener thresholds
PENNY_MAX_PRICE = float(os.environ.get("PENNY_MAX_PRICE", "5.0"))
PENNY_MIN_PRICE = float(os.environ.get("PENNY_MIN_PRICE", "0.1"))
PENNY_MIN_VOLUME = int(os.environ.get("PENNY_MIN_VOLUME", "500000"))
PENNY_MIN_MCAP = int(os.environ.get("PENNY_MIN_MCAP", "5000000"))

# ===========================================
# FEATURE FLAGS
# ===========================================

FEATURES = {
    'technical_indicators': True,
    'fundamental_analysis': True,
    'pdf_reports': True,
    'excel_export': True,
    'csv_export': True,
    'batch_comparison': True,
    'stock_screener': True,
    'advanced_charts': True
}

# ===========================================
# DISPLAY SETTINGS
# ===========================================

# Number of decimal places for different metrics
DECIMAL_PLACES = {
    'price': 2,
    'percentage': 2,
    'ratio': 2,
    'large_numbers': 0
}

# Format for large numbers
LARGE_NUMBER_FORMAT = 'abbreviated'  # Options: abbreviated (1.5B), full (1,500,000,000)

# ===========================================
# ALERT THRESHOLDS
# ===========================================

ALERTS = {
    'high_pe_ratio': 50,
    'low_pe_ratio': 5,
    'high_debt_equity': 2.0,
    'low_current_ratio': 1.0,
    'high_rsi': 70,
    'low_rsi': 30
}

# ===========================================
# RECOMMENDATION SETTINGS
# ===========================================

RECOMMENDATION_THRESHOLDS = {
    'strong_buy': 80,
    'buy': 65,
    'hold': 50,
    'reduce': 35,
    'sell': 0
}

# ===========================================
# FACTOR GRADE SYSTEM (Seeking Alpha-style)
# ===========================================

GRADE_PERCENTILE_THRESHOLDS = [
    (92, "A+"), (85, "A"), (77, "A-"),
    (69, "B+"), (62, "B"), (54, "B-"),
    (46, "C+"), (38, "C"), (31, "C-"),
    (23, "D+"), (15, "D"), (8,  "D-"),
    (0,  "F"),
]

GRADE_COLORS = {
    "A+": "#15803d", "A": "#16a34a", "A-": "#22c55e",
    "B+": "#65a30d", "B": "#84cc16", "B-": "#a3e635",
    "C+": "#ca8a04", "C": "#d97706", "C-": "#f59e0b",
    "D+": "#ea580c", "D": "#dc2626", "D-": "#b91c1c",
    "F":  "#7f1d1d", "N/A": "#94a3b8",
}

# Sector median benchmarks for absolute-threshold fallback
# (when fewer than 3 peers return a valid metric)
SECTOR_METRIC_MEDIANS = {
    "Technology": {
        "pe": 28.0, "fwd_pe": 24.0, "pb": 7.5, "ps": 5.8, "ev_ebitda": 22.0,
        "revenue_growth": 0.10, "eps_growth": 0.12, "ebitda_growth": 0.11, "fcf_growth": 0.10,
        "gross_margin": 0.55, "net_margin": 0.18, "roe": 0.25, "roic": 0.18, "fcf_margin": 0.15,
        "mom_1m": 0.02, "mom_3m": 0.05, "mom_6m": 0.10, "mom_12m": 0.18,
    },
    "Financial Services": {
        "pe": 13.0, "fwd_pe": 11.0, "pb": 1.4, "ps": 2.5, "ev_ebitda": 11.0,
        "revenue_growth": 0.06, "eps_growth": 0.08, "ebitda_growth": 0.07, "fcf_growth": 0.06,
        "gross_margin": 0.65, "net_margin": 0.22, "roe": 0.12, "roic": 0.10, "fcf_margin": 0.12,
        "mom_1m": 0.01, "mom_3m": 0.04, "mom_6m": 0.08, "mom_12m": 0.14,
    },
    "Healthcare": {
        "pe": 22.0, "fwd_pe": 18.0, "pb": 4.0, "ps": 3.5, "ev_ebitda": 16.0,
        "revenue_growth": 0.07, "eps_growth": 0.09, "ebitda_growth": 0.08, "fcf_growth": 0.07,
        "gross_margin": 0.58, "net_margin": 0.14, "roe": 0.18, "roic": 0.14, "fcf_margin": 0.13,
        "mom_1m": 0.01, "mom_3m": 0.03, "mom_6m": 0.07, "mom_12m": 0.12,
    },
    "Consumer Cyclical": {
        "pe": 20.0, "fwd_pe": 17.0, "pb": 4.5, "ps": 1.8, "ev_ebitda": 14.0,
        "revenue_growth": 0.06, "eps_growth": 0.08, "ebitda_growth": 0.07, "fcf_growth": 0.06,
        "gross_margin": 0.35, "net_margin": 0.07, "roe": 0.20, "roic": 0.14, "fcf_margin": 0.06,
        "mom_1m": 0.01, "mom_3m": 0.04, "mom_6m": 0.08, "mom_12m": 0.14,
    },
    "Consumer Defensive": {
        "pe": 22.0, "fwd_pe": 19.0, "pb": 5.0, "ps": 1.5, "ev_ebitda": 15.0,
        "revenue_growth": 0.04, "eps_growth": 0.06, "ebitda_growth": 0.05, "fcf_growth": 0.05,
        "gross_margin": 0.38, "net_margin": 0.09, "roe": 0.22, "roic": 0.15, "fcf_margin": 0.07,
        "mom_1m": 0.00, "mom_3m": 0.02, "mom_6m": 0.05, "mom_12m": 0.10,
    },
    "Energy": {
        "pe": 12.0, "fwd_pe": 10.0, "pb": 1.8, "ps": 1.2, "ev_ebitda": 8.0,
        "revenue_growth": 0.05, "eps_growth": 0.06, "ebitda_growth": 0.05, "fcf_growth": 0.05,
        "gross_margin": 0.30, "net_margin": 0.10, "roe": 0.15, "roic": 0.12, "fcf_margin": 0.08,
        "mom_1m": 0.01, "mom_3m": 0.03, "mom_6m": 0.06, "mom_12m": 0.10,
    },
    "Industrials": {
        "pe": 20.0, "fwd_pe": 17.0, "pb": 4.0, "ps": 2.0, "ev_ebitda": 14.0,
        "revenue_growth": 0.06, "eps_growth": 0.08, "ebitda_growth": 0.07, "fcf_growth": 0.06,
        "gross_margin": 0.35, "net_margin": 0.10, "roe": 0.18, "roic": 0.14, "fcf_margin": 0.08,
        "mom_1m": 0.01, "mom_3m": 0.03, "mom_6m": 0.07, "mom_12m": 0.12,
    },
    "Communication Services": {
        "pe": 20.0, "fwd_pe": 17.0, "pb": 3.5, "ps": 3.0, "ev_ebitda": 14.0,
        "revenue_growth": 0.08, "eps_growth": 0.10, "ebitda_growth": 0.09, "fcf_growth": 0.08,
        "gross_margin": 0.50, "net_margin": 0.15, "roe": 0.20, "roic": 0.15, "fcf_margin": 0.14,
        "mom_1m": 0.01, "mom_3m": 0.04, "mom_6m": 0.08, "mom_12m": 0.14,
    },
    "Real Estate": {
        "pe": 35.0, "fwd_pe": 30.0, "pb": 2.5, "ps": 6.0, "ev_ebitda": 20.0,
        "revenue_growth": 0.05, "eps_growth": 0.06, "ebitda_growth": 0.05, "fcf_growth": 0.04,
        "gross_margin": 0.55, "net_margin": 0.20, "roe": 0.08, "roic": 0.06, "fcf_margin": 0.18,
        "mom_1m": 0.00, "mom_3m": 0.02, "mom_6m": 0.05, "mom_12m": 0.08,
    },
    "Utilities": {
        "pe": 18.0, "fwd_pe": 16.0, "pb": 1.8, "ps": 2.5, "ev_ebitda": 12.0,
        "revenue_growth": 0.03, "eps_growth": 0.04, "ebitda_growth": 0.03, "fcf_growth": 0.02,
        "gross_margin": 0.42, "net_margin": 0.15, "roe": 0.10, "roic": 0.07, "fcf_margin": 0.05,
        "mom_1m": 0.00, "mom_3m": 0.02, "mom_6m": 0.04, "mom_12m": 0.07,
    },
    "Basic Materials": {
        "pe": 15.0, "fwd_pe": 12.0, "pb": 2.5, "ps": 1.5, "ev_ebitda": 10.0,
        "revenue_growth": 0.05, "eps_growth": 0.06, "ebitda_growth": 0.05, "fcf_growth": 0.04,
        "gross_margin": 0.28, "net_margin": 0.09, "roe": 0.14, "roic": 0.11, "fcf_margin": 0.07,
        "mom_1m": 0.01, "mom_3m": 0.03, "mom_6m": 0.06, "mom_12m": 0.10,
    },
    "_default": {
        "pe": 20.0, "fwd_pe": 17.0, "pb": 3.5, "ps": 2.5, "ev_ebitda": 15.0,
        "revenue_growth": 0.07, "eps_growth": 0.09, "ebitda_growth": 0.08, "fcf_growth": 0.07,
        "gross_margin": 0.45, "net_margin": 0.12, "roe": 0.15, "roic": 0.12, "fcf_margin": 0.10,
        "mom_1m": 0.01, "mom_3m": 0.03, "mom_6m": 0.07, "mom_12m": 0.12,
    },
}

# Dividend scorecard thresholds
DIVIDEND_PAYOUT_THRESHOLDS = [0.25, 0.50, 0.70, 0.85]   # A+→A→B→C→D cut-offs
DIVIDEND_COVERAGE_THRESHOLDS = [5.0, 3.0, 2.0, 1.5]     # interest coverage ratio
DIVIDEND_DEBT_THRESHOLDS = [0.5, 1.0, 1.5, 2.0]         # debt-to-equity ratio

# ===========================================
# ADVANCED OPTIONS
# ===========================================

# Enable debug mode (shows additional information)
DEBUG_MODE = False

# Log file location
LOG_FILE = 'stock_analyzer.log'

# ===========================================
# LOGGING SETUP
# ===========================================
import logging
import os

_log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
_handlers = [logging.StreamHandler()]
if LOG_FILE:
    _handlers.append(logging.FileHandler(os.path.expanduser(LOG_FILE), mode='a', encoding='utf-8'))

logging.basicConfig(
    level=_log_level,
    format='%(asctime)s %(levelname)s %(name)s — %(message)s',
    handlers=_handlers,
    force=True,
)

# Enable data caching
ENABLE_CACHE = True

# Cache directory
CACHE_DIR = '~/.cache/stock_analyzer/'

# ===========================================
# CUSTOMIZATION
# ===========================================

# Custom stock lists for quick access
CUSTOM_LISTS = {
    'Tech Giants': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA'],
    'Semiconductors': ['NVDA', 'AMD', 'INTC', 'TSM', 'AVGO'],
    'Financial': ['JPM', 'BAC', 'WFC', 'C', 'GS'],
    'Healthcare': ['JNJ', 'PFE', 'UNH', 'ABBV', 'TMO'],
    'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG']
}

# ===========================================
# NOTES
# ===========================================

# To modify settings:
# 1. Edit the values in this file
# 2. Save the file
# 3. Restart the application

# For boolean values use True or False (capitalized)
# For strings use quotes: 'value' or "value"
# For numbers don't use quotes: 100, 3.14
# For lists use brackets: [item1, item2, item3]
# For dictionaries use braces: {'key': 'value'}

# ===========================================
# END OF CONFIGURATION
# ===========================================
