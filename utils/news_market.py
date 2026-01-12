"""
News and Market Context Utilities
Fetches news, market data, and contextual information
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Optional

class NewsMarketData:
    """Handle news and market context data"""
    
    def __init__(self):
        self.cache = {}
    
    def get_stock_news(self, ticker: str, limit: int = 10) -> List[Dict]:
        """Get recent news for a stock"""
        try:
            stock = yf.Ticker(ticker)
            news = []
            
            # Method 1: Try yfinance's built-in news property
            try:
                news = stock.news
                if news is None:
                    news = []
            except Exception:
                news = []
            
            # Method 2: If no news, try direct API call to Yahoo Finance
            if not news or len(news) == 0:
                try:
                    # Try the newer Yahoo Finance API endpoint
                    news_url = f"https://query2.finance.yahoo.com/v2/finance/search?q={ticker}&quotesCount=1&newsCount={limit}"
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': 'application/json',
                        'Accept-Language': 'en-US,en;q=0.9'
                    }
                    response = requests.get(news_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        # Check both possible response structures
                        if 'news' in data and data['news']:
                            news = data['news']
                        elif 'finance' in data and 'result' in data['finance']:
                            finance_result = data['finance']['result']
                            if isinstance(finance_result, list) and len(finance_result) > 0:
                                if 'news' in finance_result[0]:
                                    news = finance_result[0]['news']
                except Exception:
                    pass
            
            # Method 3: Try alternative endpoint (v1 API)
            if not news or len(news) == 0:
                try:
                    news_url = f"https://query1.finance.yahoo.com/v1/finance/search?q={ticker}&quotesCount=1&newsCount={limit}"
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': 'application/json'
                    }
                    response = requests.get(news_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if 'news' in data and data['news']:
                            news = data['news']
                        elif 'modules' in data:
                            # Sometimes news is in modules array
                            for module in data.get('modules', []):
                                if isinstance(module, dict) and 'news' in module:
                                    news = module['news']
                                    break
                except Exception:
                    pass
            
            # Method 4: Try news endpoint directly for the ticker
            if not news or len(news) == 0:
                try:
                    # Get quote data first to find the proper symbol
                    quote_url = f"https://query2.finance.yahoo.com/v1/finance/search?q={ticker}"
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'application/json'
                    }
                    quote_response = requests.get(quote_url, headers=headers, timeout=10)
                    if quote_response.status_code == 200:
                        quote_data = quote_response.json()
                        # Try to extract quote and get news for it
                        if 'quotes' in quote_data and quote_data['quotes']:
                            symbol = quote_data['quotes'][0].get('symbol', ticker)
                            # Now try to get news using the news endpoint
                            news_endpoint = f"https://query1.finance.yahoo.com/v1/finance/search?q={symbol}&newsCount={limit}"
                            news_response = requests.get(news_endpoint, headers=headers, timeout=10)
                            if news_response.status_code == 200:
                                news_data = news_response.json()
                                if 'news' in news_data:
                                    news = news_data['news']
                except Exception:
                    pass
            
            # Format news items if we have any
            if news and len(news) > 0:
                formatted_news = []
                for item in news[:limit]:
                    # Handle different news item formats from yfinance
                    # yfinance news structure: {'uuid', 'title', 'publisher', 'link', 'providerPublishTime', 'type', ...}
                    title = None
                    publisher = None
                    link = None
                    published_time = None
                    summary = None
                    
                    # Try different key variations
                    if isinstance(item, dict):
                        # Check if this is the new yfinance nested structure
                        # New structure has: item['content'] with nested data
                        content = item.get('content')
                        
                        if content and isinstance(content, dict):
                            # New yfinance structure (nested in 'content')
                            title = (content.get('title') or 
                                    content.get('headline') or 
                                    content.get('name'))
                            
                            summary = (content.get('summary') or 
                                     content.get('description') or 
                                     content.get('text') or 
                                     content.get('body'))
                            
                            # Publisher from provider
                            provider = item.get('provider', {})
                            if isinstance(provider, dict):
                                publisher = provider.get('displayName') or provider.get('name')
                            else:
                                publisher = None
                            
                            # Link from canonicalUrl or clickThroughUrl
                            canonical = item.get('canonicalUrl', {})
                            click_through = item.get('clickThroughUrl', {})
                            if isinstance(canonical, dict) and canonical.get('url'):
                                link = canonical.get('url')
                            elif isinstance(click_through, dict) and click_through.get('url'):
                                link = click_through.get('url')
                            else:
                                link = None
                            
                            # Timestamp from pubDate or displayTime
                            timestamp = content.get('pubDate') or content.get('displayTime')
                            
                        else:
                            # Old structure or direct API response (flat structure)
                            title = (item.get('title') or 
                                    item.get('headline') or 
                                    item.get('headlines') or 
                                    item.get('name') or
                                    item.get('longTitle') or
                                    item.get('shortTitle'))
                            
                            # Publisher variations
                            publisher = (item.get('publisher') or 
                                        item.get('source') or 
                                        item.get('publisherName') or
                                        item.get('provider') or
                                        item.get('author'))
                            
                            # Link variations - check multiple formats
                            link = (item.get('link') or 
                                   item.get('url') or 
                                   item.get('canonicalUrl') or
                                   item.get('clickThroughUrl') or
                                   item.get('redirectUrl'))
                            
                            # Summary/description variations
                            summary = (item.get('summary') or 
                                    item.get('description') or 
                                    item.get('text') or 
                                    item.get('body') or 
                                    item.get('content') or
                                    item.get('snippet') or
                                    item.get('excerpt'))
                            
                            # Timestamp handling - check multiple timestamp fields
                            timestamp = (item.get('providerPublishTime') or 
                                       item.get('pubDate') or 
                                       item.get('publishedAt') or 
                                       item.get('publishTime') or
                                       item.get('time') or
                                       item.get('date') or
                                       item.get('created'))
                        
                        # Fix link if it's relative
                        if link and link != '#':
                            if not link.startswith('http'):
                                if link.startswith('/'):
                                    link = f"https://finance.yahoo.com{link}"
                                else:
                                    link = f"https://finance.yahoo.com/{link}"
                        elif not link:
                            link = '#'
                        
                        # Process timestamp
                        if timestamp:
                            try:
                                # Handle Unix timestamp (seconds or milliseconds)
                                if isinstance(timestamp, (int, float)):
                                    # Check if it's in seconds or milliseconds
                                    if timestamp > 1e12:  # Likely milliseconds
                                        timestamp = timestamp / 1000
                                    elif timestamp < 1e9:  # Too small, might be wrong format
                                        timestamp = timestamp * 1000 if timestamp > 1e6 else timestamp
                                    # Always create naive datetime from timestamp
                                    published_time = datetime.fromtimestamp(timestamp)
                                    # Remove timezone info to make it naive
                                    if published_time.tzinfo:
                                        published_time = published_time.replace(tzinfo=None)
                                elif isinstance(timestamp, str):
                                    # Try parsing ISO format or other string formats
                                    try:
                                        # Handle ISO format with Z
                                        timestamp_clean = timestamp.replace('Z', '+00:00')
                                        published_time = datetime.fromisoformat(timestamp_clean)
                                        # Convert to naive datetime for consistent comparison
                                        if published_time.tzinfo:
                                            # Convert to UTC then remove timezone info
                                            published_time = published_time.astimezone().replace(tzinfo=None)
                                    except:
                                        # Try other common formats
                                        try:
                                            published_time = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S')
                                        except:
                                            pass
                            except Exception:
                                pass
                    
                    # Ensure we have valid values
                    if not title or title == 'No title':
                        continue  # Skip items without titles
                    
                    if not publisher:
                        publisher = 'Unknown'
                    
                    if not link or link == '#':
                        link = '#'
                    
                    # Truncate summary
                    if summary and isinstance(summary, str):
                        summary = summary[:300] + '...' if len(summary) > 300 else summary
                    else:
                        summary = 'No summary available'
                    
                    formatted_news.append({
                        'title': title,
                        'publisher': publisher,
                        'link': link,
                        'published': published_time,
                        'summary': summary
                    })
                
                return formatted_news
            
            return []
        except Exception as e:
            # Log error but don't expose to user - return empty list
            # Could add logging here: import logging; logging.error(f"Error fetching news for {ticker}: {str(e)}")
            return []
    
    def get_market_overview(self) -> Dict:
        """Get overall market overview"""
        try:
            # Major indices
            indices = {
                'SPY': 'S&P 500',
                'QQQ': 'NASDAQ 100',
                'DIA': 'Dow Jones',
                'IWM': 'Russell 2000'
            }
            
            market_data = {}
            for ticker, name in indices.items():
                try:
                    index_ticker = yf.Ticker(ticker)
                    hist = index_ticker.history(period='2d')
                    if len(hist) >= 2:
                        current = hist['Close'].iloc[-1]
                        previous = hist['Close'].iloc[-2]
                        change = current - previous
                        change_pct = (change / previous) * 100
                        
                        market_data[name] = {
                            'price': current,
                            'change': change,
                            'change_pct': change_pct,
                            'ticker': ticker
                        }
                except:
                    continue
            
            return market_data
        except Exception as e:
            return {}
    
    def get_sector_performance(self) -> pd.DataFrame:
        """Get sector performance data"""
        try:
            # Major sector ETFs
            sectors = {
                'XLK': 'Technology',
                'XLE': 'Energy',
                'XLF': 'Financials',
                'XLV': 'Healthcare',
                'XLI': 'Industrials',
                'XLP': 'Consumer Staples',
                'XLY': 'Consumer Discretionary',
                'XLU': 'Utilities',
                'XLB': 'Materials',
                'XLRE': 'Real Estate',
                'XLC': 'Communication'
            }
            
            sector_data = []
            for ticker, name in sectors.items():
                try:
                    sector_ticker = yf.Ticker(ticker)
                    hist = sector_ticker.history(period='5d')
                    if len(hist) >= 2:
                        current = hist['Close'].iloc[-1]
                        week_ago = hist['Close'].iloc[-5] if len(hist) >= 5 else hist['Close'].iloc[0]
                        change_pct = ((current - week_ago) / week_ago) * 100
                        
                        sector_data.append({
                            'Sector': name,
                            'Ticker': ticker,
                            'Price': current,
                            'Change %': change_pct
                        })
                except:
                    continue
            
            return pd.DataFrame(sector_data).sort_values('Change %', ascending=False)
        except:
            return pd.DataFrame()
    
    def get_market_movers(self, direction: str = 'gainers') -> pd.DataFrame:
        """Get market movers (gainers/losers)"""
        try:
            # Use SPY holdings or major stocks
            major_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'V', 'JNJ']
            
            movers = []
            for ticker in major_stocks:
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period='2d')
                    if len(hist) >= 2:
                        current = hist['Close'].iloc[-1]
                        previous = hist['Close'].iloc[-2]
                        change_pct = ((current - previous) / previous) * 100
                        
                        info = stock.info
                        movers.append({
                            'Ticker': ticker,
                            'Company': info.get('longName', ticker),
                            'Price': current,
                            'Change %': change_pct,
                            'Volume': hist['Volume'].iloc[-1]
                        })
                except:
                    continue
            
            df = pd.DataFrame(movers)
            if direction == 'gainers':
                return df.nlargest(10, 'Change %')
            else:
                return df.nsmallest(10, 'Change %')
        except:
            return pd.DataFrame()

