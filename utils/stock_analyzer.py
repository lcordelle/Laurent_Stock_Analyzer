"""
Stock Analyzer Core Engine
Handles all stock data fetching, scoring, and analysis logic
Simplified for local use with Yahoo Finance
"""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf
from utils.ticker_resolver import resolve_to_ticker
from utils.alpha_vantage_client import AlphaVantageClient
import pandas as pd
import numpy as np
import warnings
import time
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class StockAnalyzer:
    """Advanced Stock Analysis Engine"""

    _cache: dict = {}  # class-level — shared across all instances (warmer + Streamlit sessions)

    def __init__(self):
        pass
    
    def get_stock_data(self, ticker, period="1y"):
        """Fetch stock data.
        History: yfinance (full period). Fundamentals + price: Alpha Vantage (OVERVIEW + GLOBAL_QUOTE).
        On yfinance failure: stale disk cache. AV results cached to disk (respects 25 req/day limit)."""
        import os, json
        from pathlib import Path
        from datetime import datetime as _dt

        query = str(ticker).strip()
        resolved = resolve_to_ticker(query)
        ticker = resolved if resolved else query.upper()

        cache_key = f"{ticker}_{period}"
        if cache_key in StockAnalyzer._cache:
            entry = StockAnalyzer._cache[cache_key]
            if time.time() - entry.get('timestamp', 0) < 1800:
                return entry['data']

        disk_cache_dir = Path.home() / '.cache' / 'stock_analyzer' / 'yf_cache'
        disk_cache_dir.mkdir(parents=True, exist_ok=True)
        disk_cache_path = disk_cache_dir / f"{ticker}_{period}.json"
        av_key = os.environ.get('ALPHA_VANTAGE_API_KEY', '')

        def _enrich_with_av(info: dict) -> tuple[dict, str]:
            """Merge AV OVERVIEW + GLOBAL_QUOTE into info dict.
            Returns (merged_info, data_source_label)."""
            if not av_key:
                return info, 'yfinance'
            av = AlphaVantageClient(api_key=av_key)
            av_info = dict(info)
            sources = ['yfinance']
            try:
                overview, _, _ = av.get_company_overview(ticker)
                if overview.get('name'):
                    # AV OVERVIEW is the authoritative fundamentals source
                    for k in ('sector', 'industry', 'marketCap', 'trailingPE', 'forwardPE',
                              'pegRatio', 'priceToBook', 'beta', 'dividendYield',
                              'fiftyTwoWeekHigh', 'fiftyTwoWeekLow', '52WeekHigh', '52WeekLow',
                              'operatingMargins', 'profitMargins', 'returnOnEquity', 'returnOnAssets',
                              'revenueGrowth', 'earningsGrowth', 'debtToEquity',
                              'currentRatio', 'quickRatio', 'targetMeanPrice',
                              'longName', 'longBusinessSummary', 'description'):
                        if overview.get(k):
                            av_info[k] = overview[k]
                    sources.append('Alpha Vantage')
            except Exception:
                pass
            try:
                quote, _, _ = av.get_quote(ticker)
                if quote.get('currentPrice'):
                    av_info['currentPrice'] = quote['currentPrice']
                    av_info['regularMarketPrice'] = quote['currentPrice']
                    if 'Alpha Vantage' not in sources:
                        sources.append('Alpha Vantage')
            except Exception:
                pass
            return av_info, ' + '.join(sources)

        try:
            stock = yf.Ticker(ticker)

            def _get(future, default=None):
                try:
                    v = future.result()
                    return v if v is not None else (default if default is not None else pd.DataFrame())
                except Exception:
                    return default if default is not None else pd.DataFrame()

            with ThreadPoolExecutor(max_workers=5) as pool:
                f_hist = pool.submit(lambda: stock.history(period=period))
                f_info = pool.submit(lambda: stock.info)
                f_fin  = pool.submit(lambda: stock.financials)
                f_bs   = pool.submit(lambda: stock.balance_sheet)
                f_cf   = pool.submit(lambda: stock.cashflow)

            hist          = _get(f_hist, pd.DataFrame())
            info          = _get(f_info, {})
            financials    = _get(f_fin,  pd.DataFrame())
            balance_sheet = _get(f_bs,   pd.DataFrame())
            cash_flow     = _get(f_cf,   pd.DataFrame())

            if hist is None or len(hist) == 0:
                raise Exception("no_data")

            # Supplement empty info from disk cache (e.g. yfinance rate-limited)
            if len(info) < 5 and disk_cache_path.exists():
                try:
                    _disk = json.loads(disk_cache_path.read_text())
                    if len(_disk.get('info', {})) > 5:
                        info = _disk['info']
                except Exception:
                    pass

            data_source = 'yfinance'

            # Persist yfinance info to disk immediately for stale fallback
            try:
                disk_cache_path.write_text(json.dumps({
                    '_ts': time.time(), '_cached_at': _dt.utcnow().isoformat(),
                    'info': {k: v for k, v in info.items() if isinstance(v, (str, int, float, bool, type(None)))},
                }))
            except Exception:
                pass

            # AV enrichment runs in background — overwrites disk cache when done; next request picks it up
            if av_key:
                def _enrich_async(info_copy=dict(info), dpath=disk_cache_path):
                    enriched, _ = _enrich_with_av(info_copy)
                    try:
                        dpath.write_text(json.dumps({
                            '_ts': time.time(), '_cached_at': _dt.utcnow().isoformat(),
                            'info': {k: v for k, v in enriched.items() if isinstance(v, (str, int, float, bool, type(None)))},
                        }))
                    except Exception:
                        pass
                threading.Thread(target=_enrich_async, daemon=True).start()

            result = {
                'ticker': ticker, 'history': hist, 'info': info,
                'financials': financials, 'balance_sheet': balance_sheet,
                'cash_flow': cash_flow, 'stock_object': stock,
                'data_source': data_source, 'cached_at': None, 'is_stale': False,
            }
            StockAnalyzer._cache[cache_key] = {'data': result, 'timestamp': time.time()}
            return result

        except Exception as live_err:
            if 'no_data' in str(live_err):
                return {"error": "no_data", "ticker": ticker}

            logger.warning("yfinance failed for %s (%s), trying stale cache", ticker, live_err)

            if disk_cache_path.exists():
                try:
                    cached = json.loads(disk_cache_path.read_text())
                    cached_info = cached.get('info', {})
                    cached_at = cached.get('_cached_at')
                    hist = None
                    if av_key:
                        try:
                            av = AlphaVantageClient(api_key=av_key)
                            hist, _, _ = av.get_historical_data(ticker, 'compact')
                        except Exception:
                            pass
                    if hist is None or len(hist) == 0:
                        return {"error": str(live_err), "ticker": ticker}
                    result = {
                        'ticker': ticker, 'history': hist, 'info': cached_info,
                        'financials': pd.DataFrame(), 'balance_sheet': pd.DataFrame(),
                        'cash_flow': pd.DataFrame(), 'stock_object': None,
                        'data_source': 'Alpha Vantage (stale cache)',
                        'cached_at': cached_at, 'is_stale': True,
                    }
                    StockAnalyzer._cache[cache_key] = {'data': result, 'timestamp': time.time()}
                    return result
                except Exception:
                    pass

            logger.error("All data sources failed for %s: %s", ticker, live_err)
            return {"error": str(live_err), "ticker": ticker}

    def calculate_score(self, data):
        """Calculate comprehensive stock score (0-100)"""
        if not data or "error" in data:
            return None
        
        info = data['info']
        score = 0
        max_score = 100
        components = {}
        
        # Profitability Score (25 points)
        try:
            gm = info.get('grossMargins')
            if gm is not None and not pd.isna(gm):
                gross_margin = float(gm) * 100
                if gross_margin > 60:
                    score += 25; components['Gross Margin'] = 25
                elif gross_margin > 40:
                    score += 15; components['Gross Margin'] = 15
                elif gross_margin > 20:
                    score += 10; components['Gross Margin'] = 10
                else:
                    score += 5; components['Gross Margin'] = 5
            else:
                components['Gross Margin'] = 0
        except (TypeError, ValueError, AttributeError) as e:
            logger.warning("Gross margin scoring failed: %s", e)
            components['Gross Margin'] = 0

        # ROE Score (20 points)
        try:
            roe_raw = info.get('returnOnEquity')
            if roe_raw is not None and not pd.isna(roe_raw):
                roe = float(roe_raw) * 100
                if roe > 20:
                    score += 20; components['ROE'] = 20
                elif roe > 15:
                    score += 15; components['ROE'] = 15
                elif roe > 10:
                    score += 10; components['ROE'] = 10
                else:
                    score += 5; components['ROE'] = 5
            else:
                components['ROE'] = 0
        except (TypeError, ValueError, AttributeError) as e:
            logger.warning("ROE scoring failed: %s", e)
            components['ROE'] = 0

        # FCF Margin Score (20 points)
        try:
            fcf = info.get('freeCashflow')
            rev = info.get('totalRevenue')
            if fcf is not None and rev is not None and not pd.isna(fcf) and not pd.isna(rev) and float(rev) != 0:
                fcf_margin = float(fcf) / float(rev) * 100
                if fcf_margin > 15:
                    score += 20; components['FCF Margin'] = 20
                elif fcf_margin > 10:
                    score += 15; components['FCF Margin'] = 15
                elif fcf_margin > 5:
                    score += 10; components['FCF Margin'] = 10
                else:
                    score += 5; components['FCF Margin'] = 5
            else:
                components['FCF Margin'] = 0
        except (TypeError, ValueError, ZeroDivisionError, AttributeError) as e:
            logger.warning("FCF margin scoring failed: %s", e)
            components['FCF Margin'] = 0

        # Valuation Score (20 points)
        try:
            pe = info.get('trailingPE')
            if pe is not None and not pd.isna(pe):
                pe_ratio = float(pe)
                if 10 < pe_ratio < 25:
                    score += 20; components['Valuation'] = 20
                elif 5 < pe_ratio < 35:
                    score += 15; components['Valuation'] = 15
                elif pe_ratio < 50:
                    score += 10; components['Valuation'] = 10
                else:
                    score += 5; components['Valuation'] = 5
            else:
                components['Valuation'] = 0
        except (TypeError, ValueError, AttributeError) as e:
            logger.warning("Valuation scoring failed: %s", e)
            components['Valuation'] = 0

        # Growth Score (15 points)
        try:
            rg = info.get('revenueGrowth')
            if rg is not None and not pd.isna(rg):
                revenue_growth = float(rg) * 100
                if revenue_growth > 20:
                    score += 15; components['Growth'] = 15
                elif revenue_growth > 10:
                    score += 10; components['Growth'] = 10
                elif revenue_growth > 0:
                    score += 5; components['Growth'] = 5
                else:
                    components['Growth'] = 0
            else:
                components['Growth'] = 0
        except (TypeError, ValueError, AttributeError) as e:
            logger.warning("Growth scoring failed: %s", e)
            components['Growth'] = 0
        
        # Debt quality modifier
        try:
            de = info.get('debtToEquity')
            if de is not None and not pd.isna(de):
                d = float(de)
                if d > 300:
                    score -= 10; components['Debt Penalty'] = -10
                elif d > 150:
                    score -= 5; components['Debt Penalty'] = -5
                elif d < 50:
                    score += 5; components['Debt Bonus'] = 5
        except Exception:
            pass

        return {
            'total_score': min(max(score, 0), max_score),
            'components': components,
            'max_score': max_score
        }
    
    def get_key_metrics(self, data):
        """Extract key financial metrics"""
        if not data or "error" in data:
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
            'Dividend Yield': info.get('trailingAnnualDividendYield', 0) * 100 if info.get('trailingAnnualDividendYield') else 0,
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
            'Number of Analysts': info.get('numberOfAnalystOpinions', 0),
            # Yahoo: lower = more bullish (~1 strong buy .. ~5 strong sell); ~3 neutral
            'recommendationMean': info.get('recommendationMean'),
            '52 Week High': info.get('fiftyTwoWeekHigh'),
            '52 Week Low': info.get('fiftyTwoWeekLow'),
        }
        
        return metrics
    
    def calculate_technical_indicators(self, hist):
        """Calculate technical indicators including Stochastic, ADX, and Ichimoku"""
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
        
        # Stochastic Oscillator (14-period)
        if len(hist) >= 14:
            low_14 = hist['Low'].rolling(window=14).min()
            high_14 = hist['High'].rolling(window=14).max()
            hist['Stoch_K'] = 100 * ((hist['Close'] - low_14) / (high_14 - low_14))
            hist['Stoch_D'] = hist['Stoch_K'].rolling(window=3).mean()
        
        # ADX (Average Directional Index) - 14-period
        if len(hist) >= 28:
            # Calculate True Range
            hist['TR'] = pd.concat([
                hist['High'] - hist['Low'],
                abs(hist['High'] - hist['Close'].shift()),
                abs(hist['Low'] - hist['Close'].shift())
            ], axis=1).max(axis=1)
            
            # Calculate Directional Movement
            hist['DM_Plus'] = np.where(
                (hist['High'] - hist['High'].shift()) > (hist['Low'].shift() - hist['Low']),
                np.maximum(hist['High'] - hist['High'].shift(), 0),
                0
            )
            hist['DM_Minus'] = np.where(
                (hist['Low'].shift() - hist['Low']) > (hist['High'] - hist['High'].shift()),
                np.maximum(hist['Low'].shift() - hist['Low'], 0),
                0
            )
            
            # Smooth the values
            period = 14
            hist['TR_Smooth'] = hist['TR'].rolling(window=period).sum()
            hist['DM_Plus_Smooth'] = hist['DM_Plus'].rolling(window=period).sum()
            hist['DM_Minus_Smooth'] = hist['DM_Minus'].rolling(window=period).sum()
            
            # Calculate DI+ and DI-
            hist['DI_Plus'] = 100 * (hist['DM_Plus_Smooth'] / hist['TR_Smooth'])
            hist['DI_Minus'] = 100 * (hist['DM_Minus_Smooth'] / hist['TR_Smooth'])
            
            # Calculate DX and ADX
            hist['DX'] = 100 * abs(hist['DI_Plus'] - hist['DI_Minus']) / (hist['DI_Plus'] + hist['DI_Minus'])
            hist['ADX'] = hist['DX'].rolling(window=period).mean()
        
        # Ichimoku Cloud
        if len(hist) >= 52:
            # Tenkan-sen (Conversion Line): (9-period high + 9-period low) / 2
            period1 = 9
            period2 = 26
            period3 = 52
            
            hist['Ichimoku_Tenkan'] = (hist['High'].rolling(window=period1).max() + 
                                       hist['Low'].rolling(window=period1).min()) / 2
            
            # Kijun-sen (Base Line): (26-period high + 26-period low) / 2
            hist['Ichimoku_Kijun'] = (hist['High'].rolling(window=period2).max() + 
                                     hist['Low'].rolling(window=period2).min()) / 2
            
            # Senkou Span A (Leading Span A): (Tenkan + Kijun) / 2, shifted 26 periods forward
            hist['Ichimoku_Senkou_A'] = ((hist['Ichimoku_Tenkan'] + hist['Ichimoku_Kijun']) / 2).shift(period2)
            
            # Senkou Span B (Leading Span B): (52-period high + 52-period low) / 2, shifted 26 periods forward
            hist['Ichimoku_Senkou_B'] = ((hist['High'].rolling(window=period3).max() + 
                                         hist['Low'].rolling(window=period3).min()) / 2).shift(period2)
            
            # Chikou Span (Lagging Span): Close price shifted 26 periods backward
            hist['Ichimoku_Chikou'] = hist['Close'].shift(-period2)

        # OBV (On-Balance Volume) — cumulative volume direction indicator
        hist['OBV'] = (np.sign(hist['Close'].diff()).fillna(0) * hist['Volume']).cumsum()

        # VWAP — 20-day rolling (meaningful for swing traders on daily data)
        typical_price = (hist['High'] + hist['Low'] + hist['Close']) / 3
        hist['VWAP'] = (
            (typical_price * hist['Volume']).rolling(20).sum() /
            hist['Volume'].rolling(20).sum()
        )

        return hist
    
    def calculate_forecast(self, data, metrics, score, days=30):
        """Calculate price forecast and probability based on multiple factors"""
        if not data or "error" in data or not metrics or not score:
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
        score_factor = score['total_score'] / 100  # 0-1
        momentum_factor = max(-1, min(1, momentum / 10))
        revenue_growth = metrics.get('Revenue Growth', 0)
        earnings_growth = metrics.get('Earnings Growth', 0)
        avg_growth = (revenue_growth + earnings_growth) / 2 if (revenue_growth and earnings_growth) else revenue_growth or earnings_growth or 0
        growth_factor = 1 if avg_growth > 5 else -0.5 if avg_growth < -5 else avg_growth / 10
        
        forecast_direction = (score_factor * 0.4 + trend_score * 0.2 + momentum_factor * 0.2 + 
                              max(-1, min(1, growth_factor)) * 0.2)
        
        annual_return_estimate = forecast_direction * (abs(momentum) * 0.5 + abs(avg_growth) * 0.3)
        
        # Calculate forecast for 1 month
        time_factor = days / 365
        expected_change_pct = annual_return_estimate * time_factor
        forecast_price = current_price * (1 + expected_change_pct / 100)
        
        # Calculate probability
        base_probability = score['total_score'] / 100
        if (momentum > 0 and trend_score > 0) or (momentum < 0 and trend_score < 0):
            consistency_bonus = 0.1
        else:
            consistency_bonus = -0.1
        
        probability = min(95, max(20, (base_probability + consistency_bonus) * 100 * 0.85))
        
        # Determine forecast type
        if forecast_price > current_price * 1.15:
            forecast_type = "Strong Buy"
        elif forecast_price > current_price * 1.05:
            forecast_type = "Buy"
        elif forecast_price > current_price * 0.95:
            forecast_type = "Hold"
        elif forecast_price > current_price * 0.85:
            forecast_type = "Reduce"
        else:
            forecast_type = "Sell"
        
        return {
            'current_price': current_price,
            'forecast_price': forecast_price,
            'forecast_change_pct': expected_change_pct,
            'forecast_type': forecast_type,
            'probability': probability,
            'momentum': momentum,
            'volatility': volatility,
            'trend': 'Bullish' if trend_score > 0 else 'Bearish' if trend_score < 0 else 'Neutral'
        }
