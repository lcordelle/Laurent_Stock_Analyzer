"""
Earnings Calendar Utilities
Track earnings dates, history, and estimates
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class EarningsCalendar:
    """Handle earnings calendar and data"""
    
    def __init__(self):
        self.cache = {}
    
    def get_earnings_dates(self, ticker: str) -> Dict:
        """Get earnings dates for a stock"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            earnings_data = {
                'last_earnings_date': None,
                'next_earnings_date': None,
                'earnings_quarter': None,
                'earnings_history': [],
                'analyst_estimates': {}
            }
            
            # Get earnings dates from info (most reliable method)
            if 'earningsDate' in info and info['earningsDate']:
                dates = info['earningsDate']
                if dates and len(dates) >= 1:
                    try:
                        if isinstance(dates[0], (int, float)):
                            earnings_data['last_earnings_date'] = pd.to_datetime(dates[0], unit='s').date()
                        elif isinstance(dates[0], pd.Timestamp):
                            earnings_data['last_earnings_date'] = dates[0].date()
                        else:
                            earnings_data['last_earnings_date'] = pd.to_datetime(dates[0]).date()
                    except:
                        pass
                
                if dates and len(dates) >= 2:
                    try:
                        if isinstance(dates[1], (int, float)):
                            earnings_data['next_earnings_date'] = pd.to_datetime(dates[1], unit='s').date()
                        elif isinstance(dates[1], pd.Timestamp):
                            earnings_data['next_earnings_date'] = dates[1].date()
                        else:
                            earnings_data['next_earnings_date'] = pd.to_datetime(dates[1]).date()
                    except:
                        pass
            
            # Try to get earnings calendar (alternative method)
            if not earnings_data['next_earnings_date']:
                try:
                    calendar = stock.calendar
                    if calendar is not None and len(calendar) > 0:
                        if hasattr(calendar.index[0], 'date'):
                            earnings_data['next_earnings_date'] = calendar.index[0].date()
                        else:
                            earnings_data['next_earnings_date'] = pd.to_datetime(calendar.index[0]).date()
                except:
                    pass
            
            # Get earnings history with proper formatting
            try:
                earnings = stock.earnings_history
                if earnings is not None and len(earnings) > 0:
                    # Convert to list of dicts with standardized keys
                    earnings_list = []
                    for idx, row in earnings.iterrows():
                        earnings_list.append({
                            'Date': idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx),
                            'Actual': row.get('epsActual', row.get('Actual', 0)),
                            'Estimate': row.get('epsEstimate', row.get('Estimate', 0)),
                            'Surprise': row.get('epsDifference', row.get('Surprise', 0)),
                            'Surprise %': row.get('surprisePercent', row.get('Surprise %', 0)) * 100 if row.get('surprisePercent') else (row.get('Surprise %', 0))
                        })
                    earnings_data['earnings_history'] = earnings_list[:5]  # Last 5 quarters
            except Exception as e:
                pass
            
            # Get earnings estimates from info
            try:
                trailing_eps = info.get('trailingEps') or info.get('trailingEps', 0)
                forward_eps = info.get('forwardEps') or info.get('forwardEps', 0)
                earnings_growth = info.get('earningsGrowth')
                
                # Convert earnings growth from decimal to percentage if needed
                if earnings_growth and isinstance(earnings_growth, (int, float)):
                    if earnings_growth < 1 and earnings_growth > -1:  # Likely a decimal
                        earnings_growth = earnings_growth
                    else:
                        earnings_growth = earnings_growth / 100
                
                earnings_data['analyst_estimates'] = {
                    'eps_estimate': trailing_eps if trailing_eps else 0,
                    'forward_eps': forward_eps if forward_eps else 0,
                    'eps_growth': earnings_growth if earnings_growth else 0
                }
            except Exception as e:
                earnings_data['analyst_estimates'] = {
                    'eps_estimate': 0,
                    'forward_eps': 0,
                    'eps_growth': 0
                }
            
            return earnings_data
        except Exception as e:
            return {
                'last_earnings_date': None,
                'next_earnings_date': None,
                'earnings_quarter': None,
                'earnings_history': [],
                'analyst_estimates': {}
            }
    
    def get_upcoming_earnings(self, days_ahead: int = 30) -> pd.DataFrame:
        """Get stocks with upcoming earnings in next N days"""
        # Major stocks to check
        major_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'JPM', 'JNJ', 'V', 
                       'PG', 'MA', 'HD', 'DIS', 'NFLX', 'AMD', 'INTC', 'CSCO', 'ORCL', 'CRM']
        
        upcoming = []
        today = datetime.now().date()
        end_date = today + timedelta(days=days_ahead)
        
        for ticker in major_stocks:
            try:
                earnings_data = self.get_earnings_dates(ticker)
                next_date = earnings_data.get('next_earnings_date')
                
                if next_date:
                    if isinstance(next_date, pd.Timestamp):
                        next_date = next_date.date()
                    elif isinstance(next_date, (int, float)):
                        next_date = pd.to_datetime(next_date).date()
                    
                    if today <= next_date <= end_date:
                        stock = yf.Ticker(ticker)
                        info = stock.info
                        upcoming.append({
                            'Ticker': ticker,
                            'Company': info.get('longName', ticker),
                            'Earnings Date': next_date,
                            'Days Until': (next_date - today).days,
                            'Last Close': stock.history(period='1d')['Close'].iloc[-1] if len(stock.history(period='1d')) > 0 else 0
                        })
            except:
                continue
        
        df = pd.DataFrame(upcoming)
        if len(df) > 0:
            df = df.sort_values('Earnings Date')
        return df
    
    def get_earnings_surprises(self, ticker: str) -> pd.DataFrame:
        """Get earnings surprises history"""
        try:
            stock = yf.Ticker(ticker)
            earnings = stock.earnings_history
            
            if earnings is not None and len(earnings) > 0:
                surprises = []
                for idx, row in earnings.iterrows():
                    # Handle different data formats from yfinance
                    actual = row.get('epsActual', row.get('Actual', 0))
                    estimate = row.get('epsEstimate', row.get('Estimate', 0))
                    surprise_diff = row.get('epsDifference', row.get('Surprise', 0))
                    
                    # Get surprise percentage (can be in different formats)
                    surprise_pct = 0
                    if 'surprisePercent' in row:
                        surprise_pct = row['surprisePercent'] * 100  # Convert from decimal
                    elif 'Surprise %' in row:
                        surprise_pct = row['Surprise %']
                    elif actual and estimate:
                        # Calculate manually if not provided
                        surprise_pct = ((actual - estimate) / estimate) * 100 if estimate != 0 else 0
                    
                    surprises.append({
                        'Date': idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx),
                        'Actual': actual,
                        'Estimate': estimate,
                        'Surprise': surprise_diff,
                        'Surprise %': surprise_pct
                    })
                
                df = pd.DataFrame(surprises)
                if len(df) > 0:
                    df = df.sort_values('Date', ascending=False)
                return df
            return pd.DataFrame(columns=['Date', 'Actual', 'Estimate', 'Surprise', 'Surprise %'])
        except Exception as e:
            return pd.DataFrame(columns=['Date', 'Actual', 'Estimate', 'Surprise', 'Surprise %'])

