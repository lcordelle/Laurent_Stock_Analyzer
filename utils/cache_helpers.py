"""
Caching helpers for remote/ngrok performance.
Reduces yfinance API calls on repeated analyses.
"""
import streamlit as st
from utils.stock_analyzer import StockAnalyzer


@st.cache_data(ttl=300)  # 5 min cache - same as StockAnalyzer internal
def get_cached_stock_data(ticker: str, period: str = "1y"):
    """Fetch stock data with Streamlit-level caching. Speeds up remote use."""
    return StockAnalyzer().get_stock_data(ticker, period=period)
