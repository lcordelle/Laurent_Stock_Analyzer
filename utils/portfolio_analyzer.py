"""
Portfolio Analyzer
Analyzes user's stock portfolio with comprehensive metrics
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class PortfolioAnalyzer:
    """Analyze user's stock portfolio"""
    
    def __init__(self):
        self.cache = {}
    
    def parse_ibkr_csv(self, csv_content):
        """
        Parse IBKR (Interactive Brokers) CSV export
        IBKR CSV typically has columns like: Symbol, Quantity, Market Value, etc.
        Enhanced to handle various IBKR export formats
        """
        holdings = {}
        try:
            import io
            
            # Try different delimiters
            delimiters = [',', '\t', ';', '|']
            df = None
            
            for delimiter in delimiters:
                try:
                    df = pd.read_csv(io.StringIO(csv_content), delimiter=delimiter)
                    if len(df.columns) > 1:  # If we got multiple columns, this delimiter works
                        break
                except:
                    continue
            
            if df is None or len(df.columns) < 2:
                return holdings
            
            # Common IBKR column names (expanded list)
            symbol_col = None
            quantity_col = None
            
            # Try to find symbol/ticker column - more variations
            symbol_keywords = ['symbol', 'ticker', 'instrument', 'underlying', 'asset', 'security', 
                             'stock', 'equity', 'name', 'description', 'isin', 'cusip']
            
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if any(keyword in col_lower for keyword in symbol_keywords):
                    symbol_col = col
                    break
            
            # Try to find quantity/shares column - more variations
            quantity_keywords = ['quantity', 'qty', 'shares', 'position', 'units', 'contracts',
                               'size', 'amount', 'holdings', 'number', 'count']
            
            for col in df.columns:
                col_lower = str(col).lower().strip()
                if any(keyword in col_lower for keyword in quantity_keywords):
                    # Make sure it's numeric
                    try:
                        sample_val = df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else None
                        if sample_val is not None:
                            float(sample_val)
                            quantity_col = col
                            break
                    except:
                        continue
            
            # If still not found, try heuristic approach
            if not symbol_col:
                # Look for column with short text values (likely tickers)
                for col in df.columns:
                    if df[col].dtype == 'object':
                        sample_values = df[col].dropna().head(10)
                        if len(sample_values) > 0:
                            avg_len = sample_values.astype(str).str.len().mean()
                            # Tickers are usually 1-10 characters
                            if 1 <= avg_len <= 10:
                                # Check if values look like tickers (alphanumeric, mostly uppercase)
                                sample_str = str(sample_values.iloc[0]).upper()
                                if sample_str.isalnum() or '.' in sample_str:
                                    symbol_col = col
                                    break
            
            if not quantity_col:
                # Look for numeric columns that could be quantities
                for col in df.columns:
                    if df[col].dtype in ['int64', 'float64', 'int32', 'float32']:
                        # Check if values are positive (quantities should be)
                        sample_values = df[col].dropna().head(10)
                        if len(sample_values) > 0 and (sample_values > 0).any():
                            quantity_col = col
                            break
            
            # If we found both columns, parse the data
            if symbol_col and quantity_col:
                for idx, row in df.iterrows():
                    try:
                        ticker_raw = str(row[symbol_col]).strip()
                        if not ticker_raw or ticker_raw.upper() in ['NAN', 'NONE', 'NULL', '', 'N/A', 'NA']:
                            continue
                        
                        ticker = ticker_raw.upper()
                        
                        # Remove exchange suffixes (e.g., AAPL.SWISS -> AAPL, AAPL.US -> AAPL)
                        if '.' in ticker:
                            ticker = ticker.split('.')[0]
                        
                        # Remove common suffixes
                        ticker = ticker.replace(' STOCK', '').replace(' EQUITY', '').replace(' COMMON', '').strip()
                        
                        # Skip if ticker is too long (probably not a ticker) or empty
                        if len(ticker) > 10 or len(ticker) == 0:
                            continue
                        
                        # Get quantity
                        qty_raw = row[quantity_col]
                        if pd.isna(qty_raw):
                            continue
                        
                        try:
                            shares = float(qty_raw)
                            # Skip if shares is 0 or negative
                            if shares <= 0:
                                continue
                            
                            # If ticker is valid, add to holdings
                            # Allow alphanumeric and some special chars (like hyphens)
                            if ticker and (ticker.replace('-', '').isalnum() or len(ticker) <= 5):
                                # If ticker already exists, add shares
                                if ticker in holdings:
                                    holdings[ticker] += shares
                                else:
                                    holdings[ticker] = shares
                        except (ValueError, TypeError):
                            continue
                    except Exception as e:
                        continue
            
            # If we didn't find standard columns OR found very few holdings, try more aggressive parsing
            if len(holdings) < 5 and len(df) > 0:
                # Try ALL possible column combinations
                object_cols = [col for col in df.columns if df[col].dtype == 'object']
                numeric_cols = [col for col in df.columns if df[col].dtype in ['int64', 'float64', 'int32', 'float32']]
                
                # Try each object column as potential ticker column
                for potential_symbol_col in object_cols:
                    if potential_symbol_col == symbol_col:  # Already tried
                        continue
                    
                    # Try each numeric column as potential quantity column
                    for potential_quantity_col in numeric_cols:
                        if potential_quantity_col == quantity_col:  # Already tried
                            continue
                        
                        # Try parsing with this combination
                        temp_holdings = {}
                        for idx, row in df.iterrows():
                            try:
                                ticker_raw = str(row[potential_symbol_col]).strip()
                                if not ticker_raw or ticker_raw.upper() in ['NAN', 'NONE', 'NULL', '', 'N/A', 'NA']:
                                    continue
                                
                                ticker = ticker_raw.upper()
                                
                                # Remove exchange suffixes
                                if '.' in ticker:
                                    ticker = ticker.split('.')[0]
                                
                                # Remove common suffixes
                                ticker = ticker.replace(' STOCK', '').replace(' EQUITY', '').replace(' COMMON', '').strip()
                                
                                # Skip if ticker is too long or empty
                                if len(ticker) > 10 or len(ticker) == 0:
                                    continue
                                
                                # Get quantity
                                qty_raw = row[potential_quantity_col]
                                if pd.isna(qty_raw):
                                    continue
                                
                                try:
                                    shares = float(qty_raw)
                                    if shares <= 0:
                                        continue
                                    
                                    if ticker and (ticker.replace('-', '').isalnum() or len(ticker) <= 5):
                                        if ticker in temp_holdings:
                                            temp_holdings[ticker] += shares
                                        else:
                                            temp_holdings[ticker] = shares
                                except (ValueError, TypeError):
                                    continue
                            except:
                                continue
                        
                        # If this combination found more holdings, use it
                        if len(temp_holdings) > len(holdings):
                            holdings = temp_holdings
                            symbol_col = potential_symbol_col
                            quantity_col = potential_quantity_col
                            break
                    
                    if len(holdings) >= 5:
                        break
            
            # If we didn't find standard columns, try to parse row by row
            if not holdings and len(df) > 0:
                # Try to find any column that might contain ticker:quantity pairs
                for col in df.columns:
                    sample = str(df[col].iloc[0]) if len(df[col]) > 0 else ""
                    if ':' in sample or ' ' in sample:
                        # Might be ticker:quantity format
                        for _, row in df.iterrows():
                            try:
                                cell_value = str(row[col]).strip()
                                if ':' in cell_value:
                                    parts = cell_value.split(':')
                                    if len(parts) >= 2:
                                        ticker = parts[0].strip().upper()
                                        shares = float(parts[1].strip())
                                        if ticker and shares > 0:
                                            if '.' in ticker:
                                                ticker = ticker.split('.')[0]
                                            if ticker not in holdings:
                                                holdings[ticker] = shares
                                            else:
                                                holdings[ticker] += shares
                            except:
                                continue
            
        except Exception as e:
            print(f"Error parsing IBKR CSV: {e}")
            import traceback
            traceback.print_exc()
        
        return holdings
    
    def parse_portfolio_input(self, portfolio_text):
        """
        Parse portfolio input text
        Format: "TICKER:SHARES" or "TICKER SHARES" or "TICKER,SHARES"
        Example: "AAPL:10, MSFT:5, GOOGL:3" or "AAPL 10, MSFT 5"
        Also supports tab-separated values (common in IBKR exports)
        """
        holdings = {}
        try:
            # Check if it looks like CSV (has headers or multiple columns)
            lines = portfolio_text.strip().split('\n')
            
            # If it looks like CSV/TSV with headers, try CSV parsing first
            if len(lines) > 1:
                first_line = lines[0]
                has_delimiter = ',' in first_line or '\t' in first_line or ';' in first_line
                
                if has_delimiter:
                    # Check if first line looks like headers
                    first_line_lower = first_line.lower()
                    header_keywords = ['symbol', 'ticker', 'quantity', 'qty', 'shares', 'position', 
                                     'instrument', 'underlying', 'asset', 'security', 'units', 'contracts']
                    
                    # Try CSV parsing if it looks like structured data
                    if any(keyword in first_line_lower for keyword in header_keywords) or len(first_line.split(',')) > 2 or len(first_line.split('\t')) > 2:
                        # Try as CSV
                        csv_content = '\n'.join(lines)
                        holdings = self.parse_ibkr_csv(csv_content)
                        if holdings:
                            return holdings
                    
                    # Even without clear headers, if it has multiple columns, try parsing
                    if len(first_line.split(',')) >= 2 or len(first_line.split('\t')) >= 2:
                        csv_content = '\n'.join(lines)
                        holdings = self.parse_ibkr_csv(csv_content)
                        if holdings:
                            return holdings
            
            # Otherwise, parse as simple text format
            # Handle both comma and newline separated entries
            if '\n' in portfolio_text:
                entries = [e.strip() for e in portfolio_text.split('\n') if e.strip()]
            else:
                entries = [e.strip() for e in portfolio_text.split(',') if e.strip()]
            
            for entry in entries:
                if not entry:
                    continue
                
                # Skip header lines
                if any(keyword in entry.lower() for keyword in ['symbol', 'ticker', 'quantity', 'qty', 'shares']):
                    continue
                
                # Try different separators
                if ':' in entry:
                    parts = entry.split(':')
                elif '\t' in entry:
                    parts = entry.split('\t')
                elif ' ' in entry:
                    parts = entry.split()
                elif ',' in entry and entry.count(',') == 1:
                    parts = entry.split(',')
                else:
                    # Assume format is "TICKER SHARES" or "TICKER:SHARES"
                    parts = entry.replace(':', ' ').replace('\t', ' ').split()
                
                if len(parts) >= 2:
                    ticker = parts[0].strip().upper()
                    # Remove exchange suffixes
                    if '.' in ticker:
                        ticker = ticker.split('.')[0]
                    
                    try:
                        shares = float(parts[1].strip().replace(',', ''))
                        if shares > 0:
                            holdings[ticker] = shares
                    except ValueError:
                        continue
                elif len(parts) == 1:
                    # Single ticker, assume 1 share
                    ticker = parts[0].strip().upper()
                    if '.' in ticker:
                        ticker = ticker.split('.')[0]
                    if ticker and ticker != 'NAN':
                        holdings[ticker] = 1.0
        
        except Exception as e:
            print(f"Error parsing portfolio: {e}")
        
        return holdings
    
    def get_portfolio_data(self, holdings):
        """Get current data for all portfolio holdings"""
        portfolio_data = {}
        
        for ticker, shares in holdings.items():
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                
                if current_price and current_price > 0:
                    portfolio_data[ticker] = {
                        'shares': shares,
                        'current_price': current_price,
                        'market_value': shares * current_price,
                        'info': info,
                        'ticker': ticker
                    }
            except Exception as e:
                print(f"Error fetching data for {ticker}: {e}")
                continue
        
        return portfolio_data
    
    def calculate_portfolio_metrics(self, portfolio_data):
        """Calculate comprehensive portfolio metrics"""
        if not portfolio_data:
            return None
        
        total_value = sum(data['market_value'] for data in portfolio_data.values())
        
        if total_value == 0:
            return None
        
        # Calculate weighted averages
        weighted_pe = 0
        weighted_forward_pe = 0
        weighted_peg = 0
        weighted_roe = 0
        weighted_roa = 0
        weighted_gross_margin = 0
        weighted_operating_margin = 0
        weighted_profit_margin = 0
        weighted_revenue_growth = 0
        weighted_beta = 0
        weighted_dividend_yield = 0
        
        total_weight = 0
        valid_stocks = 0
        
        for ticker, data in portfolio_data.items():
            info = data['info']
            weight = data['market_value'] / total_value
            
            # P/E Ratio
            pe = info.get('trailingPE', info.get('forwardPE', 0))
            if pe and pe > 0:
                weighted_pe += pe * weight
                total_weight += weight
            
            # Forward P/E
            forward_pe = info.get('forwardPE', 0)
            if forward_pe and forward_pe > 0:
                weighted_forward_pe += forward_pe * weight
            
            # PEG Ratio
            peg = info.get('pegRatio', 0)
            if peg and peg > 0:
                weighted_peg += peg * weight
            
            # ROE
            roe = info.get('returnOnEquity', 0)
            if roe:
                weighted_roe += roe * weight
            
            # ROA
            roa = info.get('returnOnAssets', 0)
            if roa:
                weighted_roa += roa * weight
            
            # Gross Margin
            gross_margin = info.get('grossMargins', 0)
            if gross_margin:
                weighted_gross_margin += gross_margin * 100 * weight
            
            # Operating Margin
            operating_margin = info.get('operatingMargins', 0)
            if operating_margin:
                weighted_operating_margin += operating_margin * 100 * weight
            
            # Profit Margin
            profit_margin = info.get('profitMargins', 0)
            if profit_margin:
                weighted_profit_margin += profit_margin * 100 * weight
            
            # Revenue Growth
            revenue_growth = info.get('revenueGrowth', 0)
            if revenue_growth:
                weighted_revenue_growth += revenue_growth * 100 * weight
            
            # Beta
            beta = info.get('beta', 1.0)
            if beta:
                weighted_beta += beta * weight
            
            # Dividend Yield
            dividend_yield = info.get('dividendYield', 0)
            if dividend_yield:
                weighted_dividend_yield += dividend_yield * 100 * weight
            
            valid_stocks += 1
        
        # Calculate sector allocation
        sector_allocation = {}
        for ticker, data in portfolio_data.items():
            sector = data['info'].get('sector', 'Unknown')
            if sector:
                sector_allocation[sector] = sector_allocation.get(sector, 0) + data['market_value']
        
        # Calculate industry allocation
        industry_allocation = {}
        for ticker, data in portfolio_data.items():
            industry = data['info'].get('industry', 'Unknown')
            if industry:
                industry_allocation[industry] = industry_allocation.get(industry, 0) + data['market_value']
        
        # Calculate portfolio concentration (Herfindahl-Hirschman Index)
        weights = [data['market_value'] / total_value for data in portfolio_data.values()]
        hhi = sum(w ** 2 for w in weights) * 10000  # Scale to 0-10000
        
        # Number of holdings
        num_holdings = len(portfolio_data)
        
        return {
            'total_value': total_value,
            'num_holdings': num_holdings,
            'weighted_pe': weighted_pe if total_weight > 0 else 0,
            'weighted_forward_pe': weighted_forward_pe,
            'weighted_peg': weighted_peg,
            'weighted_roe': weighted_roe,
            'weighted_roa': weighted_roa,
            'weighted_gross_margin': weighted_gross_margin,
            'weighted_operating_margin': weighted_operating_margin,
            'weighted_profit_margin': weighted_profit_margin,
            'weighted_revenue_growth': weighted_revenue_growth,
            'weighted_beta': weighted_beta,
            'weighted_dividend_yield': weighted_dividend_yield,
            'sector_allocation': sector_allocation,
            'industry_allocation': industry_allocation,
            'concentration_hhi': hhi,
            'portfolio_data': portfolio_data
        }
    
    def calculate_portfolio_performance(self, portfolio_data, period='1y'):
        """Calculate portfolio performance metrics"""
        if not portfolio_data:
            return None
        
        tickers = list(portfolio_data.keys())
        shares_dict = {ticker: data['shares'] for ticker, data in portfolio_data.items()}
        
        try:
            # Get historical prices for all tickers
            portfolio_hist = {}
            for ticker in tickers:
                stock = yf.Ticker(ticker)
                hist = stock.history(period=period)
                if not hist.empty:
                    portfolio_hist[ticker] = hist['Close']
            
            if not portfolio_hist:
                return None
            
            # Align all price series to common dates
            all_dates = set()
            for prices in portfolio_hist.values():
                all_dates.update(prices.index)
            
            all_dates = sorted(all_dates)
            
            # Calculate portfolio value over time
            portfolio_values = []
            for date in all_dates:
                total_value = 0
                for ticker, prices in portfolio_hist.items():
                    if date in prices.index:
                        price = prices.loc[date]
                        shares = shares_dict[ticker]
                        total_value += price * shares
                portfolio_values.append(total_value)
            
            if not portfolio_values:
                return None
            
            portfolio_series = pd.Series(portfolio_values, index=all_dates)
            
            # Calculate returns
            returns = portfolio_series.pct_change().dropna()
            
            # Current value
            current_value = portfolio_values[-1]
            initial_value = portfolio_values[0]
            
            # Total return
            total_return = ((current_value - initial_value) / initial_value) * 100 if initial_value > 0 else 0
            
            # Annualized return
            days = (all_dates[-1] - all_dates[0]).days
            if days > 0:
                annualized_return = ((current_value / initial_value) ** (365 / days) - 1) * 100
            else:
                annualized_return = 0
            
            # Volatility (annualized)
            if len(returns) > 0:
                volatility = returns.std() * np.sqrt(252) * 100  # Annualized
            else:
                volatility = 0
            
            # Sharpe Ratio (assuming risk-free rate of 2%)
            risk_free_rate = 2.0
            if volatility > 0:
                sharpe_ratio = (annualized_return - risk_free_rate) / volatility
            else:
                sharpe_ratio = 0
            
            # Max drawdown
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min() * 100
            
            return {
                'current_value': current_value,
                'initial_value': initial_value,
                'total_return': total_return,
                'annualized_return': annualized_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'portfolio_series': portfolio_series,
                'returns': returns
            }
        
        except Exception as e:
            print(f"Error calculating performance: {e}")
            return None
    
    def get_portfolio_risk_metrics(self, portfolio_data):
        """Calculate portfolio-level risk metrics"""
        if not portfolio_data:
            return None
        
        # Get betas and calculate weighted beta
        betas = []
        weights = []
        total_value = sum(data['market_value'] for data in portfolio_data.values())
        
        for ticker, data in portfolio_data.items():
            beta = data['info'].get('beta', 1.0)
            if beta:
                weight = data['market_value'] / total_value
                betas.append(beta)
                weights.append(weight)
        
        portfolio_beta = sum(b * w for b, w in zip(betas, weights)) if weights else 1.0
        
        # Calculate correlation (simplified - would need historical data for full correlation matrix)
        # For now, return basic metrics
        
        return {
            'portfolio_beta': portfolio_beta,
            'num_positions': len(portfolio_data),
            'largest_position_pct': max(data['market_value'] for data in portfolio_data.values()) / total_value * 100 if total_value > 0 else 0
        }

