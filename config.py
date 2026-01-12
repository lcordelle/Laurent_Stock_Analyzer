# VirtualFusion Stock Analyzer Pro - Configuration File
# Customize application behavior and settings

# ===========================================
# APPLICATION SETTINGS
# ===========================================

APP_TITLE = "VirtualFusion Stock Analyzer Pro"
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
# API SETTINGS
# ===========================================

# Yahoo Finance settings
YF_TIMEOUT = 30  # seconds
YF_MAX_RETRIES = 3
YF_RETRY_DELAY = 2  # seconds

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
# ADVANCED OPTIONS
# ===========================================

# Enable debug mode (shows additional information)
DEBUG_MODE = False

# Log file location
LOG_FILE = 'stock_analyzer.log'

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
