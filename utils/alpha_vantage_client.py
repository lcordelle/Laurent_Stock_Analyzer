"""
Alpha Vantage Data Client
Fetches stock data from Alpha Vantage API as alternative to Yahoo Finance
"""

import requests
import pandas as pd
import numpy as np
import time
import os
from datetime import datetime, timedelta

class AlphaVantageClient:
    """Client for fetching data from Alpha Vantage API"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('ALPHA_VANTAGE_API_KEY', '0SD4K06XAEF1P5DI')
        self.base_url = 'https://www.alphavantage.co/query'
        self.last_request_time = 0
        self.min_request_interval = 12.1  # Alpha Vantage free tier: 5 calls/min = 12 seconds between calls
        
    def _rate_limit(self):
        """Enforce rate limiting (5 calls per minute for free tier)"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _make_request(self, function, symbol, **params):
        """Make API request to Alpha Vantage"""
        self._rate_limit()
        
        params.update({
            'function': function,
            'symbol': symbol,
            'apikey': self.api_key,
            'datatype': 'json'
        })
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Check for API errors
            if 'Error Message' in data:
                error_msg = data['Error Message']
                print(f"Alpha Vantage Error for {symbol} ({function}): {error_msg}", file=__import__('sys').stderr)
                raise Exception(f"Alpha Vantage Error: {error_msg}")
            if 'Note' in data:
                note = data['Note']
                print(f"Alpha Vantage Rate Limit for {symbol} ({function}): {note}", file=__import__('sys').stderr)
                raise Exception(f"Alpha Vantage Rate Limit: {note}")
            
            # Check if we got valid data
            if not data or len(data) == 0:
                print(f"Alpha Vantage empty response for {symbol} ({function})", file=__import__('sys').stderr)
                raise Exception(f"Alpha Vantage empty response")
            
            return data
        except requests.exceptions.RequestException as e:
            error_msg = f"Alpha Vantage request failed for {symbol} ({function}): {str(e)}"
            print(error_msg, file=__import__('sys').stderr)
            raise Exception(error_msg)
        except Exception as e:
            print(f"Alpha Vantage error for {symbol} ({function}): {str(e)}", file=__import__('sys').stderr)
            raise
    
    def get_historical_data(self, symbol, period='1y'):
        """Get historical price data (OHLCV)"""
        # Map period to Alpha Vantage output size
        period_map = {
            '1d': 'compact',
            '5d': 'compact',
            '1mo': 'compact',
            '3mo': 'full',
            '6mo': 'full',
            '1y': 'full',
            '2y': 'full',
            '5y': 'full',
            'max': 'full'
        }
        outputsize = period_map.get(period, 'full')
        
        data = self._make_request('TIME_SERIES_DAILY_ADJUSTED', symbol, outputsize=outputsize)
        
        # Parse the time series data
        if 'Time Series (Daily)' not in data:
            return None
        
        time_series = data['Time Series (Daily)']
        df_data = []
        
        for date_str, values in time_series.items():
            try:
                df_data.append({
                    'Date': pd.to_datetime(date_str),
                    'Open': float(values.get('1. open', 0)),
                    'High': float(values.get('2. high', 0)),
                    'Low': float(values.get('3. low', 0)),
                    'Close': float(values.get('4. close', 0)),
                    'Adj Close': float(values.get('5. adjusted close', values.get('4. close', 0))),
                    'Volume': int(float(values.get('6. volume', 0)))
                })
            except (ValueError, KeyError) as e:
                continue  # Skip invalid entries
        
        if not df_data:
            return None
        
        df = pd.DataFrame(df_data)
        df.set_index('Date', inplace=True)
        df.sort_index(inplace=True)
        
        # Ensure we have at least some data
        if len(df) == 0:
            return None
        
        # Filter by period if needed
        if period in ['1d', '5d', '1mo']:
            end_date = df.index[-1]
            if period == '1d':
                start_date = end_date - timedelta(days=1)
            elif period == '5d':
                start_date = end_date - timedelta(days=5)
            elif period == '1mo':
                start_date = end_date - timedelta(days=30)
            df = df[df.index >= start_date]
        
        return df
    
    def get_company_overview(self, symbol):
        """Get company overview and fundamentals"""
        data = self._make_request('OVERVIEW', symbol)
        
        if 'Symbol' not in data:
            return {}
        
        # Map Alpha Vantage fields to Yahoo Finance-like structure
        overview = {
            'symbol': data.get('Symbol', ''),
            'name': data.get('Name', ''),
            'description': data.get('Description', ''),
            'sector': data.get('Sector', ''),
            'industry': data.get('Industry', ''),
            'marketCap': float(data.get('MarketCapitalization', 0) or 0),
            'currentPrice': float(data.get('52WeekHigh', 0) or 0),  # Will get from quote
            'trailingPE': float(data.get('PERatio', 0) or 0),
            'forwardPE': float(data.get('ForwardPE', 0) or 0),
            'pegRatio': float(data.get('PEGRatio', 0) or 0),
            'priceToBook': float(data.get('PriceToBookRatio', 0) or 0),
            'dividendYield': float(data.get('DividendYield', 0) or 0) / 100 if data.get('DividendYield') else 0,
            'beta': float(data.get('Beta', 0) or 0),
            '52WeekHigh': float(data.get('52WeekHigh', 0) or 0),
            '52WeekLow': float(data.get('52WeekLow', 0) or 0),
            'fiftyTwoWeekHigh': float(data.get('52WeekHigh', 0) or 0),
            'fiftyTwoWeekLow': float(data.get('52WeekLow', 0) or 0),
            'grossMargins': float(data.get('GrossProfitTTM', 0) or 0) / float(data.get('RevenueTTM', 1) or 1) if data.get('RevenueTTM') else 0,
            'operatingMargins': float(data.get('OperatingMarginTTM', 0) or 0) / 100 if data.get('OperatingMarginTTM') else 0,
            'profitMargins': float(data.get('ProfitMargin', 0) or 0) / 100 if data.get('ProfitMargin') else 0,
            'returnOnEquity': float(data.get('ReturnOnEquityTTM', 0) or 0) / 100 if data.get('ReturnOnEquityTTM') else 0,
            'returnOnAssets': float(data.get('ReturnOnAssetsTTM', 0) or 0) / 100 if data.get('ReturnOnAssetsTTM') else 0,
            'revenueGrowth': float(data.get('QuarterlyRevenueGrowthYOY', 0) or 0) / 100 if data.get('QuarterlyRevenueGrowthYOY') else 0,
            'earningsGrowth': float(data.get('QuarterlyEarningsGrowthYOY', 0) or 0) / 100 if data.get('QuarterlyEarningsGrowthYOY') else 0,
            'debtToEquity': float(data.get('DebtToEquity', 0) or 0) if data.get('DebtToEquity') else 0,
            'currentRatio': float(data.get('CurrentRatio', 0) or 0) if data.get('CurrentRatio') else 0,
            'quickRatio': float(data.get('QuickRatio', 0) or 0) if data.get('QuickRatio') else 0,
            'targetMeanPrice': float(data.get('AnalystTargetPrice', 0) or 0) if data.get('AnalystTargetPrice') else 0,
            'numberOfAnalystOpinions': int(data.get('AnalystRating', 0) or 0),
            'recommendationKey': data.get('AnalystRating', 'N/A'),
            'volume': int(data.get('Volume', 0) or 0),
            'averageVolume': int(data.get('AverageVolume', 0) or 0),
            'longName': data.get('Name', ''),
            'longBusinessSummary': data.get('Description', ''),
        }
        
        return overview
    
    def get_quote(self, symbol):
        """Get real-time quote"""
        data = self._make_request('GLOBAL_QUOTE', symbol)
        
        if 'Global Quote' not in data:
            return {}
        
        quote = data['Global Quote']
        return {
            'currentPrice': float(quote.get('05. price', 0) or 0),
            'open': float(quote.get('02. open', 0) or 0),
            'high': float(quote.get('03. high', 0) or 0),
            'low': float(quote.get('04. low', 0) or 0),
            'previousClose': float(quote.get('08. previous close', 0) or 0),
            'volume': int(quote.get('06. volume', 0) or 0),
            'change': float(quote.get('09. change', 0) or 0),
            'changePercent': float(quote.get('10. change percent', 0) or 0) / 100 if quote.get('10. change percent') else 0,
        }
    
    def get_income_statement(self, symbol):
        """Get income statement (annual)"""
        data = self._make_request('INCOME_STATEMENT', symbol)
        
        if 'annualReports' not in data or len(data['annualReports']) == 0:
            return pd.DataFrame()
        
        # Convert to DataFrame
        reports = data['annualReports']
        df = pd.DataFrame(reports)
        
        # Set fiscal date as index
        if 'fiscalDateEnding' in df.columns:
            df['fiscalDateEnding'] = pd.to_datetime(df['fiscalDateEnding'])
            df.set_index('fiscalDateEnding', inplace=True)
            df.sort_index(inplace=True)
        
        return df
    
    def get_balance_sheet(self, symbol):
        """Get balance sheet (annual)"""
        data = self._make_request('BALANCE_SHEET', symbol)
        
        if 'annualReports' not in data or len(data['annualReports']) == 0:
            return pd.DataFrame()
        
        reports = data['annualReports']
        df = pd.DataFrame(reports)
        
        if 'fiscalDateEnding' in df.columns:
            df['fiscalDateEnding'] = pd.to_datetime(df['fiscalDateEnding'])
            df.set_index('fiscalDateEnding', inplace=True)
            df.sort_index(inplace=True)
        
        return df
    
    def get_cash_flow(self, symbol):
        """Get cash flow statement (annual)"""
        data = self._make_request('CASH_FLOW', symbol)
        
        if 'annualReports' not in data or len(data['annualReports']) == 0:
            return pd.DataFrame()
        
        reports = data['annualReports']
        df = pd.DataFrame(reports)
        
        if 'fiscalDateEnding' in df.columns:
            df['fiscalDateEnding'] = pd.to_datetime(df['fiscalDateEnding'])
            df.set_index('fiscalDateEnding', inplace=True)
            df.sort_index(inplace=True)
        
        return df
    
    def get_stock_data(self, symbol, period='1y'):
        """Get comprehensive stock data (compatible with yfinance format)"""
        try:
            # Get quote first for current price (faster)
            quote = self.get_quote(symbol)
            current_price = quote.get('currentPrice', 0) if quote else 0
            
            # Get historical data
            hist = self.get_historical_data(symbol, period)
            if hist is None or len(hist) == 0:
                return None
            
            # Update current price from latest close if quote failed
            if current_price == 0 and len(hist) > 0:
                current_price = float(hist['Close'].iloc[-1])
            
            # Get company overview
            overview = self.get_company_overview(symbol)
            
            # Update with current price
            overview['currentPrice'] = current_price
            overview['regularMarketPrice'] = current_price
            
            # Get financial statements (optional - can be slow)
            financials = pd.DataFrame()
            balance_sheet = pd.DataFrame()
            cash_flow = pd.DataFrame()
            
            try:
                financials = self.get_income_statement(symbol)
            except:
                pass
            
            try:
                balance_sheet = self.get_balance_sheet(symbol)
            except:
                pass
            
            try:
                cash_flow = self.get_cash_flow(symbol)
            except:
                pass
            
            # Return in yfinance-compatible format
            return {
                'ticker': symbol.upper(),
                'history': hist,
                'info': overview,
                'financials': financials,
                'balance_sheet': balance_sheet,
                'cash_flow': cash_flow,
                'stock_object': None  # Not needed for Alpha Vantage
            }
        except Exception as e:
            print(f"Alpha Vantage error for {symbol}: {str(e)}", file=__import__('sys').stderr)
            return None

