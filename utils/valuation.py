"""
Stock Valuation Utilities
Calculate intrinsic value, fair value, and valuation metrics
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime

class StockValuation:
    """Calculate stock valuation and intrinsic value"""
    
    def __init__(self):
        self.risk_free_rate = 0.04  # Assume 4% risk-free rate (10-year Treasury)
    
    def calculate_intrinsic_value_dcf(self, ticker: str, info: Dict) -> Dict:
        """Calculate intrinsic value using Discounted Cash Flow (DCF) model"""
        try:
            # Get financial data
            free_cash_flow = info.get('freeCashflow', 0)
            revenue = info.get('totalRevenue', 0)
            earnings = info.get('netIncome', 0)
            total_debt = info.get('totalDebt', 0)
            cash = info.get('totalCash', 0)
            shares_outstanding = info.get('sharesOutstanding', 0)
            
            if not shares_outstanding or shares_outstanding == 0:
                return None
            
            # Growth assumptions
            revenue_growth = info.get('revenueGrowth', 0) or 0
            if isinstance(revenue_growth, float) and abs(revenue_growth) > 1:
                revenue_growth = revenue_growth / 100  # Convert percentage to decimal
            
            # Terminal growth rate (conservative)
            terminal_growth = 0.03  # 3%
            
            # Calculate WACC (Weighted Average Cost of Capital)
            beta = info.get('beta', 1.0) or 1.0
            market_return = 0.10  # Expected market return 10%
            cost_of_equity = self.risk_free_rate + beta * (market_return - self.risk_free_rate)
            cost_of_debt = 0.05  # Assume 5% cost of debt
            debt_equity_ratio = info.get('debtToEquity', 0) or 0
            
            if debt_equity_ratio > 0:
                equity_weight = 1 / (1 + debt_equity_ratio)
                debt_weight = debt_equity_ratio / (1 + debt_equity_ratio)
                wacc = (cost_of_equity * equity_weight) + (cost_of_debt * debt_weight * (1 - 0.21))  # 21% tax
            else:
                wacc = cost_of_equity
            
            # DCF Calculation (simplified 5-year projection)
            if free_cash_flow and free_cash_flow > 0:
                fcf_growth = min(revenue_growth, 0.15)  # Cap growth at 15%
                
                # Project FCF for 5 years
                projected_fcf = []
                current_fcf = free_cash_flow
                for year in range(1, 6):
                    current_fcf = current_fcf * (1 + fcf_growth)
                    discount_factor = (1 + wacc) ** year
                    pv = current_fcf / discount_factor
                    projected_fcf.append(pv)
                
                # Terminal value
                terminal_fcf = current_fcf * (1 + terminal_growth)
                terminal_value = terminal_fcf / (wacc - terminal_growth)
                terminal_pv = terminal_value / ((1 + wacc) ** 5)
                
                # Enterprise value
                enterprise_value = sum(projected_fcf) + terminal_pv
                
                # Equity value
                equity_value = enterprise_value - total_debt + cash
                
                # Intrinsic value per share
                intrinsic_value = equity_value / shares_outstanding if shares_outstanding > 0 else 0
                
                return {
                    'intrinsic_value': intrinsic_value,
                    'enterprise_value': enterprise_value,
                    'equity_value': equity_value,
                    'wacc': wacc * 100,
                    'method': 'DCF'
                }
            
            return None
        except Exception as e:
            return None
    
    def calculate_intrinsic_value_pe(self, ticker: str, info: Dict, metrics: Dict) -> Dict:
        """Calculate intrinsic value using P/E multiple method"""
        try:
            current_price = metrics.get('Current Price', 0)
            pe_ratio = metrics.get('P/E Ratio', 0)
            forward_pe = metrics.get('Forward P/E', 0)
            
            if not current_price or not pe_ratio:
                return None
            
            # Get industry/sector average P/E
            sector_pe = info.get('sectorPE', pe_ratio)
            industry_pe = info.get('industryPE', sector_pe)
            
            # Use forward P/E if available, otherwise use trailing
            target_pe = forward_pe if forward_pe and forward_pe > 0 else pe_ratio
            
            # Get earnings
            trailing_eps = info.get('trailingEps', 0)
            forward_eps = info.get('forwardEps', trailing_eps)
            
            # Calculate intrinsic value using industry average P/E
            if industry_pe and industry_pe > 0:
                intrinsic_value = forward_eps * industry_pe
            elif sector_pe and sector_pe > 0:
                intrinsic_value = forward_eps * sector_pe
            else:
                # Use fair P/E ratio (15-20 for average company)
                fair_pe = 18
                intrinsic_value = forward_eps * fair_pe if forward_eps > 0 else trailing_eps * fair_pe
            
            return {
                'intrinsic_value': intrinsic_value,
                'method': 'P/E Multiple',
                'target_pe': target_pe,
                'fair_pe': industry_pe or sector_pe or 18
            }
        except:
            return None
    
    def calculate_intrinsic_value_pbv(self, ticker: str, info: Dict, metrics: Dict) -> Dict:
        """Calculate intrinsic value using Price-to-Book method"""
        try:
            current_price = metrics.get('Current Price', 0)
            price_to_book = metrics.get('Price to Book', 0)
            book_value = info.get('bookValue', 0)
            
            if not book_value or book_value <= 0:
                return None
            
            # Industry average P/B
            industry_pb = info.get('industryPB', 2.0)
            
            # Calculate intrinsic value
            intrinsic_value = book_value * industry_pb if industry_pb > 0 else book_value * 2.0
            
            return {
                'intrinsic_value': intrinsic_value,
                'method': 'P/B Multiple',
                'book_value': book_value,
                'target_pb': industry_pb or 2.0
            }
        except:
            return None
    
    def comprehensive_valuation(self, ticker: str, info: Dict, metrics: Dict) -> Dict:
        """Calculate comprehensive valuation using multiple methods"""
        valuations = {}
        
        # DCF Method
        dcf_valuation = self.calculate_intrinsic_value_dcf(ticker, info)
        if dcf_valuation:
            valuations['DCF'] = dcf_valuation
        
        # P/E Method
        pe_valuation = self.calculate_intrinsic_value_pe(ticker, info, metrics)
        if pe_valuation:
            valuations['P/E Multiple'] = pe_valuation
        
        # P/B Method
        pb_valuation = self.calculate_intrinsic_value_pbv(ticker, info, metrics)
        if pb_valuation:
            valuations['P/B Multiple'] = pb_valuation
        
        if not valuations:
            return None
        
        # Calculate average intrinsic value
        intrinsic_values = [v['intrinsic_value'] for v in valuations.values() if v.get('intrinsic_value', 0) > 0]
        
        if intrinsic_values:
            avg_intrinsic_value = np.mean(intrinsic_values)
            current_price = metrics.get('Current Price', 0)
            
            # Valuation assessment
            if current_price > 0:
                discount_premium = ((avg_intrinsic_value - current_price) / current_price) * 100
                
                if discount_premium > 20:
                    valuation_status = "Significantly Undervalued"
                elif discount_premium > 10:
                    valuation_status = "Undervalued"
                elif discount_premium > -10:
                    valuation_status = "Fairly Valued"
                elif discount_premium > -20:
                    valuation_status = "Overvalued"
                else:
                    valuation_status = "Significantly Overvalued"
            else:
                discount_premium = 0
                valuation_status = "Unable to Determine"
            
            return {
                'intrinsic_value': avg_intrinsic_value,
                'current_price': current_price,
                'discount_premium': discount_premium,
                'valuation_status': valuation_status,
                'methods': valuations,
                'number_of_methods': len(valuations)
            }
        
        return None








