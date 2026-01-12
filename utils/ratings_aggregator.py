"""
Ratings Aggregator
Collect ratings from multiple verified sources and create summary
"""

import yfinance as yf
import pandas as pd
from typing import Dict, List, Optional

class RatingsAggregator:
    """Aggregate ratings from multiple sources"""
    
    def __init__(self):
        self.sources = ['Yahoo Finance', 'Internal Analysis', 'Market Consensus']
    
    def get_yahoo_ratings(self, ticker: str) -> Dict:
        """Get ratings from Yahoo Finance"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            recommendation = info.get('recommendationKey', 'N/A')
            recommendation_mean = info.get('recommendationMean', 0)
            number_of_analysts = info.get('numberOfAnalystOpinions', 0)
            
            # Convert recommendation to rating
            rating_map = {
                'strong_buy': 5,
                'buy': 4,
                'hold': 3,
                'underperform': 2,
                'sell': 1
            }
            
            rating_score = rating_map.get(recommendation, 3)
            
            return {
                'source': 'Yahoo Finance',
                'rating': recommendation.upper().replace('_', ' ') if recommendation != 'N/A' else 'N/A',
                'rating_score': rating_score,
                'analysts': number_of_analysts,
                'mean_rating': recommendation_mean,
                'target_price': info.get('targetMeanPrice', 0),
                'target_high': info.get('targetHighPrice', 0),
                'target_low': info.get('targetLowPrice', 0)
            }
        except:
            return None
    
    def get_internal_rating(self, score: Dict) -> Dict:
        """Generate internal rating based on our scoring system"""
        try:
            total_score = score.get('total_score', 0)
            
            if total_score >= 80:
                rating = 'STRONG BUY'
                rating_score = 5
            elif total_score >= 70:
                rating = 'BUY'
                rating_score = 4
            elif total_score >= 60:
                rating = 'HOLD'
                rating_score = 3
            elif total_score >= 50:
                rating = 'UNDERPERFORM'
                rating_score = 2
            else:
                rating = 'SELL'
                rating_score = 1
            
            return {
                'source': 'Internal Analysis',
                'rating': rating,
                'rating_score': rating_score,
                'score': total_score,
                'analysts': 1,
                'confidence': 'High'
            }
        except:
            return None
    
    def get_market_consensus(self, ticker: str, info: Dict) -> Dict:
        """Generate market consensus rating"""
        try:
            # Aggregate from available data
            recommendation = info.get('recommendationKey', 'hold')
            recommendation_mean = info.get('recommendationMean', 3.0)
            
            if recommendation_mean >= 4.5:
                rating = 'STRONG BUY'
                rating_score = 5
            elif recommendation_mean >= 3.5:
                rating = 'BUY'
                rating_score = 4
            elif recommendation_mean >= 2.5:
                rating = 'HOLD'
                rating_score = 3
            elif recommendation_mean >= 1.5:
                rating = 'UNDERPERFORM'
                rating_score = 2
            else:
                rating = 'SELL'
                rating_score = 1
            
            return {
                'source': 'Market Consensus',
                'rating': rating,
                'rating_score': rating_score,
                'mean_rating': recommendation_mean,
                'analysts': info.get('numberOfAnalystOpinions', 0),
                'target_price': info.get('targetMeanPrice', 0)
            }
        except:
            return None
    
    def aggregate_ratings(self, ticker: str, score: Dict, info: Dict) -> Dict:
        """Aggregate all ratings into summary table"""
        ratings = []
        
        # Yahoo Finance
        yahoo_rating = self.get_yahoo_ratings(ticker)
        if yahoo_rating:
            ratings.append(yahoo_rating)
        
        # Internal Analysis
        internal_rating = self.get_internal_rating(score)
        if internal_rating:
            ratings.append(internal_rating)
        
        # Market Consensus
        market_rating = self.get_market_consensus(ticker, info)
        if market_rating:
            ratings.append(market_rating)
        
        if not ratings:
            return None
        
        # Calculate composite rating
        rating_scores = [r['rating_score'] for r in ratings if r.get('rating_score')]
        if rating_scores:
            avg_rating_score = sum(rating_scores) / len(rating_scores)
            
            if avg_rating_score >= 4.5:
                composite_rating = 'STRONG BUY'
            elif avg_rating_score >= 3.5:
                composite_rating = 'BUY'
            elif avg_rating_score >= 2.5:
                composite_rating = 'HOLD'
            elif avg_rating_score >= 1.5:
                composite_rating = 'UNDERPERFORM'
            else:
                composite_rating = 'SELL'
        else:
            composite_rating = 'N/A'
            avg_rating_score = 0
        
        # Create summary dataframe
        ratings_df = pd.DataFrame(ratings)
        
        return {
            'ratings': ratings,
            'ratings_df': ratings_df,
            'composite_rating': composite_rating,
            'average_rating_score': avg_rating_score,
            'number_of_sources': len(ratings),
            'consensus': {
                'rating': composite_rating,
                'score': avg_rating_score,
                'sources': len(ratings)
            }
        }








