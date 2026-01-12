"""
Stock Analyzer Core Engine
Handles all stock data fetching, scoring, and analysis logic
Simplified for local use with Yahoo Finance
"""

import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import time
warnings.filterwarnings('ignore')

class StockAnalyzer:
    """Advanced Stock Analysis Engine"""
    
    def __init__(self):
        self.cache = {}
    
    def get_stock_data(self, ticker, period="1y"):
        """Fetch comprehensive stock data with caching"""
        # Clean ticker symbol
        ticker = str(ticker).upper().strip()
        
        # Check cache first
        cache_key = f"{ticker}_{period}"
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            # Check if cache is still valid (5 minutes)
            if time.time() - cached_data.get('timestamp', 0) < 300:
                return cached_data.get('data')
        
        try:
            # Use yfinance - works perfectly on local network
            stock = yf.Ticker(ticker)
            
            # Get historical data
            hist = stock.history(period=period)
            
            # Check if we got valid data
            if hist is None or len(hist) == 0:
                return None
            
            # Fetch additional data
            try:
                info = stock.info
            except:
                info = {}
            
            try:
                financials = stock.financials
                if financials is None:
                    financials = pd.DataFrame()
            except:
                financials = pd.DataFrame()
            
            try:
                balance_sheet = stock.balance_sheet
                if balance_sheet is None:
                    balance_sheet = pd.DataFrame()
            except:
                balance_sheet = pd.DataFrame()
            
            try:
                cash_flow = stock.cashflow
                if cash_flow is None:
                    cash_flow = pd.DataFrame()
            except:
                cash_flow = pd.DataFrame()
            
            # Return data
            result = {
                'ticker': ticker,
                'history': hist,
                'info': info,
                'financials': financials,
                'balance_sheet': balance_sheet,
                'cash_flow': cash_flow,
                'stock_object': stock
            }
            
            # Cache the result
            self.cache[cache_key] = {
                'data': result,
                'timestamp': time.time()
            }
            
            return result
        except Exception as e:
            return None
