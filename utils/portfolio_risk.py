"""
Portfolio Risk Management Dashboard
Provides portfolio-level risk metrics, VaR, correlation analysis, and stress testing
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class PortfolioRiskManager:
    """Professional portfolio risk analysis and management"""
    
    def __init__(self):
        self.risk_free_rate = 0.02  # 2% risk-free rate (can be updated)
    
    def calculate_portfolio_metrics(self, positions):
        """
        Calculate portfolio-level risk metrics
        
        Args:
            positions: List of dicts with keys: 'ticker', 'shares', 'entry_price', 'current_price'
        
        Returns:
            dict with portfolio metrics
        """
        if not positions or len(positions) == 0:
            return None
        
        total_value = 0
        total_cost = 0
        position_values = []
        
        for pos in positions:
            shares = pos.get('shares', 0)
            current_price = pos.get('current_price', 0)
            entry_price = pos.get('entry_price', current_price)
            
            current_value = shares * current_price
            cost_basis = shares * entry_price
            
            total_value += current_value
            total_cost += cost_basis
            
            position_values.append({
                'ticker': pos.get('ticker', ''),
                'value': current_value,
                'weight': 0,  # Will calculate after
                'cost': cost_basis,
                'pnl': current_value - cost_basis,
                'pnl_pct': ((current_value - cost_basis) / cost_basis * 100) if cost_basis > 0 else 0
            })
        
        # Calculate weights
        for pv in position_values:
            pv['weight'] = (pv['value'] / total_value * 100) if total_value > 0 else 0
        
        total_pnl = total_value - total_cost
        total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
        
        return {
            'total_value': total_value,
            'total_cost': total_cost,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct,
            'positions': position_values,
            'num_positions': len(positions)
        }
    
    def calculate_var(self, positions, confidence_level=0.95, time_horizon=1):
        """
        Calculate Value at Risk (VaR) for portfolio
        
        Args:
            positions: List of position dicts
            confidence_level: Confidence level (0.95 = 95%)
            time_horizon: Time horizon in days
        
        Returns:
            dict with VaR metrics
        """
        if not positions or len(positions) == 0:
            return None
        
        tickers = [pos.get('ticker') for pos in positions if pos.get('ticker')]
        if not tickers:
            return None
        
        try:
            # Fetch historical returns
            stock_data = yf.download(tickers, period="1y", progress=False)
            
            if stock_data.empty or len(stock_data) < 20:
                return None
            
            # Calculate portfolio returns
            portfolio_returns = []
            total_value = sum(pos.get('shares', 0) * pos.get('current_price', 0) for pos in positions)
            
            for i in range(1, len(stock_data)):
                daily_return = 0
                for pos in positions:
                    ticker = pos.get('ticker')
                    if ticker in stock_data['Close'].columns:
                        weight = (pos.get('shares', 0) * pos.get('current_price', 0)) / total_value if total_value > 0 else 0
                        if i < len(stock_data):
                            prev_close = stock_data['Close'].iloc[i-1][ticker]
                            curr_close = stock_data['Close'].iloc[i][ticker]
                            if prev_close > 0:
                                ticker_return = (curr_close - prev_close) / prev_close
                                daily_return += weight * ticker_return
                
                portfolio_returns.append(daily_return)
            
            if len(portfolio_returns) == 0:
                return None
            
            # Calculate VaR
            portfolio_returns = np.array(portfolio_returns)
            mean_return = np.mean(portfolio_returns)
            std_return = np.std(portfolio_returns)
            
            # Parametric VaR
            z_score = 1.645 if confidence_level == 0.95 else 2.326 if confidence_level == 0.99 else 1.282
            var_pct = z_score * std_return * np.sqrt(time_horizon)
            var_dollar = abs(var_pct * total_value)
            
            # Historical VaR
            sorted_returns = np.sort(portfolio_returns)
            var_index = int((1 - confidence_level) * len(sorted_returns))
            historical_var_pct = abs(sorted_returns[var_index] if var_index < len(sorted_returns) else sorted_returns[0])
            historical_var_dollar = abs(historical_var_pct * total_value)
            
            return {
                'confidence_level': confidence_level,
                'time_horizon_days': time_horizon,
                'var_percentage': var_pct * 100,
                'var_dollar': var_dollar,
                'historical_var_percentage': historical_var_pct * 100,
                'historical_var_dollar': historical_var_dollar,
                'portfolio_volatility': std_return * np.sqrt(252) * 100,  # Annualized
                'mean_daily_return': mean_return * 100
            }
        except Exception as e:
            return None
    
    def calculate_correlation_matrix(self, tickers, period="1y"):
        """
        Calculate correlation matrix for portfolio tickers
        
        Args:
            tickers: List of ticker symbols
            period: Time period for data
        
        Returns:
            DataFrame with correlation matrix
        """
        if not tickers or len(tickers) < 2:
            return None
        
        try:
            stock_data = yf.download(tickers, period=period, progress=False)
            
            if stock_data.empty or 'Close' not in stock_data.columns:
                return None
            
            # Get closing prices
            closes = stock_data['Close'] if isinstance(stock_data.columns, pd.MultiIndex) else stock_data
            
            # Calculate returns
            returns = closes.pct_change().dropna()
            
            # Calculate correlation
            correlation_matrix = returns.corr()
            
            return correlation_matrix
        except Exception as e:
            return None
    
    def calculate_portfolio_beta(self, positions, benchmark_ticker="SPY"):
        """
        Calculate portfolio beta relative to benchmark
        
        Args:
            positions: List of position dicts
            benchmark_ticker: Benchmark ticker (default: SPY)
        
        Returns:
            dict with beta metrics
        """
        if not positions or len(positions) == 0:
            return None
        
        tickers = [pos.get('ticker') for pos in positions if pos.get('ticker')]
        if not tickers:
            return None
        
        try:
            # Fetch data for portfolio and benchmark
            all_tickers = tickers + [benchmark_ticker]
            stock_data = yf.download(all_tickers, period="1y", progress=False)
            
            if stock_data.empty:
                return None
            
            # Calculate returns
            closes = stock_data['Close'] if isinstance(stock_data.columns, pd.MultiIndex) else stock_data
            returns = closes.pct_change().dropna()
            
            if benchmark_ticker not in returns.columns:
                return None
            
            benchmark_returns = returns[benchmark_ticker]
            
            # Calculate weighted portfolio returns
            total_value = sum(pos.get('shares', 0) * pos.get('current_price', 0) for pos in positions)
            portfolio_returns = pd.Series(0.0, index=returns.index)
            
            for pos in positions:
                ticker = pos.get('ticker')
                if ticker in returns.columns:
                    weight = (pos.get('shares', 0) * pos.get('current_price', 0)) / total_value if total_value > 0 else 0
                    portfolio_returns += weight * returns[ticker]
            
            # Calculate beta
            covariance = np.cov(portfolio_returns, benchmark_returns)[0][1]
            benchmark_variance = np.var(benchmark_returns)
            beta = covariance / benchmark_variance if benchmark_variance > 0 else 1.0
            
            # Calculate alpha (simplified)
            portfolio_mean = portfolio_returns.mean() * 252  # Annualized
            benchmark_mean = benchmark_returns.mean() * 252  # Annualized
            alpha = (portfolio_mean - self.risk_free_rate) - beta * (benchmark_mean - self.risk_free_rate)
            
            return {
                'beta': beta,
                'alpha': alpha * 100,  # As percentage
                'benchmark_ticker': benchmark_ticker,
                'portfolio_volatility': portfolio_returns.std() * np.sqrt(252) * 100,
                'benchmark_volatility': benchmark_returns.std() * np.sqrt(252) * 100
            }
        except Exception as e:
            return None
    
    def stress_test(self, positions, scenarios):
        """
        Perform stress testing on portfolio
        
        Args:
            positions: List of position dicts
            scenarios: Dict with scenario names and price changes (e.g., {'Crash': -0.20, 'Rally': 0.15})
        
        Returns:
            dict with stress test results
        """
        if not positions or not scenarios:
            return None
        
        results = {}
        total_value = sum(pos.get('shares', 0) * pos.get('current_price', 0) for pos in positions)
        
        for scenario_name, price_change in scenarios.items():
            stressed_value = 0
            for pos in positions:
                shares = pos.get('shares', 0)
                current_price = pos.get('current_price', 0)
                stressed_price = current_price * (1 + price_change)
                stressed_value += shares * stressed_price
            
            pnl_change = stressed_value - total_value
            pnl_change_pct = (pnl_change / total_value * 100) if total_value > 0 else 0
            
            results[scenario_name] = {
                'stressed_value': stressed_value,
                'pnl_change': pnl_change,
                'pnl_change_pct': pnl_change_pct,
                'price_change': price_change * 100
            }
        
        return results
    
    def calculate_sharpe_ratio(self, positions, period="1y"):
        """
        Calculate Sharpe ratio for portfolio
        
        Args:
            positions: List of position dicts
            period: Time period for calculation
        
        Returns:
            dict with Sharpe ratio and related metrics
        """
        if not positions or len(positions) == 0:
            return None
        
        tickers = [pos.get('ticker') for pos in positions if pos.get('ticker')]
        if not tickers:
            return None
        
        try:
            stock_data = yf.download(tickers, period=period, progress=False)
            
            if stock_data.empty:
                return None
            
            # Calculate portfolio returns
            closes = stock_data['Close'] if isinstance(stock_data.columns, pd.MultiIndex) else stock_data
            returns = closes.pct_change().dropna()
            
            total_value = sum(pos.get('shares', 0) * pos.get('current_price', 0) for pos in positions)
            portfolio_returns = pd.Series(0.0, index=returns.index)
            
            for pos in positions:
                ticker = pos.get('ticker')
                if ticker in returns.columns:
                    weight = (pos.get('shares', 0) * pos.get('current_price', 0)) / total_value if total_value > 0 else 0
                    portfolio_returns += weight * returns[ticker]
            
            # Annualized metrics
            mean_return = portfolio_returns.mean() * 252
            std_return = portfolio_returns.std() * np.sqrt(252)
            
            # Sharpe ratio
            sharpe_ratio = (mean_return - self.risk_free_rate) / std_return if std_return > 0 else 0
            
            # Sortino ratio (downside deviation)
            downside_returns = portfolio_returns[portfolio_returns < 0]
            downside_std = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else std_return
            sortino_ratio = (mean_return - self.risk_free_rate) / downside_std if downside_std > 0 else 0
            
            return {
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio,
                'annualized_return': mean_return * 100,
                'annualized_volatility': std_return * 100,
                'risk_free_rate': self.risk_free_rate * 100
            }
        except Exception as e:
            return None

