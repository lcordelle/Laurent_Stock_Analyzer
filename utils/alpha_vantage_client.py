"""
Alpha Vantage Data Client
Fetches stock data from Alpha Vantage API as alternative to Yahoo Finance
"""

import requests
import pandas as pd
import numpy as np
import time
import os
import json
from pathlib import Path
from datetime import datetime, timedelta

# TTLs for disk cache by function type
_CACHE_TTL = {
    'GLOBAL_QUOTE': 4 * 3600,
    'OVERVIEW': 24 * 3600,
    'TIME_SERIES_DAILY': 7 * 24 * 3600,
    'INCOME_STATEMENT': 7 * 24 * 3600,
    'BALANCE_SHEET': 7 * 24 * 3600,
    'CASH_FLOW': 7 * 24 * 3600,
}
_CACHE_DIR = Path.home() / '.cache' / 'stock_analyzer' / 'av_cache'

class AlphaVantageClient:
    """Client for fetching data from Alpha Vantage API"""

    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('ALPHA_VANTAGE_API_KEY', '')
        self.base_url = 'https://www.alphavantage.co/query'
        self.last_request_time = 0
        self.min_request_interval = 12.1  # Alpha Vantage free tier: 5 calls/min = 12 seconds between calls
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, function: str, symbol: str) -> Path:
        return _CACHE_DIR / f"{symbol.upper()}_{function}.json"

    def _read_cache(self, function: str, symbol: str):
        """Return (data, cached_at_iso, is_expired) or None if no cache file."""
        path = self._cache_path(function, symbol)
        if not path.exists():
            return None
        try:
            entry = json.loads(path.read_text())
            cached_at = entry['_cached_at']
            age = time.time() - entry['_ts']
            ttl = _CACHE_TTL.get(function, 24 * 3600)
            return entry['data'], cached_at, age > ttl
        except Exception:
            return None

    def _write_cache(self, function: str, symbol: str, data: dict) -> None:
        path = self._cache_path(function, symbol)
        entry = {'_ts': time.time(), '_cached_at': datetime.utcnow().isoformat(), 'data': data}
        path.write_text(json.dumps(entry))
        
    def _rate_limit(self):
        """Enforce rate limiting (5 calls per minute for free tier)"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _make_request(self, function, symbol, **params):
        """Make API request. Returns (data, cached_at_iso, is_stale).
        On rate-limit or error, falls back to disk cache if available."""
        self._rate_limit()

        req_params = {
            'function': function,
            'symbol': symbol,
            'apikey': self.api_key,
            'datatype': 'json',
            **params,
        }

        try:
            response = requests.get(self.base_url, params=req_params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if 'Error Message' in data:
                raise Exception(f"Alpha Vantage Error: {data['Error Message']}")
            if 'Note' in data or 'Information' in data:
                raise Exception(f"Alpha Vantage Rate Limit: {data.get('Note') or data.get('Information')}")
            if not data:
                raise Exception("Alpha Vantage empty response")

            self._write_cache(function, symbol, data)
            return data, datetime.utcnow().isoformat(), False

        except Exception as e:
            import sys
            print(f"[Alpha Vantage] ⚠️ Live fetch failed ({function}/{symbol}): {e} — trying cache", file=sys.stderr)
            cached = self._read_cache(function, symbol)
            if cached:
                data, cached_at, _ = cached
                return data, cached_at, True
            raise
    
    def get_historical_data(self, symbol, period='1y'):
        """Returns (DataFrame|None, cached_at_iso, is_stale)."""
        period_map = {
            '1d': 'compact', '5d': 'compact', '1mo': 'compact',
            '3mo': 'compact', '6mo': 'compact', '1y': 'compact',
            '2y': 'compact', '5y': 'compact', 'max': 'compact',
            'compact': 'compact',
        }
        outputsize = period_map.get(period, 'compact')
        data, cached_at, is_stale = self._make_request('TIME_SERIES_DAILY', symbol, outputsize=outputsize)

        if 'Time Series (Daily)' not in data:
            return None, cached_at, is_stale

        df_data = []
        for date_str, values in data['Time Series (Daily)'].items():
            try:
                close = float(values.get('4. close', 0))
                df_data.append({
                    'Date': pd.to_datetime(date_str),
                    'Open': float(values.get('1. open', 0)),
                    'High': float(values.get('2. high', 0)),
                    'Low': float(values.get('3. low', 0)),
                    'Close': close,
                    'Adj Close': close,
                    'Volume': int(float(values.get('5. volume', 0))),
                })
            except (ValueError, KeyError):
                continue

        if not df_data:
            return None, cached_at, is_stale

        df = pd.DataFrame(df_data).set_index('Date').sort_index()
        if len(df) == 0:
            return None, cached_at, is_stale

        if period in ('1d', '5d', '1mo'):
            end_date = df.index[-1]
            delta = {'1d': 1, '5d': 5, '1mo': 30}[period]
            df = df[df.index >= end_date - timedelta(days=delta)]

        return df, cached_at, is_stale

    def get_company_overview(self, symbol):
        """Returns (dict, cached_at_iso, is_stale)."""
        data, cached_at, is_stale = self._make_request('OVERVIEW', symbol)

        if 'Symbol' not in data:
            return {}, cached_at, is_stale

        def _f(k, default=0): return float(data.get(k, default) or default)
        def _pct(k): return _f(k) / 100 if data.get(k) else 0

        overview = {
            'symbol': data.get('Symbol', ''),
            'name': data.get('Name', ''),
            'description': data.get('Description', ''),
            'sector': data.get('Sector', ''),
            'industry': data.get('Industry', ''),
            'marketCap': _f('MarketCapitalization'),
            'currentPrice': _f('52WeekHigh'),
            'trailingPE': _f('PERatio'),
            'forwardPE': _f('ForwardPE'),
            'pegRatio': _f('PEGRatio'),
            'priceToBook': _f('PriceToBookRatio'),
            'dividendYield': _pct('DividendYield'),
            'beta': _f('Beta'),
            '52WeekHigh': _f('52WeekHigh'),
            '52WeekLow': _f('52WeekLow'),
            'fiftyTwoWeekHigh': _f('52WeekHigh'),
            'fiftyTwoWeekLow': _f('52WeekLow'),
            'grossMargins': _f('GrossProfitTTM') / (_f('RevenueTTM') or 1) if data.get('RevenueTTM') else 0,
            'operatingMargins': _pct('OperatingMarginTTM'),
            'profitMargins': _pct('ProfitMargin'),
            'returnOnEquity': _pct('ReturnOnEquityTTM'),
            'returnOnAssets': _pct('ReturnOnAssetsTTM'),
            'revenueGrowth': _pct('QuarterlyRevenueGrowthYOY'),
            'earningsGrowth': _pct('QuarterlyEarningsGrowthYOY'),
            'debtToEquity': _f('DebtToEquity'),
            'currentRatio': _f('CurrentRatio'),
            'quickRatio': _f('QuickRatio'),
            'targetMeanPrice': _f('AnalystTargetPrice'),
            'numberOfAnalystOpinions': int(data.get('AnalystRating', 0) or 0),
            'recommendationKey': data.get('AnalystRating', 'N/A'),
            'volume': int(data.get('Volume', 0) or 0),
            'averageVolume': int(data.get('AverageVolume', 0) or 0),
            'longName': data.get('Name', ''),
            'longBusinessSummary': data.get('Description', ''),
        }
        return overview, cached_at, is_stale

    def get_quote(self, symbol):
        """Returns (dict, cached_at_iso, is_stale)."""
        data, cached_at, is_stale = self._make_request('GLOBAL_QUOTE', symbol)

        if 'Global Quote' not in data:
            return {}, cached_at, is_stale

        q = data['Global Quote']
        result = {
            'currentPrice': float(q.get('05. price', 0) or 0),
            'open': float(q.get('02. open', 0) or 0),
            'high': float(q.get('03. high', 0) or 0),
            'low': float(q.get('04. low', 0) or 0),
            'previousClose': float(q.get('08. previous close', 0) or 0),
            'volume': int(q.get('06. volume', 0) or 0),
            'change': float(q.get('09. change', 0) or 0),
            'changePercent': float(q.get('10. change percent', '0').rstrip('%') or 0) / 100,
        }
        return result, cached_at, is_stale

    def get_income_statement(self, symbol):
        """Returns (DataFrame, cached_at_iso, is_stale)."""
        data, cached_at, is_stale = self._make_request('INCOME_STATEMENT', symbol)
        if 'annualReports' not in data or not data['annualReports']:
            return pd.DataFrame(), cached_at, is_stale
        df = pd.DataFrame(data['annualReports'])
        if 'fiscalDateEnding' in df.columns:
            df['fiscalDateEnding'] = pd.to_datetime(df['fiscalDateEnding'])
            df.set_index('fiscalDateEnding', inplace=True)
            df.sort_index(inplace=True)
        return df, cached_at, is_stale

    def get_balance_sheet(self, symbol):
        """Returns (DataFrame, cached_at_iso, is_stale)."""
        data, cached_at, is_stale = self._make_request('BALANCE_SHEET', symbol)
        if 'annualReports' not in data or not data['annualReports']:
            return pd.DataFrame(), cached_at, is_stale
        df = pd.DataFrame(data['annualReports'])
        if 'fiscalDateEnding' in df.columns:
            df['fiscalDateEnding'] = pd.to_datetime(df['fiscalDateEnding'])
            df.set_index('fiscalDateEnding', inplace=True)
            df.sort_index(inplace=True)
        return df, cached_at, is_stale

    def get_cash_flow(self, symbol):
        """Returns (DataFrame, cached_at_iso, is_stale)."""
        data, cached_at, is_stale = self._make_request('CASH_FLOW', symbol)
        if 'annualReports' not in data or not data['annualReports']:
            return pd.DataFrame(), cached_at, is_stale
        df = pd.DataFrame(data['annualReports'])
        if 'fiscalDateEnding' in df.columns:
            df['fiscalDateEnding'] = pd.to_datetime(df['fiscalDateEnding'])
            df.set_index('fiscalDateEnding', inplace=True)
            df.sort_index(inplace=True)
        return df, cached_at, is_stale
    
    def get_stock_data(self, symbol, period='1y'):
        """Returns (data_dict, cached_at_iso, is_stale) or raises on total failure."""
        any_stale = False
        oldest_cached_at = None

        def _track(cached_at, stale):
            nonlocal any_stale, oldest_cached_at
            if stale:
                any_stale = True
            if cached_at and (oldest_cached_at is None or cached_at < oldest_cached_at):
                oldest_cached_at = cached_at

        hist, ca, stale = self.get_historical_data(symbol, period)
        _track(ca, stale)
        if hist is None or len(hist) == 0:
            raise Exception(f"No historical data for {symbol}")

        current_price = float(hist['Close'].iloc[-1])

        quote = {}
        try:
            quote, ca, stale = self.get_quote(symbol)
            _track(ca, stale)
            if quote.get('currentPrice'):
                current_price = quote['currentPrice']
        except Exception:
            pass

        overview = {}
        try:
            overview, ca, stale = self.get_company_overview(symbol)
            _track(ca, stale)
        except Exception:
            overview = {'symbol': symbol, 'name': symbol}

        overview['currentPrice'] = current_price
        overview['regularMarketPrice'] = current_price

        result = {
            'ticker': symbol.upper(),
            'history': hist,
            'info': overview,
            'financials': pd.DataFrame(),
            'balance_sheet': pd.DataFrame(),
            'cash_flow': pd.DataFrame(),
            'stock_object': None,
        }
        return result, oldest_cached_at or datetime.utcnow().isoformat(), any_stale

