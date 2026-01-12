"""
Advanced Financial Elements
Insider trading, dividends, short interest, analyst data, and more
"""

import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class AdvancedFinancials:
    """Advanced financial data and analysis"""
    
    def __init__(self):
        self.cache = {}
    
    def get_insider_transactions(self, ticker: str) -> pd.DataFrame:
        """Get insider trading data"""
        try:
            stock = yf.Ticker(ticker)
            
            # Get insider transactions
            try:
                insider = stock.insider_transactions
                if insider is not None and len(insider) > 0:
                    return insider.head(20)  # Last 20 transactions
            except:
                pass
            
            # Try alternative method
            try:
                major_holders = stock.major_holders
                institutional_holders = stock.institutional_holders
                
                if institutional_holders is not None and len(institutional_holders) > 0:
                    return institutional_holders.head(10)
            except:
                pass
            
            return pd.DataFrame()
        except:
            return pd.DataFrame()
    
    def get_dividend_data(self, ticker: str) -> Dict:
        """Get comprehensive dividend information"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period='5y')
            
            dividend_data = {
                'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                'dividend_rate': info.get('dividendRate', 0),
                'ex_dividend_date': info.get('exDividendDate', None),
                'payout_ratio': info.get('payoutRatio', 0) * 100 if info.get('payoutRatio') else 0,
                'dividend_history': [],
                'annual_dividend': 0,
                'dividend_growth': 0
            }
            
            # Get dividend history
            try:
                dividends = stock.dividends
                if dividends is not None and len(dividends) > 0:
                    # Last 12 months
                    recent_dividends = dividends.tail(12)
                    dividend_data['dividend_history'] = recent_dividends.to_dict()
                    
                    # Annual dividend
                    last_year = dividends.tail(4)
                    dividend_data['annual_dividend'] = last_year.sum()
                    
                    # Dividend growth (comparing last 4 vs previous 4)
                    if len(dividends) >= 8:
                        recent_4 = dividends.tail(4).sum()
                        previous_4 = dividends.tail(8).head(4).sum()
                        if previous_4 > 0:
                            dividend_data['dividend_growth'] = ((recent_4 - previous_4) / previous_4) * 100
            except:
                pass
            
            return dividend_data
        except:
            return {}
    
    def get_short_interest(self, ticker: str) -> Dict:
        """Get short interest data"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            short_data = {
                'short_ratio': info.get('shortRatio', 0),
                'short_percent_of_float': info.get('sharesShort', 0) / info.get('sharesOutstanding', 1) * 100 if info.get('sharesOutstanding') else 0,
                'shares_short': info.get('sharesShort', 0),
                'shares_short_prior_month': info.get('sharesShortPriorMonth', 0),
                'short_percent_change': 0
            }
            
            # Calculate change
            if short_data['shares_short'] > 0 and short_data['shares_short_prior_month'] > 0:
                short_data['short_percent_change'] = ((short_data['shares_short'] - short_data['shares_short_prior_month']) / short_data['shares_short_prior_month']) * 100
            
            return short_data
        except:
            return {}
    
    def get_analyst_data(self, ticker: str) -> Dict:
        """Get comprehensive analyst data"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            analyst_data = {
                'recommendation': info.get('recommendationKey', 'N/A'),
                'recommendation_mean': info.get('recommendationMean', 0),
                'number_of_analysts': info.get('numberOfAnalystOpinions', 0),
                'target_price': info.get('targetMeanPrice', 0),
                'target_high': info.get('targetHighPrice', 0),
                'target_low': info.get('targetLowPrice', 0),
                'current_price': info.get('currentPrice', 0),
                'upside_potential': 0,
                'price_targets': {}
            }
            
            # Calculate upside potential
            if analyst_data['target_price'] > 0 and analyst_data['current_price'] > 0:
                analyst_data['upside_potential'] = ((analyst_data['target_price'] - analyst_data['current_price']) / analyst_data['current_price']) * 100
            
            # Get price targets breakdown
            try:
                recommendations = stock.recommendations
                if recommendations is not None:
                    analyst_data['price_targets']['breakdown'] = recommendations.tail(10).to_dict('records')
            except:
                pass
            
            return analyst_data
        except:
            return {}
    
    def get_institutional_holdings(self, ticker: str) -> pd.DataFrame:
        """Get institutional holdings"""
        try:
            stock = yf.Ticker(ticker)
            
            try:
                institutional = stock.institutional_holders
                if institutional is not None and len(institutional) > 0:
                    return institutional.head(15)
            except:
                pass
            
            # Alternative: major holders
            try:
                major = stock.major_holders
                if major is not None:
                    return pd.DataFrame(major)
            except:
                pass
            
            return pd.DataFrame()
        except:
            return pd.DataFrame()
    
    def get_sector_peers(self, ticker: str) -> List[str]:
        """Get sector peers for comparison"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            sector = info.get('sector', '')
            industry = info.get('industry', '')
            
            # Common sector mappings
            sector_tickers = {
                'Technology': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'ORCL', 'CSCO', 'INTC', 'AMD'],
                'Financial Services': ['JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'SCHW', 'BLK', 'AXP', 'V'],
                'Healthcare': ['JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'ABT', 'DHR', 'BMY', 'AMGN', 'GILD'],
                'Consumer Cyclical': ['AMZN', 'TSLA', 'HD', 'NKE', 'SBUX', 'MCD', 'LOW', 'TGT', 'WMT', 'F'],
                'Consumer Defensive': ['WMT', 'PG', 'KO', 'PEP', 'COST', 'CL', 'MDLZ', 'GIS', 'KMB', 'TGT']
            }
            
            for sector_name, tickers in sector_tickers.items():
                if sector_name.lower() in sector.lower() or sector.lower() in sector_name.lower():
                    # Remove current ticker if present
                    peers = [t for t in tickers if t != ticker.upper()]
                    return peers[:5]  # Return top 5 peers
            
            return []
        except:
            return []
    
    def get_esg_score(self, ticker: str) -> Dict:
        """Get ESG (Environmental, Social, Governance) score"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            esg_data = {
                'environment_score': info.get('environmentScore', None),
                'social_score': info.get('socialScore', None),
                'governance_score': info.get('governanceScore', None),
                'total_esg_score': info.get('totalEsg', None),
                'controversy_score': info.get('controversyScore', None),
                'esg_percentile': info.get('percentile', None)
            }
            
            return esg_data
        except:
            return {}
    
    def get_company_filings(self, ticker: str) -> List[Dict]:
        """Get recent SEC filings"""
        try:
            stock = yf.Ticker(ticker)
            
            # Try to get filings
            try:
                calendar = stock.calendar
                # yfinance doesn't directly provide filings, but we can mention this
                filings = [{
                    'type': '10-K',
                    'description': 'Annual Report',
                    'note': 'Check SEC EDGAR for detailed filings'
                }]
                return filings
            except:
                return []
        except:
            return []








