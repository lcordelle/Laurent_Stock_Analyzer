"""
Peer Benchmarking Utilities
Compare stocks against sector peers and competitors
"""

import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional
from utils.stock_analyzer import StockAnalyzer

class PeerBenchmark:
    """Benchmark stocks against peers"""
    
    def __init__(self):
        self.analyzer = StockAnalyzer()
    
    def get_sector_peers(self, ticker: str, sector: str = None) -> List[str]:
        """Get sector peers for comparison"""
        # Enhanced sector mappings with more stocks
        sector_peers = {
            'Technology': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'ORCL', 'CSCO', 'INTC', 'AMD', 'TSM', 'CRM', 'ADBE', 'NOW', 'PANW'],
            'Financial Services': ['JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'SCHW', 'BLK', 'AXP', 'V', 'MA', 'COF', 'TFC', 'PNC', 'USB'],
            'Healthcare': ['JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'ABT', 'DHR', 'BMY', 'AMGN', 'GILD', 'CVS', 'CI', 'HUM', 'ELV', 'LLY'],
            'Consumer Cyclical': ['AMZN', 'TSLA', 'HD', 'NKE', 'SBUX', 'MCD', 'LOW', 'TGT', 'WMT', 'F', 'GM', 'NFLX', 'DIS', 'BKNG', 'MAR'],
            'Consumer Defensive': ['WMT', 'PG', 'KO', 'PEP', 'COST', 'CL', 'MDLZ', 'GIS', 'KMB', 'TGT', 'KR', 'SYY', 'ADM', 'TSN', 'CPB'],
            'Energy': ['XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'VLO', 'PSX', 'HES', 'FANG', 'OVV', 'CTRA', 'MRO', 'DVN', 'APA'],
            'Industrials': ['BA', 'CAT', 'GE', 'HON', 'RTX', 'LMT', 'NOC', 'GD', 'TDG', 'EMR', 'ETN', 'ITW', 'PH', 'FTV', 'AME'],
            'Communication Services': ['GOOGL', 'META', 'NFLX', 'DIS', 'CMCSA', 'T', 'VZ', 'CHTR', 'EA', 'TTWO', 'ATVI', 'LYV', 'FOXA', 'NWSA', 'PARA'],
            'Real Estate': ['AMT', 'PLD', 'EQIX', 'PSA', 'WELL', 'SPG', 'O', 'DLR', 'EXPI', 'CBRE', 'AVB', 'EQR', 'UDR', 'MAA', 'ESS'],
            'Utilities': ['NEE', 'DUK', 'SO', 'AEP', 'SRE', 'XEL', 'WEC', 'ES', 'PEG', 'AEE', 'ED', 'ETR', 'FE', 'PNW', 'CMS'],
            'Basic Materials': ['LIN', 'APD', 'ECL', 'SHW', 'PPG', 'DD', 'DOW', 'FCX', 'NEM', 'VALE', 'NUE', 'STLD', 'X', 'CLF', 'ARCH']
        }
        
        try:
            if not sector:
                stock = yf.Ticker(ticker)
                info = stock.info
                sector = info.get('sector', '')
            
            sector_lower = sector.lower()
            for sector_name, peers in sector_peers.items():
                if sector_lower in sector_name.lower() or sector_name.lower() in sector_lower:
                    # Remove current ticker if present
                    peer_list = [p for p in peers if p.upper() != ticker.upper()]
                    return peer_list[:10]  # Return top 10 peers
            
            return []
        except:
            return []
    
    def benchmark_against_peers(self, ticker: str, metrics: Dict, score: Dict, 
                                peers: List[str] = None) -> Dict:
        """Benchmark stock against peers"""
        try:
            if not peers:
                peers = self.get_sector_peers(ticker)
            
            if not peers:
                return None
            
            # Get data for main stock
            main_stock = {
                'ticker': ticker,
                'score': score.get('total_score', 0),
                'pe_ratio': metrics.get('P/E Ratio', 0),
                'roe': metrics.get('ROE', 0),
                'revenue_growth': metrics.get('Revenue Growth', 0),
                'profit_margin': metrics.get('Profit Margin', 0),
                'current_price': metrics.get('Current Price', 0),
                'market_cap': metrics.get('Market Cap', 0)
            }
            
            # Get data for peers
            peer_data = []
            for peer_ticker in peers[:8]:  # Limit to 8 peers
                try:
                    peer_stock = yf.Ticker(peer_ticker)
                    peer_info = peer_stock.info
                    peer_hist = peer_stock.history(period='1y')
                    
                    if len(peer_hist) == 0:
                        continue
                    
                    # Get key metrics
                    peer_price = peer_hist['Close'].iloc[-1]
                    peer_pe = peer_info.get('trailingPE', 0)
                    peer_roe = peer_info.get('returnOnEquity', 0) * 100 if peer_info.get('returnOnEquity') else 0
                    peer_revenue_growth = peer_info.get('revenueGrowth', 0) * 100 if peer_info.get('revenueGrowth') else 0
                    peer_profit_margin = peer_info.get('profitMargins', 0) * 100 if peer_info.get('profitMargins') else 0
                    peer_market_cap = peer_info.get('marketCap', 0)
                    
                    # Calculate score for peer
                    try:
                        peer_score_result = self.analyzer.analyze_stock(peer_ticker)
                        if peer_score_result and 'score' in peer_score_result:
                            peer_score = peer_score_result['score']
                        else:
                            # Fallback: calculate basic score
                            peer_score = {'total_score': 50}  # Default neutral score
                    except:
                        peer_score = {'total_score': 50}  # Default if calculation fails
                    
                    peer_data.append({
                        'ticker': peer_ticker,
                        'score': peer_score.get('total_score', 0),
                        'pe_ratio': peer_pe,
                        'roe': peer_roe,
                        'revenue_growth': peer_revenue_growth,
                        'profit_margin': peer_profit_margin,
                        'current_price': peer_price,
                        'market_cap': peer_market_cap,
                        'company_name': peer_info.get('longName', peer_ticker)
                    })
                except:
                    continue
            
            if not peer_data:
                return None
            
            # Create comparison dataframe
            comparison_data = [main_stock] + peer_data
            comparison_df = pd.DataFrame(comparison_data)
            
            # Calculate rankings
            comparison_df['score_rank'] = comparison_df['score'].rank(ascending=False, method='min')
            comparison_df['pe_rank'] = comparison_df['pe_ratio'].rank(ascending=True, method='min')  # Lower P/E is better
            comparison_df['roe_rank'] = comparison_df['roe'].rank(ascending=False, method='min')
            comparison_df['growth_rank'] = comparison_df['revenue_growth'].rank(ascending=False, method='min')
            
            # Calculate percentiles
            for metric in ['score', 'pe_ratio', 'roe', 'revenue_growth', 'profit_margin']:
                if metric in comparison_df.columns:
                    comparison_df[f'{metric}_percentile'] = comparison_df[metric].rank(pct=True) * 100
            
            # Overall ranking
            comparison_df['overall_rank'] = (
                comparison_df['score_rank'] * 0.4 +
                comparison_df['roe_rank'] * 0.3 +
                comparison_df['growth_rank'] * 0.3
            ).rank(ascending=True, method='min')
            
            # Find main stock position
            main_stock_row = comparison_df[comparison_df['ticker'] == ticker.upper()]
            if len(main_stock_row) > 0:
                main_position = int(main_stock_row['overall_rank'].iloc[0])
                total_peers = len(comparison_df)
                percentile = ((total_peers - main_position + 1) / total_peers) * 100
                
                benchmark_summary = {
                    'position': main_position,
                    'total_peers': total_peers,
                    'percentile': percentile,
                    'better_than': f"{total_peers - main_position} of {total_peers} peers"
                }
            else:
                benchmark_summary = None
            
            return {
                'main_ticker': ticker,
                'peer_comparison': comparison_df,
                'benchmark_summary': benchmark_summary,
                'peers_analyzed': len(peer_data)
            }
        except Exception as e:
            return None

