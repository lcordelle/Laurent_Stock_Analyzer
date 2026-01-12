"""
Batch Stock Comparison Page
Compare multiple stocks side by side with detailed analysis
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from utils.stock_analyzer import StockAnalyzer
from utils.visualizations import (
    create_comparison_table, create_score_breakdown_table,
    create_price_chart, create_volume_chart, create_financial_metrics_chart,
    create_trading_signals_chart
)
from utils.risk_analysis import RiskAnalyzer
from utils.valuation import StockValuation
from utils.ratings_aggregator import RatingsAggregator
from utils.peer_benchmark import PeerBenchmark
from utils.news_market import NewsMarketData
from utils.metric_display import display_enhanced_metric
from components.styling import apply_platform_theme, render_header, render_footer
from components.navigation import render_navigation

# Page configuration
st.set_page_config(
    page_title="Batch Stock Comparison",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply theme and navigation
apply_platform_theme()
render_navigation()

# Initialize analyzers
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = StockAnalyzer()
if 'risk_analyzer' not in st.session_state:
    st.session_state.risk_analyzer = RiskAnalyzer()
if 'valuation' not in st.session_state:
    st.session_state.valuation = StockValuation()
if 'ratings_aggregator' not in st.session_state:
    st.session_state.ratings_aggregator = RatingsAggregator()
if 'peer_benchmark' not in st.session_state:
    st.session_state.peer_benchmark = PeerBenchmark()
if 'news_market' not in st.session_state:
    st.session_state.news_market = NewsMarketData()

analyzer = st.session_state.analyzer
risk_analyzer = st.session_state.risk_analyzer
valuation = st.session_state.valuation
ratings_agg = st.session_state.ratings_aggregator
peer_bench = st.session_state.peer_benchmark
news_market = st.session_state.news_market

# Get settings from session state
time_period = st.session_state.get('time_period', '1y')

# Header
render_header("📈 Batch Stock Comparison", "Compare multiple stocks side by side")

st.write("Compare multiple stocks to identify the best investment opportunities")

# Input for multiple tickers
tickers_input = st.text_area(
    "Enter stock tickers (comma-separated):",
    value="NVDA, AMD, SOFI, PLTR",
    height=100
)

compare_btn = st.button("📊 Compare Stocks", type="primary")

if compare_btn and tickers_input:
    tickers = [t.strip().upper() for t in tickers_input.split(',')]
    
    if len(tickers) > 10:
        st.warning("⚠️ Please limit comparison to 10 stocks maximum")
        tickers = tickers[:10]
    
    stocks_data = {}
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, ticker in enumerate(tickers):
        status_text.text(f"Fetching data for {ticker}...")
        data = analyzer.get_stock_data(ticker, period=time_period)
        if data:
            stocks_data[ticker] = data
        progress_bar.progress((i + 1) / len(tickers))
    
    status_text.empty()
    progress_bar.empty()
    
    if stocks_data:
        # Calculate technical indicators and analysis for all stocks
        show_technical = st.session_state.get('show_technical', True)
        
        stocks_analysis = {}
        for ticker in stocks_data:
            if stocks_data[ticker] and len(stocks_data[ticker]['history']) > 0:
                data = stocks_data[ticker]
                metrics = analyzer.get_key_metrics(data)
                score = analyzer.calculate_score(data)
                
                if show_technical and len(data['history']) >= 20:
                    data['history'] = analyzer.calculate_technical_indicators(data['history'])
                
                forecast = analyzer.calculate_forecast(data, metrics, score)
                
                stocks_analysis[ticker] = {
                    'data': data,
                    'metrics': metrics,
                    'score': score,
                    'forecast': forecast
                }
        
        # Sort by score
        sorted_tickers = sorted(stocks_analysis.keys(), 
                               key=lambda t: stocks_analysis[t]['score']['total_score'], 
                               reverse=True)
        
        # Summary comparison table at top
        st.subheader("📊 Quick Comparison Summary")
        summary_data = []
        for ticker in sorted_tickers:
            info = stocks_analysis[ticker]
            summary_data.append({
                'Ticker': ticker,
                'Company': info['data']['info'].get('longName', ticker)[:30],
                'Score': info['score']['total_score'],
                'Price': info['metrics']['Current Price'],
                'Forecast': info['forecast']['forecast_price'] if info['forecast'] else None,
                'Change %': info['forecast']['forecast_change_pct'] if info['forecast'] else None,
                'Probability': info['forecast']['probability'] if info['forecast'] else None,
            })
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(
            summary_df.style.background_gradient(subset=['Score'], cmap='RdYlGn', vmin=0, vmax=100)
            .format({
                'Price': '${:.2f}',
                'Forecast': '${:.2f}' if 'Forecast' in summary_df.columns else None,
                'Change %': '{:+.2f}%' if 'Change %' in summary_df.columns else None,
                'Probability': '{:.1f}%' if 'Probability' in summary_df.columns else None,
            }),
            use_container_width=True,
            hide_index=True
        )
        
        st.markdown("---")
        st.subheader("📈 Detailed Analysis for Each Stock")
        
        # Display detailed analysis for each stock (same style as Single Analysis)
        for ticker in sorted_tickers:
            info = stocks_analysis[ticker]
            data = info['data']
            metrics = info['metrics']
            score = info['score']
            forecast = info['forecast']
            
            # Create expander for each stock
            with st.expander(f"📊 {ticker} - {data['info'].get('longName', ticker)} | Score: {score['total_score']}/100", expanded=False):
                # Company info
                st.write(data['info'].get('longBusinessSummary', 'No description available')[:500] + '...')
                
                # Score display
                col1, col2, col3 = st.columns(3)
                with col1:
                    score_color = 'positive' if score['total_score'] >= 70 else 'negative' if score['total_score'] < 50 else 'neutral'
                    st.markdown(f"### Overall Score")
                    st.markdown(f'<p class="{score_color}" style="font-size: 3rem; font-weight: bold;">{score["total_score"]}/100</p>', 
                              unsafe_allow_html=True)
                with col2:
                    st.metric("Current Price", f"${metrics['Current Price']:.2f}")
                    if forecast:
                        st.metric("Forecast Price", f"${forecast['forecast_price']:.2f}", 
                                 delta=f"{forecast['forecast_change_pct']:+.2f}%")
                with col3:
                    st.metric("Market Cap", f"${metrics['Market Cap']/1e9:.2f}B" if metrics['Market Cap'] > 1e9 else f"${metrics['Market Cap']/1e6:.2f}M")
                    if forecast:
                        st.metric("Probability", f"{forecast['probability']:.1f}%")
                
                st.markdown("---")
                
                # Score Breakdown Table with Forecast
                create_score_breakdown_table(score, forecast)
                
                st.markdown("---")
                
                # Tabs for different views - Now includes Trading Signals, Valuation, Ratings, Peers, and News
                tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
                    "📈 Charts", "🎯 Trading Signals", "📊 Key Metrics", "💰 Financials", "🎯 Technical", "⚠️ Risk",
                    "💎 Valuation", "⭐ Ratings", "🔗 Peers", "📰 News"
                ])
                
                with tab1:
                    if len(data['history']) > 0:
                        # Calculate intrinsic value for fair value tunnel
                        intrinsic_value = None
                        try:
                            valuation_result = valuation.comprehensive_valuation(ticker, data['info'], metrics)
                            if valuation_result:
                                intrinsic_value = valuation_result['intrinsic_value']
                        except:
                            pass  # If valuation fails, continue without fair value tunnel
                        
                        price_chart = create_price_chart(data, intrinsic_value=intrinsic_value, metrics=metrics)
                        if price_chart:
                            st.plotly_chart(price_chart, use_container_width=True)
                            st.caption("💡 **Chart Features:** Fair Value Tunnel (blue shaded area), VWAP (purple), Support/Resistance (green/red), Pivot Points (gray/orange), Moving Averages, Bollinger Bands, Entry/Exit Signals")
                        st.plotly_chart(create_volume_chart(data['history'], ticker), use_container_width=True)
                
                with tab2:
                    # Trading Signals Tab
                    st.markdown("### 🎯 Professional Trading Signals")
                    st.markdown("*Buy/Sell zones with entry/exit points, stop loss, and take profit targets*")
                    
                    # Calculate intrinsic value
                    intrinsic_value = None
                    try:
                        valuation_result = valuation.comprehensive_valuation(ticker, data['info'], metrics)
                        if valuation_result:
                            intrinsic_value = valuation_result['intrinsic_value']
                    except:
                        pass
                    
                    # Create trading signals chart
                    signals_result = create_trading_signals_chart(data, intrinsic_value=intrinsic_value, metrics=metrics, score=score)
                    
                    if signals_result:
                        signals_chart, trading_signals = signals_result
                        
                        if signals_chart:
                            st.plotly_chart(signals_chart, use_container_width=True)
                            
                            st.markdown("---")
                            
                            # Display detailed signals breakdown
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("#### 🟢 BUY Signals - Educational Guide")
                                st.caption("💡 Hover over chart markers for detailed explanations")
                                
                                if trading_signals['buy_signals']:
                                    for signal in trading_signals['buy_signals']:
                                        confidence_color = "#4CAF50" if signal['confidence'] == 'High' else "#FFA726"
                                        confidence_icon = "🟢" if signal['confidence'] == 'High' else "🟡"
                                        
                                        if signal['type'] == 'Value Buy':
                                            instruction = "📚 <b>Value Buy:</b> Stock is below fair value - long-term opportunity"
                                            action = "✅ Consider entering for fundamental value"
                                        elif signal['type'] == 'Technical Buy':
                                            instruction = "📚 <b>Technical Buy:</b> Oversold + Support - potential bounce"
                                            action = "✅ Consider short-medium term trade"
                                        else:
                                            instruction = "📚 <b>Momentum Buy:</b> Bullish trend - ride the momentum"
                                            action = "✅ Use trailing stops to protect gains"
                                        
                                        st.markdown(f"""
                                        <div style="background-color: #e8f5e9; padding: 20px; border-radius: 8px; border-left: 5px solid {confidence_color}; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                            <h4 style="margin: 0 0 10px 0; color: #1B5E20;">{confidence_icon} {signal['type']} - ${signal['price']:.2f}</h4>
                                            <p style="margin: 8px 0; color: #2E7D32; font-weight: bold;">📊 {signal['reason']}</p>
                                            <p style="margin: 10px 0 5px 0; color: #4CAF50; font-weight: bold;">{confidence_icon} Confidence: {signal['confidence']}</p>
                                            <hr style="margin: 10px 0; border-color: #a5d6a7;">
                                            <p style="margin: 8px 0; color: #1B5E20; font-size: 0.9em;">{instruction}</p>
                                            <p style="margin: 8px 0; color: #1B5E20; font-size: 0.9em;">{action}</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                else:
                                    st.info("📚 **No active BUY signals.** 💡 Wait for better entry opportunities.", unsafe_allow_html=True)
                            
                            with col2:
                                st.markdown("#### 🔴 SELL Signals - Educational Guide")
                                st.caption("💡 Hover over chart markers for detailed explanations")
                                
                                if trading_signals['sell_signals']:
                                    for signal in trading_signals['sell_signals']:
                                        confidence_color = "#EF5350" if signal['confidence'] == 'High' else "#FF9800"
                                        confidence_icon = "🔴" if signal['confidence'] == 'High' else "🟠"
                                        
                                        if signal['type'] == 'Value Sell':
                                            instruction = "📚 <b>Value Sell:</b> Stock is above fair value - profit opportunity"
                                            action = "✅ Consider taking profits"
                                        elif signal['type'] == 'Technical Sell':
                                            instruction = "📚 <b>Technical Sell:</b> Overbought + Resistance - potential pullback"
                                            action = "✅ Take profits near resistance"
                                        else:
                                            instruction = "📚 <b>Momentum Sell:</b> Bearish trend - protect capital"
                                            action = "✅ Exit to avoid further decline"
                                        
                                        st.markdown(f"""
                                        <div style="background-color: #ffebee; padding: 20px; border-radius: 8px; border-left: 5px solid {confidence_color}; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                            <h4 style="margin: 0 0 10px 0; color: #B71C1C;">{confidence_icon} {signal['type']} - ${signal['price']:.2f}</h4>
                                            <p style="margin: 8px 0; color: #C62828; font-weight: bold;">📊 {signal['reason']}</p>
                                            <p style="margin: 10px 0 5px 0; color: #EF5350; font-weight: bold;">{confidence_icon} Confidence: {signal['confidence']}</p>
                                            <hr style="margin: 10px 0; border-color: #ef9a9a;">
                                            <p style="margin: 8px 0; color: #B71C1C; font-size: 0.9em;">{instruction}</p>
                                            <p style="margin: 8px 0; color: #B71C1C; font-size: 0.9em;">{action}</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                else:
                                    st.info("📚 **No active SELL signals.** 💡 Stock not showing overvaluation.", unsafe_allow_html=True)
                            
                            st.markdown("---")
                            
                            # Risk Management
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("#### 🛡️ Risk Management - Educational Guide")
                                if trading_signals['stop_loss']:
                                    sl = trading_signals['stop_loss']
                                    st.markdown(f"""
                                    <div style="background-color: #fff3e0; padding: 20px; border-radius: 8px; border-left: 5px solid #FF9800; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                        <h4 style="margin: 0 0 10px 0; color: #E65100;">🛡️ Stop Loss: ${sl['price']:.2f}</h4>
                                        <p style="margin: 8px 0; color: #F57C00; font-weight: bold;">📊 {sl['reason']}</p>
                                        <hr style="margin: 10px 0; border-color: #ffb74d;">
                                        <p style="margin: 8px 0; color: #E65100; font-size: 0.9em;">
                                            <b>📚 What is a Stop Loss?</b><br>
                                            A stop loss limits your maximum loss per share. Always set one before entering a trade.
                                        </p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                else:
                                    st.info("📚 **Calculate entry signals first.** 💡 Stop loss is essential for risk management.", unsafe_allow_html=True)
                            
                            with col2:
                                st.markdown("#### 🎯 Take Profit Targets - Educational Guide")
                                if trading_signals['take_profit']:
                                    for tp in trading_signals['take_profit']:
                                        st.markdown(f"""
                                        <div style="background-color: #e8f5e9; padding: 20px; border-radius: 8px; border-left: 5px solid #4CAF50; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                            <h4 style="margin: 0 0 10px 0; color: #1B5E20;">🎯 {tp['label']}</h4>
                                            <p style="margin: 8px 0; color: #2E7D32; font-size: 0.9em;">
                                                <b>📚 Take Profit Strategy:</b><br>
                                                Consider taking partial profits at each target. Let remaining position run to higher targets.
                                            </p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                else:
                                    st.info("📚 **Calculate entry signals first.** 💡 Setting profit targets helps lock in gains.", unsafe_allow_html=True)
                    else:
                        st.warning("⚠️ Trading signals not available. Ensure technical indicators are enabled and sufficient historical data is available.")
                
                with tab3:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("### 📍 Price Information")
                        st.markdown(f"**Today's Range:** {metrics['Today Range']}")
                        st.caption("💡 The trading range for today (low to high price)")
                        
                        st.markdown(f"**52 Week Range:** {metrics['52 Week Range']}")
                        st.caption("💡 The lowest and highest prices over the past year - shows price volatility range")
                        
                        display_enhanced_metric("Target Price", f"${metrics['Target Price']:.2f}", metric_name="Target Price")
                        st.caption("💡 Analyst consensus target price - indicates expected future price")
                        
                        display_enhanced_metric("Beta", f"{metrics['Beta']:.2f}", metric_name="Beta")
                    
                    with col2:
                        st.markdown("### 📊 Valuation")
                        display_enhanced_metric("P/E Ratio", f"{metrics['P/E Ratio']:.2f}", metric_name="P/E Ratio")
                        display_enhanced_metric("Forward P/E", f"{metrics['Forward P/E']:.2f}", metric_name="Forward P/E")
                        display_enhanced_metric("PEG Ratio", f"{metrics['PEG Ratio']:.2f}", metric_name="PEG Ratio")
                        display_enhanced_metric("Price/Book", f"{metrics['Price to Book']:.2f}", metric_name="Price to Book")
                    
                    with col3:
                        st.markdown("### 💵 Returns")
                        display_enhanced_metric("Dividend Yield", f"{metrics['Dividend Yield']:.2f}%", metric_name="Dividend Yield")
                        display_enhanced_metric("ROE", f"{metrics['ROE']:.2f}%", metric_name="ROE")
                        display_enhanced_metric("ROA", f"{metrics['ROA']:.2f}%", metric_name="ROA")
                        st.markdown(f"**Analyst Rating:** {metrics['Analyst Rating'].upper()}")
                        st.caption("💡 Consensus analyst recommendation: Buy, Hold, or Sell")
                
                with tab3:
                    st.markdown("### 💰 Financial Health Metrics")
                    st.markdown("*Color-coded indicators: 🟢 Excellent | 🟡 Good | 🟠 Fair | 🔴 Poor*")
                    
                    chart = create_financial_metrics_chart(metrics)
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("#### 💰 Profitability")
                        # Gross Margin
                        gm = metrics['Gross Margin']
                        gm_indicator = "🟢" if gm >= 40 else "🟡" if gm >= 20 else "🟠" if gm >= 10 else "🔴"
                        gm_status = "Excellent" if gm >= 40 else "Good" if gm >= 20 else "Fair" if gm >= 10 else "Poor"
                        st.markdown(f"""
                        <div style="background-color: {'#e8f5e9' if gm >= 40 else '#fff9c4' if gm >= 20 else '#ffe0b2' if gm >= 10 else '#ffebee'}; 
                                    padding: 15px; border-radius: 8px; border-left: 5px solid {'#4CAF50' if gm >= 40 else '#FFA726' if gm >= 20 else '#FF9800' if gm >= 10 else '#EF5350'}; 
                                    margin-bottom: 10px;">
                            <h4 style="margin: 0; color: {'#1B5E20' if gm >= 40 else '#F57F17' if gm >= 20 else '#E65100' if gm >= 10 else '#B71C1C'};">
                                {gm_indicator} Gross Margin: {gm:.2f}% - {gm_status}
                            </h4>
                        </div>
                        """, unsafe_allow_html=True)
                        display_enhanced_metric("Gross Margin", f"{gm:.2f}%", metric_name="Gross Margin")
                        
                        # Operating Margin
                        om = metrics['Operating Margin']
                        om_indicator = "🟢" if om >= 20 else "🟡" if om >= 10 else "🟠" if om >= 5 else "🔴"
                        om_status = "Excellent" if om >= 20 else "Good" if om >= 10 else "Fair" if om >= 5 else "Poor"
                        st.markdown(f"""
                        <div style="background-color: {'#e8f5e9' if om >= 20 else '#fff9c4' if om >= 10 else '#ffe0b2' if om >= 5 else '#ffebee'}; 
                                    padding: 15px; border-radius: 8px; border-left: 5px solid {'#4CAF50' if om >= 20 else '#FFA726' if om >= 10 else '#FF9800' if om >= 5 else '#EF5350'}; 
                                    margin-bottom: 10px;">
                            <h4 style="margin: 0; color: {'#1B5E20' if om >= 20 else '#F57F17' if om >= 10 else '#E65100' if om >= 5 else '#B71C1C'};">
                                {om_indicator} Operating Margin: {om:.2f}% - {om_status}
                            </h4>
                        </div>
                        """, unsafe_allow_html=True)
                        display_enhanced_metric("Operating Margin", f"{om:.2f}%", metric_name="Operating Margin")
                        
                        # Profit Margin
                        pm = metrics['Profit Margin']
                        pm_indicator = "🟢" if pm >= 15 else "🟡" if pm >= 5 else "🟠" if pm >= 2 else "🔴"
                        pm_status = "Excellent" if pm >= 15 else "Good" if pm >= 5 else "Fair" if pm >= 2 else "Poor"
                        st.markdown(f"""
                        <div style="background-color: {'#e8f5e9' if pm >= 15 else '#fff9c4' if pm >= 5 else '#ffe0b2' if pm >= 2 else '#ffebee'}; 
                                    padding: 15px; border-radius: 8px; border-left: 5px solid {'#4CAF50' if pm >= 15 else '#FFA726' if pm >= 5 else '#FF9800' if pm >= 2 else '#EF5350'}; 
                                    margin-bottom: 10px;">
                            <h4 style="margin: 0; color: {'#1B5E20' if pm >= 15 else '#F57F17' if pm >= 5 else '#E65100' if pm >= 2 else '#B71C1C'};">
                                {pm_indicator} Profit Margin: {pm:.2f}% - {pm_status}
                            </h4>
                        </div>
                        """, unsafe_allow_html=True)
                        display_enhanced_metric("Profit Margin", f"{pm:.2f}%", metric_name="Profit Margin")
                    
                    with col2:
                        st.markdown("#### 📈 Growth")
                        # Revenue Growth
                        rg = metrics['Revenue Growth']
                        rg_indicator = "🟢" if rg >= 15 else "🟡" if rg >= 5 else "🟠" if rg >= 0 else "🔴"
                        rg_status = "Excellent" if rg >= 15 else "Good" if rg >= 5 else "Fair" if rg >= 0 else "Declining"
                        st.markdown(f"""
                        <div style="background-color: {'#e8f5e9' if rg >= 15 else '#fff9c4' if rg >= 5 else '#ffe0b2' if rg >= 0 else '#ffebee'}; 
                                    padding: 15px; border-radius: 8px; border-left: 5px solid {'#4CAF50' if rg >= 15 else '#FFA726' if rg >= 5 else '#FF9800' if rg >= 0 else '#EF5350'}; 
                                    margin-bottom: 10px;">
                            <h4 style="margin: 0; color: {'#1B5E20' if rg >= 15 else '#F57F17' if rg >= 5 else '#E65100' if rg >= 0 else '#B71C1C'};">
                                {rg_indicator} Revenue Growth: {rg:+.2f}% - {rg_status}
                            </h4>
                        </div>
                        """, unsafe_allow_html=True)
                        display_enhanced_metric("Revenue Growth", f"{rg:+.2f}%", metric_name="Revenue Growth")
                        
                        # Earnings Growth
                        eg = metrics['Earnings Growth']
                        eg_indicator = "🟢" if eg >= 15 else "🟡" if eg >= 5 else "🟠" if eg >= 0 else "🔴"
                        eg_status = "Excellent" if eg >= 15 else "Good" if eg >= 5 else "Fair" if eg >= 0 else "Declining"
                        st.markdown(f"""
                        <div style="background-color: {'#e8f5e9' if eg >= 15 else '#fff9c4' if eg >= 5 else '#ffe0b2' if eg >= 0 else '#ffebee'}; 
                                    padding: 15px; border-radius: 8px; border-left: 5px solid {'#4CAF50' if eg >= 15 else '#FFA726' if eg >= 5 else '#FF9800' if eg >= 0 else '#EF5350'}; 
                                    margin-bottom: 10px;">
                            <h4 style="margin: 0; color: {'#1B5E20' if eg >= 15 else '#F57F17' if eg >= 5 else '#E65100' if eg >= 0 else '#B71C1C'};">
                                {eg_indicator} Earnings Growth: {eg:+.2f}% - {eg_status}
                            </h4>
                        </div>
                        """, unsafe_allow_html=True)
                        display_enhanced_metric("Earnings Growth", f"{eg:+.2f}%", metric_name="Earnings Growth")
                    
                    with col3:
                        st.markdown("#### 🏦 Financial Strength")
                        # Debt/Equity
                        de = metrics['Debt to Equity']
                        de_indicator = "🟢" if de <= 0.5 else "🟡" if de <= 1.5 else "🟠" if de <= 2.5 else "🔴"
                        de_status = "Excellent" if de <= 0.5 else "Good" if de <= 1.5 else "Fair" if de <= 2.5 else "High Debt"
                        st.markdown(f"""
                        <div style="background-color: {'#e8f5e9' if de <= 0.5 else '#fff9c4' if de <= 1.5 else '#ffe0b2' if de <= 2.5 else '#ffebee'}; 
                                    padding: 15px; border-radius: 8px; border-left: 5px solid {'#4CAF50' if de <= 0.5 else '#FFA726' if de <= 1.5 else '#FF9800' if de <= 2.5 else '#EF5350'}; 
                                    margin-bottom: 10px;">
                            <h4 style="margin: 0; color: {'#1B5E20' if de <= 0.5 else '#F57F17' if de <= 1.5 else '#E65100' if de <= 2.5 else '#B71C1C'};">
                                {de_indicator} Debt/Equity: {de:.2f} - {de_status}
                            </h4>
                        </div>
                        """, unsafe_allow_html=True)
                        display_enhanced_metric("Debt/Equity", f"{de:.2f}", metric_name="Debt to Equity")
                        
                        # Current Ratio
                        cr = metrics['Current Ratio']
                        cr_indicator = "🟢" if cr >= 1.5 else "🟡" if cr >= 1.0 else "🔴"
                        cr_status = "Excellent" if cr >= 1.5 else "Adequate" if cr >= 1.0 else "Low Liquidity"
                        st.markdown(f"""
                        <div style="background-color: {'#e8f5e9' if cr >= 1.5 else '#fff9c4' if cr >= 1.0 else '#ffebee'}; 
                                    padding: 15px; border-radius: 8px; border-left: 5px solid {'#4CAF50' if cr >= 1.5 else '#FFA726' if cr >= 1.0 else '#EF5350'}; 
                                    margin-bottom: 10px;">
                            <h4 style="margin: 0; color: {'#1B5E20' if cr >= 1.5 else '#F57F17' if cr >= 1.0 else '#B71C1C'};">
                                {cr_indicator} Current Ratio: {cr:.2f} - {cr_status}
                            </h4>
                        </div>
                        """, unsafe_allow_html=True)
                        display_enhanced_metric("Current Ratio", f"{cr:.2f}", metric_name="Current Ratio")
                        
                        # Quick Ratio
                        qr = metrics['Quick Ratio']
                        qr_indicator = "🟢" if qr >= 1.0 else "🟡" if qr >= 0.5 else "🔴"
                        qr_status = "Excellent" if qr >= 1.0 else "Adequate" if qr >= 0.5 else "Low Liquidity"
                        st.markdown(f"""
                        <div style="background-color: {'#e8f5e9' if qr >= 1.0 else '#fff9c4' if qr >= 0.5 else '#ffebee'}; 
                                    padding: 15px; border-radius: 8px; border-left: 5px solid {'#4CAF50' if qr >= 1.0 else '#FFA726' if qr >= 0.5 else '#EF5350'}; 
                                    margin-bottom: 10px;">
                            <h4 style="margin: 0; color: {'#1B5E20' if qr >= 1.0 else '#F57F17' if qr >= 0.5 else '#B71C1C'};">
                                {qr_indicator} Quick Ratio: {qr:.2f} - {qr_status}
                            </h4>
                        </div>
                        """, unsafe_allow_html=True)
                        display_enhanced_metric("Quick Ratio", f"{qr:.2f}", metric_name="Quick Ratio")
                
                with tab4:
                    if show_technical and 'RSI' in data['history'].columns:
                        st.markdown("### Technical Indicators")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            latest_rsi = data['history']['RSI'].iloc[-1]
                            rsi_status = "Oversold" if latest_rsi < 30 else "Overbought" if latest_rsi > 70 else "Neutral"
                            display_enhanced_metric("RSI (14)", f"{latest_rsi:.2f}", delta=rsi_status, metric_name="RSI")
                            
                            latest_macd = data['history']['MACD'].iloc[-1]
                            latest_signal = data['history']['Signal'].iloc[-1]
                            macd_trend = "Bullish" if latest_macd > latest_signal else "Bearish"
                            display_enhanced_metric("MACD", f"{latest_macd:.2f}", delta=macd_trend, metric_name="MACD")
                        
                        with col2:
                            current_price = data['history']['Close'].iloc[-1]
                            sma_20 = data['history']['SMA_20'].iloc[-1]
                            sma_50 = data['history']['SMA_50'].iloc[-1]
                            
                            ma_trend = "Above" if current_price > sma_20 else "Below"
                            delta_color = "normal" if current_price > sma_20 else "inverse"
                            st.metric("Price vs SMA 20", f"${current_price:.2f}", 
                                    delta=f"{ma_trend} ${sma_20:.2f}", delta_color=delta_color)
                            st.caption("💡 SMA 20: 20-day moving average. Price above = bullish trend, below = bearish trend")
                            
                            ma_trend_50 = "Above" if current_price > sma_50 else "Below"
                            delta_color_50 = "normal" if current_price > sma_50 else "inverse"
                            st.metric("Price vs SMA 50", f"${current_price:.2f}", 
                                    delta=f"{ma_trend_50} ${sma_50:.2f}", delta_color=delta_color_50)
                            st.caption("💡 SMA 50: 50-day moving average. Longer-term trend indicator. Above = long-term uptrend")
                    else:
                        st.info("Enable 'Show Technical Indicators' in settings to view technical analysis")
                
                with tab5:
                    # Risk Analysis
                    st.markdown("### ⚠️ Risk Analysis")
                    st.markdown("*Color-coded risk levels: 🟢 Low Risk | 🟡 Moderate Risk | 🟠 High Risk | 🔴 Very High Risk*")
                    
                    hist = data.get('history')
                    if hist is not None and len(hist) > 0:
                        prices = hist['Close']
                        import yfinance as yf
                        market = yf.Ticker('SPY')
                        market_hist = market.history(period=time_period)
                        market_prices = market_hist['Close'] if len(market_hist) > 0 else None
                        risk_metrics = risk_analyzer.comprehensive_risk_analysis(prices, market_prices)
                        if risk_metrics:
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                vol = risk_metrics.get('volatility', 0)
                                vol_indicator = "🟢" if vol < 20 else "🟡" if vol < 40 else "🟠" if vol < 60 else "🔴"
                                vol_status = "Low Risk" if vol < 20 else "Moderate Risk" if vol < 40 else "High Risk" if vol < 60 else "Very High Risk"
                                st.markdown(f"""
                                <div style="background-color: {'#e8f5e9' if vol < 20 else '#fff9c4' if vol < 40 else '#ffe0b2' if vol < 60 else '#ffebee'}; 
                                            padding: 15px; border-radius: 8px; border-left: 5px solid {'#4CAF50' if vol < 20 else '#FFA726' if vol < 40 else '#FF9800' if vol < 60 else '#EF5350'}; 
                                            margin-bottom: 10px;">
                                    <h4 style="margin: 0; color: {'#1B5E20' if vol < 20 else '#F57F17' if vol < 40 else '#E65100' if vol < 60 else '#B71C1C'};">
                                        {vol_indicator} Volatility: {vol:.2f}% - {vol_status}
                                    </h4>
                                </div>
                                """, unsafe_allow_html=True)
                                display_enhanced_metric("Volatility", f"{vol:.2f}%", 
                                                       help_text="💡 Annual price volatility. Under 20% is low (stable), 20-40% is moderate, over 40% is high volatility (risky).")
                                display_enhanced_metric("Beta", f"{risk_metrics.get('beta', 0):.2f}", metric_name="Beta")
                            with col2:
                                sharpe = risk_metrics.get('sharpe_ratio', 0)
                                sharpe_indicator = "🟢" if sharpe >= 2.0 else "🟡" if sharpe >= 1.0 else "🟠" if sharpe >= 0.5 else "🔴"
                                sharpe_status = "Excellent" if sharpe >= 2.0 else "Good" if sharpe >= 1.0 else "Fair" if sharpe >= 0.5 else "Poor"
                                st.markdown(f"""
                                <div style="background-color: {'#e8f5e9' if sharpe >= 2.0 else '#fff9c4' if sharpe >= 1.0 else '#ffe0b2' if sharpe >= 0.5 else '#ffebee'}; 
                                            padding: 15px; border-radius: 8px; border-left: 5px solid {'#4CAF50' if sharpe >= 2.0 else '#FFA726' if sharpe >= 1.0 else '#FF9800' if sharpe >= 0.5 else '#EF5350'}; 
                                            margin-bottom: 10px;">
                                    <h4 style="margin: 0; color: {'#1B5E20' if sharpe >= 2.0 else '#F57F17' if sharpe >= 1.0 else '#E65100' if sharpe >= 0.5 else '#B71C1C'};">
                                        {sharpe_indicator} Sharpe Ratio: {sharpe:.2f} - {sharpe_status}
                                    </h4>
                                </div>
                                """, unsafe_allow_html=True)
                                display_enhanced_metric("Sharpe Ratio", f"{sharpe:.2f}", metric_name="Sharpe Ratio")
                                mdd = risk_metrics.get('max_drawdown_pct', 0)
                                mdd_indicator = "🟢" if mdd > -15 else "🟡" if mdd > -30 else "🟠" if mdd > -50 else "🔴"
                                mdd_status = "Low Risk" if mdd > -15 else "Moderate Risk" if mdd > -30 else "High Risk" if mdd > -50 else "Very High Risk"
                                st.markdown(f"""
                                <div style="background-color: {'#e8f5e9' if mdd > -15 else '#fff9c4' if mdd > -30 else '#ffe0b2' if mdd > -50 else '#ffebee'}; 
                                            padding: 15px; border-radius: 8px; border-left: 5px solid {'#4CAF50' if mdd > -15 else '#FFA726' if mdd > -30 else '#FF9800' if mdd > -50 else '#EF5350'}; 
                                            margin-bottom: 10px;">
                                    <h4 style="margin: 0; color: {'#1B5E20' if mdd > -15 else '#F57F17' if mdd > -30 else '#E65100' if mdd > -50 else '#B71C1C'};">
                                        {mdd_indicator} Max Drawdown: {mdd:.2f}% - {mdd_status}
                                    </h4>
                                </div>
                                """, unsafe_allow_html=True)
                                display_enhanced_metric("Max Drawdown", f"{mdd:.2f}%", 
                                                       help_text="💡 Largest peak-to-trough decline. Under -15% is good, -15% to -30% is moderate, over -30% indicates high downside risk.")
                            with col3:
                                var5 = risk_metrics.get('var_5pct', 0) * 100
                                var_indicator = "🟢" if abs(var5) < 5 else "🟡" if abs(var5) < 10 else "🟠" if abs(var5) < 20 else "🔴"
                                var_status = "Low Risk" if abs(var5) < 5 else "Moderate Risk" if abs(var5) < 10 else "High Risk" if abs(var5) < 20 else "Very High Risk"
                                st.markdown(f"""
                                <div style="background-color: {'#e8f5e9' if abs(var5) < 5 else '#fff9c4' if abs(var5) < 10 else '#ffe0b2' if abs(var5) < 20 else '#ffebee'}; 
                                            padding: 15px; border-radius: 8px; border-left: 5px solid {'#4CAF50' if abs(var5) < 5 else '#FFA726' if abs(var5) < 10 else '#FF9800' if abs(var5) < 20 else '#EF5350'}; 
                                            margin-bottom: 10px;">
                                    <h4 style="margin: 0; color: {'#1B5E20' if abs(var5) < 5 else '#F57F17' if abs(var5) < 10 else '#E65100' if abs(var5) < 20 else '#B71C1C'};">
                                        {var_indicator} VaR (5%): {var5:+.2f}% - {var_status}
                                    </h4>
                                </div>
                                """, unsafe_allow_html=True)
                                st.markdown(f"**VaR (5%):** {var5:+.2f}%")
                                st.caption("💡 Value at Risk: Maximum expected loss with 95% confidence over given period")
                
                with tab6:
                    # Valuation Analysis
                    st.markdown("### 💎 Valuation Analysis")
                    st.markdown("*Color-coded valuation: 🟢 Undervalued (Buy) | 🟡 Fair Value | 🔴 Overvalued (Sell)*")
                    try:
                        valuation_result = valuation.comprehensive_valuation(ticker, data['info'], metrics)
                        if valuation_result:
                            discount_premium = valuation_result.get('discount_premium', 0)
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.markdown(f"**Intrinsic Value:** ${valuation_result['intrinsic_value']:.2f}")
                                st.caption("💡 Estimated true value based on fundamental analysis - what the stock should be worth")
                            with col2:
                                st.markdown(f"**Market Price:** ${valuation_result['current_price']:.2f}")
                                st.caption("💡 The current trading price of the stock")
                            with col3:
                                if discount_premium > 20:
                                    status_emoji = "🟢"
                                    status_color = "#4CAF50"
                                    status_bg = "#e8f5e9"
                                    status_text = "#1B5E20"
                                    status_label = "Strong Buy Opportunity"
                                elif discount_premium > 10:
                                    status_emoji = "🟢"
                                    status_color = "#4CAF50"
                                    status_bg = "#e8f5e9"
                                    status_text = "#1B5E20"
                                    status_label = "Buy Opportunity"
                                elif discount_premium > -10:
                                    status_emoji = "🟡"
                                    status_color = "#FFA726"
                                    status_bg = "#fff9c4"
                                    status_text = "#F57F17"
                                    status_label = "Fair Value"
                                elif discount_premium > -20:
                                    status_emoji = "🟠"
                                    status_color = "#FF9800"
                                    status_bg = "#ffe0b2"
                                    status_text = "#E65100"
                                    status_label = "Caution - Overvalued"
                                else:
                                    status_emoji = "🔴"
                                    status_color = "#EF5350"
                                    status_bg = "#ffebee"
                                    status_text = "#B71C1C"
                                    status_label = "Significantly Overvalued"
                                
                                st.markdown(f"""
                                <div style="background-color: {status_bg}; 
                                            padding: 15px; border-radius: 8px; border-left: 5px solid {status_color}; 
                                            margin-bottom: 10px;">
                                    <h4 style="margin: 0; color: {status_text};">
                                        {status_emoji} Valuation Gap: {discount_premium:+.1f}% - {status_label}
                                    </h4>
                                </div>
                                """, unsafe_allow_html=True)
                                st.markdown(f"**Status:** {status_emoji} {valuation_result['valuation_status']}")
                                st.caption("💡 Overall valuation assessment based on multiple valuation methods")
                    except:
                        st.info("Valuation data not available")
                
                with tab7:
                    # Ratings Summary
                    st.markdown("### ⭐ Ratings Summary")
                    st.markdown("*Color-coded ratings: 🟢 Strong Buy/Buy | 🟡 Hold | 🔴 Sell*")
                    try:
                        ratings_result = ratings_agg.aggregate_ratings(ticker, score, data['info'])
                        if ratings_result:
                            composite = ratings_result['composite_rating']
                            avg_score = ratings_result['average_rating_score']
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if "STRONG BUY" in composite.upper() or "BUY" in composite.upper():
                                    rating_emoji = "🟢"
                                    rating_color = "#4CAF50"
                                    rating_bg = "#e8f5e9"
                                    rating_text = "#1B5E20"
                                    rating_status = "Buy"
                                elif "SELL" in composite.upper():
                                    rating_emoji = "🔴"
                                    rating_color = "#EF5350"
                                    rating_bg = "#ffebee"
                                    rating_text = "#B71C1C"
                                    rating_status = "Sell"
                                else:
                                    rating_emoji = "🟡"
                                    rating_color = "#FFA726"
                                    rating_bg = "#fff9c4"
                                    rating_text = "#F57F17"
                                    rating_status = "Hold"
                                
                                st.markdown(f"""
                                <div style="background-color: {rating_bg}; 
                                            padding: 15px; border-radius: 8px; border-left: 5px solid {rating_color}; 
                                            margin-bottom: 10px;">
                                    <h4 style="margin: 0; color: {rating_text};">
                                        {rating_emoji} Composite Rating: {composite} - {rating_status}
                                    </h4>
                                </div>
                                """, unsafe_allow_html=True)
                                st.caption("💡 Aggregated rating from multiple analyst sources - overall consensus recommendation")
                            with col2:
                                if avg_score >= 4.0:
                                    score_indicator = "🟢"
                                    score_status = "Excellent"
                                    score_color = "#4CAF50"
                                    score_bg = "#e8f5e9"
                                    score_text = "#1B5E20"
                                elif avg_score >= 3.0:
                                    score_indicator = "🟡"
                                    score_status = "Good"
                                    score_color = "#FFA726"
                                    score_bg = "#fff9c4"
                                    score_text = "#F57F17"
                                elif avg_score >= 2.0:
                                    score_indicator = "🟠"
                                    score_status = "Fair"
                                    score_color = "#FF9800"
                                    score_bg = "#ffe0b2"
                                    score_text = "#E65100"
                                else:
                                    score_indicator = "🔴"
                                    score_status = "Poor"
                                    score_color = "#EF5350"
                                    score_bg = "#ffebee"
                                    score_text = "#B71C1C"
                                
                                st.markdown(f"""
                                <div style="background-color: {score_bg}; 
                                            padding: 15px; border-radius: 8px; border-left: 5px solid {score_color}; 
                                            margin-bottom: 10px;">
                                    <h4 style="margin: 0; color: {score_text};">
                                        {score_indicator} Average Score: {avg_score:.2f}/5.0 - {score_status}
                                    </h4>
                                </div>
                                """, unsafe_allow_html=True)
                                st.caption("💡 Average rating score across all sources (5.0 = Strong Buy, 1.0 = Strong Sell)")
                            
                            if len(ratings_result['ratings_df']) > 0:
                                st.markdown("---")
                                st.markdown("#### 📊 Ratings by Source")
                                st.dataframe(ratings_result['ratings_df'][['source', 'rating', 'rating_score']], 
                                          use_container_width=True, hide_index=True)
                    except:
                        st.info("Ratings data not available")
                
                with tab8:
                    # Peer Benchmarking
                    st.markdown("### 🔗 Peer Benchmarking")
                    try:
                        peers = peer_bench.get_sector_peers(ticker, data['info'].get('sector'))
                        if peers:
                            benchmark_result = peer_bench.benchmark_against_peers(ticker, metrics, score, peers)
                            if benchmark_result and benchmark_result.get('benchmark_summary'):
                                summary = benchmark_result['benchmark_summary']
                                st.metric("Peer Rank", f"{summary['position']}/{summary['total_peers']}")
                                st.metric("Percentile", f"{summary['percentile']:.0f}th")
                            if benchmark_result and len(benchmark_result.get('peer_comparison', [])) > 0:
                                comp_df = benchmark_result['peer_comparison'][['ticker', 'score', 'pe_ratio', 'roe']].head(5)
                                comp_df.columns = ['Ticker', 'Score', 'P/E', 'ROE']
                                st.dataframe(comp_df, use_container_width=True, hide_index=True)
                    except:
                        st.info("Peer data not available")
                
                with tab9:
                    # Top News for Stock
                    st.markdown("### 📰 Top News for {}".format(ticker.upper()))
                    st.markdown("*Latest news articles and market updates related to this stock*")
                    
                    try:
                        with st.spinner(f"Fetching latest news for {ticker}..."):
                            # Get top news articles
                            news_limit = st.slider("Number of articles to display", 5, 20, 10, key=f"news_limit_{ticker}")
                            news_articles = news_market.get_stock_news(ticker, limit=news_limit)
                            
                            if news_articles and len(news_articles) > 0:
                                st.success(f"✅ Found {len(news_articles)} news article(s)")
                                
                                # Display news articles
                                for idx, article in enumerate(news_articles, 1):
                                    # Determine article importance/recency
                                    time_ago = ""
                                    published_dt = article.get('published')
                                    
                                    if published_dt:
                                        # Handle timezone-aware vs naive datetimes
                                        try:
                                            # Get current time (timezone-aware if published_dt is aware)
                                            now = datetime.now(published_dt.tzinfo) if published_dt.tzinfo else datetime.now()
                                            # If published_dt is aware but now is naive, make now aware
                                            if published_dt.tzinfo and not now.tzinfo:
                                                from datetime import timezone
                                                now = datetime.now(timezone.utc).replace(tzinfo=None)
                                                published_dt = published_dt.replace(tzinfo=None)
                                            # If published_dt is naive but now is aware, make published_dt aware
                                            elif now.tzinfo and not published_dt.tzinfo:
                                                from datetime import timezone
                                                published_dt = published_dt.replace(tzinfo=timezone.utc)
                                            
                                            time_diff = now - published_dt
                                            
                                            if time_diff.days == 0:
                                                hours = time_diff.seconds // 3600
                                                if hours == 0:
                                                    minutes = time_diff.seconds // 60
                                                    time_ago = f" ({minutes} minutes ago)"
                                                else:
                                                    time_ago = f" ({hours} hour{'s' if hours > 1 else ''} ago)"
                                            elif time_diff.days == 1:
                                                time_ago = " (1 day ago)"
                                            else:
                                                time_ago = f" ({time_diff.days} days ago)"
                                        except Exception:
                                            # If datetime comparison fails, just skip time_ago
                                            time_ago = ""
                                    
                                    # Color code based on recency
                                    if published_dt:
                                        try:
                                            # Get current time (timezone-aware if published_dt is aware)
                                            now = datetime.now(published_dt.tzinfo) if published_dt.tzinfo else datetime.now()
                                            # If published_dt is aware but now is naive, make now aware
                                            if published_dt.tzinfo and not now.tzinfo:
                                                from datetime import timezone
                                                now = datetime.now(timezone.utc).replace(tzinfo=None)
                                                published_dt = published_dt.replace(tzinfo=None)
                                            # If published_dt is naive but now is aware, make published_dt aware
                                            elif now.tzinfo and not published_dt.tzinfo:
                                                from datetime import timezone
                                                published_dt = published_dt.replace(tzinfo=timezone.utc)
                                            
                                            time_diff = now - published_dt
                                            
                                            if time_diff.days == 0:
                                                border_color = "#4CAF50"  # Green for today
                                                bg_color = "#e8f5e9"
                                                recency_label = "🟢 Today"
                                            elif time_diff.days <= 7:
                                                border_color = "#FFA726"  # Orange for this week
                                                bg_color = "#fff9c4"
                                                recency_label = "🟡 This Week"
                                            else:
                                                border_color = "#90CAF9"  # Blue for older
                                                bg_color = "#e3f2fd"
                                                recency_label = "🔵 Older"
                                        except Exception:
                                            # Default if datetime comparison fails
                                            border_color = "#BDBDBD"
                                            bg_color = "#F5F5F5"
                                            recency_label = "⚪ Unknown"
                                    else:
                                        border_color = "#BDBDBD"
                                        bg_color = "#F5F5F5"
                                        recency_label = "⚪ Unknown"
                                    
                                    # Use Streamlit native components for readable text
                                    title = article.get('title', 'No title')
                                    publisher = article.get('publisher', 'Unknown')
                                    summary = article.get('summary', 'No summary available')
                                    link = article.get('link', '#')
                                    published_date = article['published'].strftime('%Y-%m-%d %H:%M') if article.get('published') else None
                                    
                                    # Display article using Streamlit expander for better UX
                                    with st.expander(f"{recency_label} 📄 {title}", expanded=(idx == 1)):
                                        # Publisher and date info
                                        col_info1, col_info2 = st.columns([2, 1])
                                        with col_info1:
                                            st.write(f"**Publisher:** {publisher}{time_ago}")
                                        with col_info2:
                                            if published_date:
                                                st.write(f"**Published:** {published_date}")
                                            else:
                                                st.write("**Published:** Unknown date")
                                        
                                        # Summary
                                        st.write("**Summary:**")
                                        st.write(summary)
                                        
                                        # Link to full article
                                        if link and link != '#':
                                            st.markdown(f"[🔗 Read Full Article →]({link})")
                                        
                                        # Add visual separator with recency indicator
                                        st.markdown(f"<div style='height: 2px; background: linear-gradient(to right, {border_color}, transparent); margin: 10px 0;'></div>", unsafe_allow_html=True)
                                    
                                    # Add separator between articles (except last one)
                                    if idx < len(news_articles):
                                        st.markdown("---")
                            elif news_articles is not None and len(news_articles) == 0:
                                st.warning(f"⚠️ No news articles found for {ticker}.")
                                st.info("💡 This may be due to limited news coverage for this stock.")
                            else:
                                st.warning(f"⚠️ Unable to fetch news for {ticker}.")
                                st.info("💡 News data may not be available for this stock.")
                    except Exception as e:
                        st.error(f"Error fetching news: {str(e)}")
                        st.info("💡 News data may be temporarily unavailable. Please try again later.")
        
        # Export options
        st.markdown("---")
        st.subheader("💾 Export Results")
        
        col1, col2 = st.columns(2)
        with col1:
            csv = summary_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV Summary",
                data=csv,
                file_name=f"stock_comparison_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.warning("⚠️ No valid stock data retrieved. Please check ticker symbols and try again.")

render_footer()

