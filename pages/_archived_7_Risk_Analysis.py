"""
Risk Analysis Page
Comprehensive risk metrics and portfolio risk analysis
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.risk_analysis import RiskAnalyzer
from utils.stock_analyzer import StockAnalyzer
from components.styling import apply_platform_theme, render_header, render_footer
from components.navigation import render_navigation

# Page configuration
st.set_page_config(
    page_title="Risk Analysis",
    page_icon="⚠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply theme and navigation
apply_platform_theme()
render_navigation()

# Initialize
if 'risk_analyzer' not in st.session_state:
    st.session_state.risk_analyzer = RiskAnalyzer()

if 'analyzer' not in st.session_state:
    st.session_state.analyzer = StockAnalyzer()

risk_analyzer = st.session_state.risk_analyzer
stock_analyzer = st.session_state.analyzer

# Header
render_header("⚠️ Risk Analysis", "Comprehensive risk metrics and portfolio risk assessment")

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Individual Stock Risk", "📈 Portfolio Risk", "⚖️ Risk Comparison"])

with tab1:
    st.markdown("### 📊 Individual Stock Risk Analysis")
    
    ticker = st.text_input("Enter Stock Ticker:", value="NVDA", key="risk_ticker").upper()
    time_period = st.selectbox("Time Period:", ["6mo", "1y", "2y", "5y"], index=1, key="risk_period")
    
    if st.button("Analyze Risk", key="analyze_risk"):
        with st.spinner(f"Analyzing risk for {ticker}..."):
            data = stock_analyzer.get_stock_data(ticker, period=time_period)
            
            if data and len(data['history']) > 0:
                prices = data['history']['Close']
                
                # Get market data for beta calculation
                import yfinance as yf
                market = yf.Ticker('SPY')
                market_hist = market.history(period=time_period)
                market_prices = market_hist['Close'] if len(market_hist) > 0 else None
                
                # Comprehensive risk analysis
                risk_metrics = risk_analyzer.comprehensive_risk_analysis(prices, market_prices)
                
                if risk_metrics:
                    st.success(f"Risk analysis complete for {ticker}")
                    
                    # Display metrics in columns
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.markdown("#### 📊 Volatility")
                        st.metric("Annualized Volatility", f"{risk_metrics.get('volatility', 0):.2f}%")
                    
                    with col2:
                        st.markdown("#### 📉 Value at Risk")
                        st.metric("VaR (5%)", f"{risk_metrics.get('var_5pct', 0)*100:+.2f}%")
                        st.metric("VaR (1%)", f"{risk_metrics.get('var_1pct', 0)*100:+.2f}%")
                    
                    with col3:
                        st.markdown("#### 📈 Risk-Adjusted Returns")
                        st.metric("Sharpe Ratio", f"{risk_metrics.get('sharpe_ratio', 0):.2f}")
                        st.metric("Sortino Ratio", f"{risk_metrics.get('sortino_ratio', 0):.2f}")
                    
                    with col4:
                        st.markdown("#### 📊 Drawdown")
                        st.metric("Max Drawdown", f"{risk_metrics.get('max_drawdown_pct', 0):.2f}%")
                        st.metric("Recovery Days", f"{risk_metrics.get('recovery_days', 0)}")
                    
                    st.markdown("---")
                    
                    # Detailed risk table
                    st.markdown("#### 📋 Complete Risk Metrics")
                    risk_df = pd.DataFrame([
                        {'Metric': 'Volatility (Annualized)', 'Value': f"{risk_metrics.get('volatility', 0):.2f}%"},
                        {'Metric': 'Beta (vs S&P 500)', 'Value': f"{risk_metrics.get('beta', 0):.2f}"},
                        {'Metric': 'Sharpe Ratio', 'Value': f"{risk_metrics.get('sharpe_ratio', 0):.2f}"},
                        {'Metric': 'Sortino Ratio', 'Value': f"{risk_metrics.get('sortino_ratio', 0):.2f}"},
                        {'Metric': 'Maximum Drawdown', 'Value': f"{risk_metrics.get('max_drawdown_pct', 0):.2f}%"},
                        {'Metric': 'VaR (5% Confidence)', 'Value': f"{risk_metrics.get('var_5pct', 0)*100:+.2f}%"},
                        {'Metric': 'VaR (1% Confidence)', 'Value': f"{risk_metrics.get('var_1pct', 0)*100:+.2f}%"},
                        {'Metric': 'Conditional VaR (5%)', 'Value': f"{risk_metrics.get('cvar_5pct', 0)*100:+.2f}%"},
                        {'Metric': 'Downside Capture', 'Value': f"{risk_metrics.get('downside_capture', 0):.2f}%"},
                        {'Metric': 'Upside Capture', 'Value': f"{risk_metrics.get('upside_capture', 0):.2f}%"},
                    ])
                    
                    st.dataframe(risk_df, use_container_width=True, hide_index=True)
                    
                    # Drawdown chart
                    st.markdown("---")
                    st.markdown("#### 📉 Drawdown Chart")
                    returns = prices.pct_change().dropna()
                    running_max = prices.expanding().max()
                    drawdown_pct = (prices / running_max - 1) * 100
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=drawdown_pct.index,
                        y=drawdown_pct,
                        fill='tozeroy',
                        mode='lines',
                        name='Drawdown %',
                        line=dict(color='red')
                    ))
                    fig.update_layout(
                        title='Drawdown Over Time',
                        xaxis_title='Date',
                        yaxis_title='Drawdown (%)',
                        height=400,
                        template='plotly_white'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("Could not calculate risk metrics")
            else:
                st.error(f"Could not fetch data for {ticker}")

with tab2:
    st.markdown("### 📈 Portfolio Risk Analysis")
    
    st.info("💡 Enter multiple stocks to analyze portfolio risk. This feature calculates correlation and portfolio-level risk metrics.")
    
    portfolio_tickers = st.text_input(
        "Enter Portfolio (comma-separated tickers):",
        value="AAPL, MSFT, GOOGL",
        key="portfolio_tickers"
    )
    
    if st.button("Analyze Portfolio Risk", key="analyze_portfolio"):
        tickers = [t.strip().upper() for t in portfolio_tickers.split(',')]
        
        with st.spinner("Analyzing portfolio risk..."):
            portfolio_data = {}
            returns_data = {}
            
            for ticker in tickers:
                data = stock_analyzer.get_stock_data(ticker, period="1y")
                if data and len(data['history']) > 0:
                    prices = data['history']['Close']
                    returns = prices.pct_change().dropna()
                    returns_data[ticker] = returns
                    risk_metrics = risk_analyzer.comprehensive_risk_analysis(prices)
                    portfolio_data[ticker] = risk_metrics
            
            if portfolio_data:
                st.success(f"Analyzed {len(portfolio_data)} stocks")
                
                # Create comparison table
                risk_comparison = []
                for ticker, metrics in portfolio_data.items():
                    risk_comparison.append({
                        'Ticker': ticker,
                        'Volatility': metrics.get('volatility', 0),
                        'Sharpe Ratio': metrics.get('sharpe_ratio', 0),
                        'Max Drawdown %': metrics.get('max_drawdown_pct', 0),
                        'Beta': metrics.get('beta', 0),
                        'VaR (5%)': metrics.get('var_5pct', 0) * 100
                    })
                
                risk_df = pd.DataFrame(risk_comparison)
                st.dataframe(
                    risk_df.style.background_gradient(subset=['Volatility', 'Sharpe Ratio'], cmap='RdYlGn')
                    .format({
                        'Volatility': '{:.2f}%',
                        'Sharpe Ratio': '{:.2f}',
                        'Max Drawdown %': '{:.2f}%',
                        'Beta': '{:.2f}',
                        'VaR (5%)': '{:+.2f}%'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
                
                # Correlation matrix
                if len(returns_data) > 1:
                    st.markdown("#### 🔗 Correlation Matrix")
                    returns_df = pd.DataFrame(returns_data)
                    correlation = returns_df.corr()
                    
                    import plotly.express as px
                    fig = px.imshow(
                        correlation,
                        labels=dict(x="Stock", y="Stock", color="Correlation"),
                        x=correlation.columns,
                        y=correlation.columns,
                        color_continuous_scale='RdBu',
                        aspect="auto"
                    )
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown("### ⚖️ Risk Comparison")
    
    st.write("Compare risk metrics across multiple stocks")
    
    compare_tickers = st.text_input(
        "Enter Stocks to Compare (comma-separated):",
        value="AAPL, NVDA, TSLA",
        key="compare_risk"
    )
    
    if st.button("Compare Risk", key="compare_risk_btn"):
        tickers = [t.strip().upper() for t in compare_tickers.split(',')]
        
        comparison_data = []
        for ticker in tickers:
            data = stock_analyzer.get_stock_data(ticker, period="1y")
            if data and len(data['history']) > 0:
                prices = data['history']['Close']
                risk_metrics = risk_analyzer.comprehensive_risk_analysis(prices)
                
                comparison_data.append({
                    'Ticker': ticker,
                    'Volatility': risk_metrics.get('volatility', 0),
                    'Sharpe': risk_metrics.get('sharpe_ratio', 0),
                    'Max DD': risk_metrics.get('max_drawdown_pct', 0),
                    'VaR 5%': risk_metrics.get('var_5pct', 0) * 100
                })
        
        if comparison_data:
            comp_df = pd.DataFrame(comparison_data)
            
            # Visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                import plotly.express as px
                fig = px.bar(comp_df, x='Ticker', y='Volatility',
                           title='Volatility Comparison',
                           color='Volatility',
                           color_continuous_scale='RdYlGn_r')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(comp_df, x='Ticker', y='Sharpe',
                           title='Sharpe Ratio Comparison',
                           color='Sharpe',
                           color_continuous_scale='RdYlGn')
                st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(
                comp_df.style.format({
                    'Volatility': '{:.2f}%',
                    'Sharpe': '{:.2f}',
                    'Max DD': '{:.2f}%',
                    'VaR 5%': '{:+.2f}%'
                }),
                use_container_width=True,
                hide_index=True
            )

render_footer()

