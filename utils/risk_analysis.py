"""
Risk Analysis Utilities
Calculate risk metrics and portfolio risk
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional
import warnings
warnings.filterwarnings('ignore')

class RiskAnalyzer:
    """Calculate various risk metrics"""
    
    def __init__(self):
        pass
    
    def calculate_var(self, returns: pd.Series, confidence: float = 0.05) -> float:
        """Calculate Value at Risk (VaR)"""
        if len(returns) == 0:
            return 0
        return np.percentile(returns.dropna(), confidence * 100)
    
    def calculate_cvar(self, returns: pd.Series, confidence: float = 0.05) -> float:
        """Calculate Conditional VaR (Expected Shortfall)"""
        if len(returns) == 0:
            return 0
        var = self.calculate_var(returns, confidence)
        return returns[returns <= var].mean()
    
    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe Ratio (annualized)"""
        if len(returns) == 0 or returns.std() == 0:
            return 0
        
        # Annualize returns and risk
        mean_return = returns.mean() * 252  # Trading days
        std_return = returns.std() * np.sqrt(252)
        
        if std_return == 0:
            return 0
        
        return (mean_return - risk_free_rate) / std_return
    
    def calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino Ratio (downside deviation only)"""
        if len(returns) == 0:
            return 0
        
        # Calculate downside returns only
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return float('inf') if returns.mean() > 0 else 0
        
        # Annualize
        mean_return = returns.mean() * 252
        downside_std = downside_returns.std() * np.sqrt(252)
        
        if downside_std == 0:
            return 0
        
        return (mean_return - risk_free_rate) / downside_std
    
    def calculate_max_drawdown(self, prices: pd.Series) -> Dict:
        """Calculate Maximum Drawdown"""
        if len(prices) == 0:
            return {'max_drawdown': 0, 'max_drawdown_pct': 0, 'recovery_days': 0}
        
        # Calculate running maximum
        running_max = prices.expanding().max()
        drawdown = prices - running_max
        drawdown_pct = (prices / running_max - 1) * 100
        
        max_dd = drawdown.min()
        max_dd_pct = drawdown_pct.min()
        
        # Find recovery period
        recovery_days = 0
        if max_dd < 0:
            max_dd_idx = drawdown.idxmin()
            recovery_period = prices.loc[max_dd_idx:]
            peak_after = recovery_period.max()
            if peak_after >= running_max.loc[max_dd_idx]:
                recovery_days = len(recovery_period[recovery_period < peak_after])
        
        return {
            'max_drawdown': abs(max_dd),
            'max_drawdown_pct': abs(max_dd_pct),
            'recovery_days': recovery_days
        }
    
    def calculate_beta(self, stock_returns: pd.Series, market_returns: pd.Series) -> float:
        """Calculate Beta vs market"""
        if len(stock_returns) == 0 or len(market_returns) == 0:
            return 0
        
        # Align indices
        aligned = pd.DataFrame({
            'stock': stock_returns,
            'market': market_returns
        }).dropna()
        
        if len(aligned) < 2:
            return 0
        
        covariance = aligned['stock'].cov(aligned['market'])
        market_variance = aligned['market'].var()
        
        if market_variance == 0:
            return 0
        
        return covariance / market_variance
    
    def calculate_volatility(self, returns: pd.Series, annualized: bool = True) -> float:
        """Calculate volatility (standard deviation of returns)"""
        if len(returns) == 0:
            return 0
        
        volatility = returns.std()
        if annualized:
            volatility *= np.sqrt(252)  # Annualize
        
        return volatility * 100  # Return as percentage
    
    def comprehensive_risk_analysis(self, prices: pd.Series, market_prices: Optional[pd.Series] = None) -> Dict:
        """Comprehensive risk analysis for a stock"""
        if len(prices) < 2:
            return {}
        
        # Calculate returns
        returns = prices.pct_change().dropna()
        
        risk_metrics = {
            'volatility': self.calculate_volatility(returns),
            'var_5pct': self.calculate_var(returns, 0.05),
            'var_1pct': self.calculate_var(returns, 0.01),
            'cvar_5pct': self.calculate_cvar(returns, 0.05),
            'sharpe_ratio': self.calculate_sharpe_ratio(returns),
            'sortino_ratio': self.calculate_sortino_ratio(returns),
        }
        
        # Max drawdown
        drawdown_info = self.calculate_max_drawdown(prices)
        risk_metrics.update(drawdown_info)
        
        # Beta if market data provided
        if market_prices is not None and len(market_prices) > 0:
            market_returns = market_prices.pct_change().dropna()
            risk_metrics['beta'] = self.calculate_beta(returns, market_returns)
        
        # Additional metrics
        risk_metrics['downside_capture'] = self._calculate_downside_capture(returns)
        risk_metrics['upside_capture'] = self._calculate_upside_capture(returns)
        
        return risk_metrics
    
    def _calculate_downside_capture(self, returns: pd.Series) -> float:
        """Calculate downside capture ratio"""
        negative_returns = returns[returns < 0]
        if len(negative_returns) == 0:
            return 0
        return negative_returns.mean() * 100
    
    def _calculate_upside_capture(self, returns: pd.Series) -> float:
        """Calculate upside capture ratio"""
        positive_returns = returns[returns > 0]
        if len(positive_returns) == 0:
            return 0
        return positive_returns.mean() * 100








