"""
Stock Analyzer Core Engine
Handles all stock data fetching, scoring, and analysis logic
"""

import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import requests
import time
import random
import os
warnings.filterwarnings('ignore')

# Monkey-patch yfinance's base session to always use proper headers
# This ensures ALL yfinance requests use our headers, even if session parameter is ignored
_original_get = requests.Session.get
_original_request = requests.Session.request

def _patched_get(self, url, **kwargs):
    """Patched get method to always include proper headers"""
    if 'headers' not in kwargs:
        kwargs['headers'] = {}
    if 'User-Agent' not in kwargs['headers']:
        kwargs['headers'].update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    return _original_get(self, url, **kwargs)

def _patched_request(self, method, url, **kwargs):
    """Patched request method to always include proper headers"""
    if 'headers' not in kwargs:
        kwargs['headers'] = {}
    if 'User-Agent' not in kwargs['headers']:
        kwargs['headers'].update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    return _original_request(self, method, url, **kwargs)

# Apply monkey patch
requests.Session.get = _patched_get
requests.Session.request = _patched_request

# Rotating user agents to avoid detection
_USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
]

def _get_random_user_agent():
    """Get a random user agent"""
    return random.choice(_USER_AGENTS)

# Configure yfinance globally to use proper headers
def _create_yfinance_session():
    """Create a session with proper headers for yfinance"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': _get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
        'DNT': '1',
        'Referer': 'https://finance.yahoo.com/',
    })
    return session

class StockAnalyzer:
    """Advanced Stock Analysis Engine"""
    
    def __init__(self):
        self.cache = {}
        # Create a session with proper headers to avoid Yahoo Finance blocking
        self.session = _create_yfinance_session()
        # Track last request time to avoid rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.5  # Minimum seconds between requests
    
    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _refresh_session(self):
        """Create a new session with fresh headers"""
        self.session = _create_yfinance_session()
    
    def get_stock_data(self, ticker, period="1y"):
        """Fetch comprehensive stock data with caching and improved error handling"""
        # Clean ticker symbol
        ticker = str(ticker).upper().strip()
        
        # Check cache first
        cache_key = f"{ticker}_{period}"
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            # Check if cache is still valid (5 minutes)
            if time.time() - cached_data.get('timestamp', 0) < 300:
                return cached_data.get('data')
        
        # Enforce rate limiting
        self._rate_limit()
        
        # Quick timeout to prevent hanging forever
        overall_start_time = time.time()
        max_total_time = 15  # Maximum 15 seconds total
        
        # Try multiple times with retry logic for cloud environments
        max_retries = 2  # Reduced retries for faster failure
        last_error = None
        
        for attempt in range(max_retries):
            # Check if we've exceeded total time limit
            if time.time() - overall_start_time > max_total_time:
                print(f"Timeout: Exceeded {max_total_time}s for {ticker}", file=__import__('sys').stderr)
                return None
            
            try:
                # Refresh session every few attempts to rotate user agent
                if attempt > 0:
                    self._refresh_session()
                    # Shorter delay on retry
                    time.sleep(random.uniform(1, 2))
                
                # Method 1: Try yf.download first (often more reliable than Ticker.history)
                hist = None
                periods_to_try = ["1mo", "5d", "1d"]  # Start with shorter periods for faster response
                
                for try_period in periods_to_try:
                    # Check timeout before each attempt
                    if time.time() - overall_start_time > max_total_time:
                        break
                    
                    try:
                        # Shorter delay
                        time.sleep(random.uniform(0.3, 0.8))
                        
                        # Use yf.download with shorter timeout
                        hist_download = yf.download(
                            ticker, 
                            period=try_period, 
                            progress=False, 
                            session=self.session, 
                            timeout=10,  # Reduced timeout for faster failure
                            show_errors=False,
                            threads=False  # Single-threaded to avoid detection
                        )
                        
                        if hist_download is not None and len(hist_download) > 0:
                            # yf.download returns DataFrame with OHLCV columns
                            # If multi-index (multiple tickers), get first ticker
                            if isinstance(hist_download.columns, pd.MultiIndex):
                                # Get first ticker's data
                                first_ticker = hist_download.columns.levels[1][0]
                                hist = hist_download.xs(first_ticker, axis=1, level=1)
                            else:
                                hist = hist_download
                            
                            # Ensure we have required columns
                            if hist is not None and len(hist) > 0:
                                required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
                                if all(col in hist.columns for col in required_cols):
                                    break
                                else:
                                    # Create missing columns from Close
                                    for col in required_cols:
                                        if col not in hist.columns:
                                            if col == 'Volume':
                                                hist[col] = 0
                                            else:
                                                hist[col] = hist.get('Close', hist.iloc[:, 0])
                                    break
                    except Exception as e:
                        last_error = str(e)
                        continue
                
                # Method 2: If download failed, try Ticker.history (with timeout check)
                if hist is None or len(hist) == 0:
                    if time.time() - overall_start_time < max_total_time:
                        try:
                            stock = yf.Ticker(ticker, session=self.session)
                            for try_period in periods_to_try:
                                if time.time() - overall_start_time > max_total_time:
                                    break
                                try:
                                    hist = stock.history(period=try_period, timeout=10)
                                    if hist is not None and len(hist) > 0:
                                        break
                                except Exception as e:
                                    last_error = str(e)
                                    continue
                        except Exception as e:
                            last_error = str(e)
                
                # If all periods failed, fail fast (don't wait long)
                if hist is None or len(hist) == 0:
                    if attempt < max_retries - 1:
                        # Short wait before retry
                        wait_time = 2
                        print(f"Retry {attempt + 1}/{max_retries} for {ticker}", file=__import__('sys').stderr)
                        time.sleep(wait_time)
                        # Refresh session for next attempt
                        self._refresh_session()
                        continue
                    else:
                        # Final attempt failed - return None quickly
                        print(f"Failed to fetch {ticker} after {max_retries} attempts", file=__import__('sys').stderr)
                        return None
                    
                    # Last attempt failed - try to get at least some data
                    # Sometimes info works even if history doesn't
                    try:
                        info = stock.info
                        if info and len(info) > 0:
                            # Create minimal history from current price
                            current_price = info.get('currentPrice') or info.get('regularMarketPrice') or 0
                            if current_price > 0:
                                # Create a minimal DataFrame with current price
                                dates = pd.date_range(end=pd.Timestamp.now(), periods=1, freq='D')
                                hist = pd.DataFrame({
                                    'Open': [current_price],
                                    'High': [current_price],
                                    'Low': [current_price],
                                    'Close': [current_price],
                                    'Volume': [info.get('volume', 0)]
                                }, index=dates)
                            else:
                                return None
                        else:
                            return None
                    except:
                        return None
                
                # Fetch additional data with error handling
                info = {}
                try:
                    info = stock.info
                    # Validate info is not empty
                    if not info or len(info) == 0:
                        info = {}
                except Exception as e:
                    info = {}
                
                financials = pd.DataFrame()
                try:
                    financials = stock.financials
                    if financials is None:
                        financials = pd.DataFrame()
                except:
                    financials = pd.DataFrame()
                
                balance_sheet = pd.DataFrame()
                try:
                    balance_sheet = stock.balance_sheet
                    if balance_sheet is None:
                        balance_sheet = pd.DataFrame()
                except:
                    balance_sheet = pd.DataFrame()
                
                cash_flow = pd.DataFrame()
                try:
                    cash_flow = stock.cashflow
                    if cash_flow is None:
                        cash_flow = pd.DataFrame()
                except:
                    cash_flow = pd.DataFrame()
                
                # Validate we have at least history data
                if hist is not None and len(hist) > 0:
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
                else:
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    return None
                    
            except Exception as e:
                # Log error for debugging
                last_error = str(e)
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = (attempt + 1) * 2
                    time.sleep(wait_time)
                    continue
                # Last attempt failed
                # Print error for debugging (will show in Render logs)
                print(f"Failed to get ticker '{ticker}' reason: {last_error}", file=__import__('sys').stderr)
                return None
        
        # If we got here, all retries failed
        if last_error:
            print(f"Failed to get ticker '{ticker}' reason: {last_error}", file=__import__('sys').stderr)
        return None
    
    def calculate_score(self, data):
        """Calculate comprehensive stock score (0-100)"""
        if not data:
            return None
        
        info = data['info']
        score = 0
        max_score = 100
        components = {}
        
        # Profitability Score (25 points)
        try:
            gross_margin = info.get('grossMargins', 0) * 100
            if gross_margin > 60:
                score += 25
                components['Gross Margin'] = 25
            elif gross_margin > 40:
                score += 15
                components['Gross Margin'] = 15
            elif gross_margin > 20:
                score += 10
                components['Gross Margin'] = 10
            else:
                components['Gross Margin'] = 5
                score += 5
        except:
            components['Gross Margin'] = 0
        
        # ROE Score (20 points)
        try:
            roe = info.get('returnOnEquity', 0) * 100
            if roe > 20:
                score += 20
                components['ROE'] = 20
            elif roe > 15:
                score += 15
                components['ROE'] = 15
            elif roe > 10:
                score += 10
                components['ROE'] = 10
            else:
                components['ROE'] = 5
                score += 5
        except:
            components['ROE'] = 0
        
        # FCF Margin Score (20 points)
        try:
            fcf_margin = info.get('freeCashflow', 0) / info.get('totalRevenue', 1) * 100
            if fcf_margin > 15:
                score += 20
                components['FCF Margin'] = 20
            elif fcf_margin > 10:
                score += 15
                components['FCF Margin'] = 15
            elif fcf_margin > 5:
                score += 10
                components['FCF Margin'] = 10
            else:
                components['FCF Margin'] = 5
                score += 5
        except:
            components['FCF Margin'] = 0
        
        # Valuation Score (20 points)
        try:
            pe_ratio = info.get('trailingPE', 999)
            if 10 < pe_ratio < 25:
                score += 20
                components['Valuation'] = 20
            elif 5 < pe_ratio < 35:
                score += 15
                components['Valuation'] = 15
            elif pe_ratio < 50:
                score += 10
                components['Valuation'] = 10
            else:
                components['Valuation'] = 5
                score += 5
        except:
            components['Valuation'] = 0
        
        # Growth Score (15 points)
        try:
            revenue_growth = info.get('revenueGrowth', 0) * 100
            if revenue_growth > 20:
                score += 15
                components['Growth'] = 15
            elif revenue_growth > 10:
                score += 10
                components['Growth'] = 10
            elif revenue_growth > 0:
                score += 5
                components['Growth'] = 5
            else:
                components['Growth'] = 0
        except:
            components['Growth'] = 0
        
        return {
            'total_score': min(score, max_score),
            'components': components,
            'max_score': max_score
        }
    
    def get_key_metrics(self, data):
        """Extract key financial metrics"""
        if not data:
            return None
        
        info = data['info']
        hist = data['history']
        
        current_price = hist['Close'].iloc[-1] if len(hist) > 0 else info.get('currentPrice', 0)
        
        metrics = {
            'Current Price': current_price,
            'Today Range': f"${hist['Low'].iloc[-1]:.2f} - ${hist['High'].iloc[-1]:.2f}" if len(hist) > 0 else "N/A",
            '52 Week Range': f"${info.get('fiftyTwoWeekLow', 0):.2f} - ${info.get('fiftyTwoWeekHigh', 0):.2f}",
            'Market Cap': info.get('marketCap', 0),
            'P/E Ratio': info.get('trailingPE', 0),
            'Forward P/E': info.get('forwardPE', 0),
            'PEG Ratio': info.get('pegRatio', 0),
            'Price to Book': info.get('priceToBook', 0),
            'Dividend Yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
            'Volume': hist['Volume'].iloc[-1] if len(hist) > 0 else info.get('volume', 0),
            'Average Volume': info.get('averageVolume', 0),
            'Gross Margin': info.get('grossMargins', 0) * 100,
            'Operating Margin': info.get('operatingMargins', 0) * 100,
            'Profit Margin': info.get('profitMargins', 0) * 100,
            'ROE': info.get('returnOnEquity', 0) * 100,
            'ROA': info.get('returnOnAssets', 0) * 100,
            'Revenue Growth': info.get('revenueGrowth', 0) * 100,
            'Earnings Growth': info.get('earningsGrowth', 0) * 100,
            'Debt to Equity': info.get('debtToEquity', 0),
            'Current Ratio': info.get('currentRatio', 0),
            'Quick Ratio': info.get('quickRatio', 0),
            'Beta': info.get('beta', 0),
            'Target Price': info.get('targetMeanPrice', 0),
            'Analyst Rating': info.get('recommendationKey', 'N/A'),
            'Number of Analysts': info.get('numberOfAnalystOpinions', 0)
        }
        
        return metrics
    
    def calculate_technical_indicators(self, hist):
        """Calculate technical indicators"""
        if hist is None or len(hist) < 50:
            return None
        
        # Moving Averages
        hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
        hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
        hist['SMA_200'] = hist['Close'].rolling(window=200).mean()
        
        # RSI
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        hist['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
        exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
        hist['MACD'] = exp1 - exp2
        hist['Signal'] = hist['MACD'].ewm(span=9, adjust=False).mean()
        
        # Bollinger Bands
        hist['BB_Middle'] = hist['Close'].rolling(window=20).mean()
        bb_std = hist['Close'].rolling(window=20).std()
        hist['BB_Upper'] = hist['BB_Middle'] + (bb_std * 2)
        hist['BB_Lower'] = hist['BB_Middle'] - (bb_std * 2)
        
        return hist
    
    def calculate_forecast(self, data, metrics, score, days=30):
        """Calculate price forecast and probability based on multiple factors
        Returns forecasts for multiple time periods: 1, 3, 6, and 12 months
        """
        if not data or not metrics or not score:
            return None
        
        hist = data.get('history')
        if hist is None or len(hist) == 0:
            return None
        
        current_price = metrics.get('Current Price', 0)
        if current_price == 0:
            return None
        
        # Calculate trend from moving averages
        trend_score = 0
        if len(hist) > 50 and 'SMA_20' in hist.columns and 'SMA_50' in hist.columns:
            if current_price > hist['SMA_20'].iloc[-1] > hist['SMA_50'].iloc[-1]:
                trend_score = 1  # Bullish
            elif current_price < hist['SMA_20'].iloc[-1] < hist['SMA_50'].iloc[-1]:
                trend_score = -1  # Bearish
        
        # Calculate momentum (recent price change)
        if len(hist) >= 20:
            price_20_days_ago = hist['Close'].iloc[-20]
            momentum = ((current_price - price_20_days_ago) / price_20_days_ago) * 100
        else:
            momentum = 0
        
        # Calculate volatility (annualized)
        if len(hist) >= 20:
            daily_returns = hist['Close'].pct_change().dropna()
            volatility = daily_returns.std() * (252 ** 0.5) * 100  # Annualized volatility %
        else:
            volatility = 0
        
        # Combine factors for forecast
        # Weight: Score (40%), Trend (20%), Momentum (20%), Fundamentals (20%)
        score_factor = score['total_score'] / 100  # 0-1
        
        # Normalize momentum (-10% to +10% maps to -1 to +1)
        momentum_factor = max(-1, min(1, momentum / 10))
        
        # Fundamental growth factor
        revenue_growth = metrics.get('Revenue Growth', 0)
        earnings_growth = metrics.get('Earnings Growth', 0)
        avg_growth = (revenue_growth + earnings_growth) / 2 if (revenue_growth and earnings_growth) else revenue_growth or earnings_growth or 0
        growth_factor = 1 if avg_growth > 5 else -0.5 if avg_growth < -5 else avg_growth / 10
        
        # Overall forecast direction (-1 to +1)
        forecast_direction = (score_factor * 0.4 + trend_score * 0.2 + momentum_factor * 0.2 + 
                              max(-1, min(1, growth_factor)) * 0.2)
        
        # Calculate expected annual return based on forecast direction and volatility
        # Adjust for time horizon: shorter periods are more uncertain
        annual_return_estimate = forecast_direction * (abs(momentum) * 0.5 + abs(avg_growth) * 0.3)
        
        # Time periods in months and corresponding days
        time_periods = {
            '1_month': 30,
            '3_months': 90,
            '6_months': 180,
            '12_months': 365
        }
        
        # Calculate forecasts for each time period
        forecasts_by_period = {}
        
        for period_name, days_in_period in time_periods.items():
            # Time decay factor: longer periods have more uncertainty
            time_factor = days_in_period / 365  # Fraction of a year
            
            # Expected return scales with time but with diminishing confidence
            # Shorter periods: higher confidence, more momentum-driven
            # Longer periods: lower confidence, more fundamental-driven
            if days_in_period <= 30:
                # 1 month: momentum and trend weighted more
                expected_change_pct = forecast_direction * abs(momentum) * 0.6
                confidence_factor = 0.85
            elif days_in_period <= 90:
                # 3 months: balanced
                expected_change_pct = annual_return_estimate * time_factor * 1.2
                confidence_factor = 0.75
            elif days_in_period <= 180:
                # 6 months: fundamentals weighted more
                expected_change_pct = annual_return_estimate * time_factor * 1.1
                confidence_factor = 0.65
            else:
                # 12 months: mostly fundamentals
                expected_change_pct = annual_return_estimate * time_factor
                confidence_factor = 0.55
            
            # Add volatility band (uncertainty increases with time)
            volatility_impact = (volatility / 100) * time_factor * 0.5
            
            # Calculate forecast price
            forecast_price = current_price * (1 + expected_change_pct / 100)
            
            # Calculate probability (confidence decreases with time)
            base_probability = score['total_score'] / 100  # 0-100%
            
            # Adjust based on momentum consistency
            if (momentum > 0 and trend_score > 0) or (momentum < 0 and trend_score < 0):
                consistency_bonus = 0.1
            else:
                consistency_bonus = -0.1
            
            # Apply time-based confidence decay
            probability = min(95, max(20, (base_probability + consistency_bonus) * 100 * confidence_factor))
            
            # Calculate upper and lower bounds (forecast ± volatility)
            upper_bound = forecast_price * (1 + volatility_impact)
            lower_bound = forecast_price * (1 - volatility_impact)
            
            forecasts_by_period[period_name] = {
                'days': days_in_period,
                'forecast_price': forecast_price,
                'forecast_change_pct': expected_change_pct,
                'probability': probability,
                'upper_bound': upper_bound,
                'lower_bound': lower_bound,
                'confidence': confidence_factor * 100
            }
        
        # Determine overall forecast type based on 12-month forecast
        forecast_12m = forecasts_by_period['12_months']['forecast_price']
        if forecast_12m > current_price * 1.15:
            forecast_type = "Strong Buy"
        elif forecast_12m > current_price * 1.05:
            forecast_type = "Buy"
        elif forecast_12m > current_price * 0.95:
            forecast_type = "Hold"
        elif forecast_12m > current_price * 0.85:
            forecast_type = "Reduce"
        else:
            forecast_type = "Sell"
        
        return {
            'current_price': current_price,
            'forecast_price': forecasts_by_period['1_month']['forecast_price'],  # Default to 1 month for backward compatibility
            'forecast_change_pct': forecasts_by_period['1_month']['forecast_change_pct'],
            'forecast_type': forecast_type,
            'probability': forecasts_by_period['1_month']['probability'],
            'momentum': momentum,
            'volatility': volatility,
            'trend': 'Bullish' if trend_score > 0 else 'Bearish' if trend_score < 0 else 'Neutral',
            'forecasts_by_period': forecasts_by_period,
            'annual_return_estimate': annual_return_estimate
        }

