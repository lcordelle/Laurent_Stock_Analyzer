"""
Performance Tracking Utilities
Track analysis history, forecast accuracy, and performance metrics
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os

class PerformanceTracker:
    """Track performance and analysis history"""
    
    def __init__(self, storage_path: str = "data/performance"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
    
    def save_analysis(self, ticker: str, analysis_data: Dict) -> bool:
        """Save analysis snapshot"""
        try:
            timestamp = datetime.now().isoformat()
            # Clean timestamp for filename
            safe_timestamp = timestamp.replace(':', '-').replace('.', '-')
            filepath = os.path.join(self.storage_path, f"{ticker}_{safe_timestamp}.json")
            
            analysis_record = {
                'ticker': ticker,
                'timestamp': timestamp,
                'score': analysis_data.get('score', {}),
                'forecast': analysis_data.get('forecast', {}),
                'metrics': analysis_data.get('metrics', {}),
                'price': analysis_data.get('current_price', 0)
            }
            
            with open(filepath, 'w') as f:
                json.dump(analysis_record, f, indent=2)
            
            return True
        except Exception as e:
            return False
    
    def get_analysis_history(self, ticker: str, days: int = 30) -> pd.DataFrame:
        """Get analysis history for a ticker"""
        try:
            history = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            if os.path.exists(self.storage_path):
                for filename in os.listdir(self.storage_path):
                    if filename.startswith(ticker) and filename.endswith('.json'):
                        filepath = os.path.join(self.storage_path, filename)
                        try:
                            with open(filepath, 'r') as f:
                                data = json.load(f)
                                record_date = datetime.fromisoformat(data['timestamp'])
                                if record_date >= cutoff_date:
                                    history.append({
                                        'Date': record_date,
                                        'Score': data['score'].get('total_score', 0),
                                        'Price': data['price'],
                                        'Forecast Price': data['forecast'].get('forecast_price', 0),
                                        'Probability': data['forecast'].get('probability', 0)
                                    })
                        except Exception as e:
                            continue
            
            if history:
                df = pd.DataFrame(history)
                df = df.sort_values('Date')
                return df
            return pd.DataFrame()
        except:
            return pd.DataFrame()
    
    def calculate_forecast_accuracy(self, ticker: str, days: int = 30) -> Dict:
        """Calculate forecast accuracy"""
        try:
            history = self.get_analysis_history(ticker, days)
            
            if len(history) < 2:
                return {
                    'forecast_accuracy': 0,
                    'price_error': 0,
                    'direction_accuracy': 0,
                    'samples': 0
                }
            
            # Compare forecasts with actual prices
            errors = []
            direction_correct = 0
            total_direction = 0
            
            for i in range(len(history) - 1):
                forecast_price = history.iloc[i]['Forecast Price']
                actual_price = history.iloc[i+1]['Price']
                
                if forecast_price > 0 and actual_price > 0:
                    error_pct = abs((forecast_price - actual_price) / actual_price) * 100
                    errors.append(error_pct)
                    
                    # Direction accuracy
                    forecast_change = forecast_price - history.iloc[i]['Price']
                    actual_change = actual_price - history.iloc[i]['Price']
                    
                    if forecast_change * actual_change >= 0:  # Same direction
                        direction_correct += 1
                    total_direction += 1
            
            if len(errors) == 0:
                return {
                    'forecast_accuracy': 0,
                    'price_error': 0,
                    'direction_accuracy': 0,
                    'samples': 0
                }
            
            avg_error = sum(errors) / len(errors)
            accuracy = max(0, 100 - avg_error)
            direction_accuracy = (direction_correct / total_direction * 100) if total_direction > 0 else 0
            
            return {
                'forecast_accuracy': accuracy,
                'price_error': avg_error,
                'direction_accuracy': direction_accuracy,
                'samples': len(errors)
            }
        except:
            return {
                'forecast_accuracy': 0,
                'price_error': 0,
                'direction_accuracy': 0,
                'samples': 0
            }
    
    def get_score_trend(self, ticker: str, days: int = 30) -> Dict:
        """Get score trend over time"""
        try:
            history = self.get_analysis_history(ticker, days)
            
            if len(history) == 0:
                return {
                    'trend': 'stable',
                    'change': 0,
                    'current_score': 0,
                    'average_score': 0
                }
            
            current_score = history.iloc[-1]['Score']
            avg_score = history['Score'].mean()
            first_score = history.iloc[0]['Score']
            change = current_score - first_score
            
            if change > 5:
                trend = 'improving'
            elif change < -5:
                trend = 'declining'
            else:
                trend = 'stable'
            
            return {
                'trend': trend,
                'change': change,
                'current_score': current_score,
                'average_score': avg_score,
                'data_points': len(history)
            }
        except:
            return {
                'trend': 'unknown',
                'change': 0,
                'current_score': 0,
                'average_score': 0
            }

