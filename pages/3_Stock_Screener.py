"""
Stock Screener Page
Filter stocks based on custom criteria with detailed analysis
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from utils.stock_analyzer import StockAnalyzer
from utils.visualizations import (
    create_score_breakdown_table, create_price_chart, 
    create_volume_chart, create_financial_metrics_chart,
    create_trading_signals_chart
)
from utils.risk_analysis import RiskAnalyzer
from utils.valuation import StockValuation
from utils.ratings_aggregator import RatingsAggregator
from utils.peer_benchmark import PeerBenchmark
from utils.news_market import NewsMarketData
from utils.metric_display import display_enhanced_metric
from utils.portfolio_analyzer import PortfolioAnalyzer
from components.styling import apply_platform_theme, render_header, render_footer
from components.navigation import render_navigation

# Page configuration
st.set_page_config(
    page_title="Stock Screener",
    page_icon="🔍",
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
if 'portfolio_analyzer' not in st.session_state:
    st.session_state.portfolio_analyzer = PortfolioAnalyzer()
if 'news_market' not in st.session_state:
    st.session_state.news_market = NewsMarketData()

analyzer = st.session_state.analyzer
risk_analyzer = st.session_state.risk_analyzer
valuation = st.session_state.valuation
ratings_agg = st.session_state.ratings_aggregator
peer_bench = st.session_state.peer_benchmark
portfolio_analyzer = st.session_state.portfolio_analyzer
news_market = st.session_state.news_market

# Get settings
show_technical = st.session_state.get('show_technical', True)
time_period = st.session_state.get('time_period', '1y')

# Header
render_header("🔍 Advanced Stock Screener & Portfolio Analyzer", "Filter stocks and analyze your portfolio")

# Tabs for Screener and Portfolio Analysis
tab_screener, tab_portfolio = st.tabs(["🔍 Stock Screener", "💼 Portfolio Analyzer"])

with tab_screener:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("💰 Valuation Filters")
        pe_min = st.number_input("Min P/E Ratio", value=0.0, step=1.0)
        pe_max = st.number_input("Max P/E Ratio", value=100.0, step=1.0)
        
        market_cap_min = st.selectbox(
            "Min Market Cap",
            ["Any", "1M", "10M", "100M", "1B", "10B", "100B"]
        )

    with col2:
        st.subheader("📊 Profitability Filters")
        margin_min = st.slider("Min Gross Margin %", 0, 100, 20)
        roe_min = st.slider("Min ROE %", 0, 100, 10)

    with col3:
        st.subheader("📈 Growth Filters")
        revenue_growth_min = st.slider("Min Revenue Growth %", -50, 100, 0)

    st.markdown("---")

    # Stock universe input
    stock_universe = st.text_area(
        "Enter stocks to screen (comma-separated):",
        value="AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA, META, AMD, NFLX, PYPL",
        height=100
    )

    screen_btn = st.button("🔍 Run Screener", type="primary")

    if screen_btn and stock_universe:
        tickers = [t.strip().upper() for t in stock_universe.split(',')]
        
        passed_stocks_analysis = {}
        failed_tickers = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, ticker in enumerate(tickers):
            status_text.text(f"Screening {ticker}...")
            data = analyzer.get_stock_data(ticker, period="1y")
            
            if data and data.get('history') is not None and len(data.get('history', [])) > 0:
                metrics = analyzer.get_key_metrics(data)
                
                # Apply filters
                passes = True
                
                if metrics['P/E Ratio'] < pe_min or metrics['P/E Ratio'] > pe_max:
                    passes = False
                
                if metrics['Gross Margin'] < margin_min:
                    passes = False
                
                if metrics['ROE'] < roe_min:
                    passes = False
                
                if metrics['Revenue Growth'] < revenue_growth_min:
                    passes = False
                
                if passes:
                    # Calculate full analysis
                    score = analyzer.calculate_score(data)
                    
                    if show_technical and len(data['history']) >= 20:
                        data['history'] = analyzer.calculate_technical_indicators(data['history'])
                    
                    forecast = analyzer.calculate_forecast(data, metrics, score)
                    
                    passed_stocks_analysis[ticker] = {
                        'data': data,
                        'metrics': metrics,
                        'score': score,
                        'forecast': forecast
                    }
            else:
                failed_tickers.append(ticker)
            
            progress_bar.progress((i + 1) / len(tickers))
            # Small delay to avoid rate limiting
            import time
            time.sleep(0.5)
        
        status_text.empty()
        progress_bar.empty()
        
        # Show failed tickers if any
        if failed_tickers:
            st.warning(f"⚠️ Could not fetch data for: {', '.join(failed_tickers)}")
            st.info("💡 **Troubleshooting tips:**\n"
                   "- Verify ticker symbols are correct (e.g., AAPL not APPL)\n"
                   "- Some stocks may have limited data availability\n"
                   "- Try again in a few moments (Yahoo Finance may be rate limiting)\n"
                   "- Check that stocks are listed on major exchanges")
        
        if passed_stocks_analysis:
            st.success(f"✅ Found {len(passed_stocks_analysis)} stocks matching criteria")
            
            # Sort by score
            sorted_tickers = sorted(passed_stocks_analysis.keys(), 
                               key=lambda t: passed_stocks_analysis[t]['score']['total_score'], 
                               reverse=True)
            
            # Summary table
            st.subheader("📊 Screening Results Summary")
            summary_data = []
            for ticker in sorted_tickers:
                info = passed_stocks_analysis[ticker]
                summary_data.append({
                    'Ticker': ticker,
                'Company': info['data']['info'].get('longName', ticker)[:30],
                'Score': info['score']['total_score'],
                'Price': info['metrics']['Current Price'],
                'Forecast': info['forecast']['forecast_price'] if info['forecast'] else None,
                'Change %': info['forecast']['forecast_change_pct'] if info['forecast'] else None,
                'Probability': info['forecast']['probability'] if info['forecast'] else None,
                'P/E Ratio': info['metrics']['P/E Ratio'],
                'Gross Margin': info['metrics']['Gross Margin'],
                'ROE': info['metrics']['ROE'],
                })
            
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(
                summary_df.style.background_gradient(subset=['Score'], cmap='RdYlGn', vmin=0, vmax=100)
                .format({
                    'Price': '${:.2f}',
                'Forecast': '${:.2f}' if 'Forecast' in summary_df.columns else None,
                'Change %': '{:+.2f}%' if 'Change %' in summary_df.columns else None,
                'Probability': '{:.1f}%' if 'Probability' in summary_df.columns else None,
                'P/E Ratio': '{:.2f}',
                'Gross Margin': '{:.2f}%',
                'ROE': '{:.2f}%',
            }),
                use_container_width=True,
                hide_index=True
            )
            
            st.markdown("---")
            st.subheader("📈 Detailed Analysis for Screened Stocks")
            
            # Display detailed analysis for each stock (same style as Single Analysis)
            for ticker in sorted_tickers:
                info = passed_stocks_analysis[ticker]
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
                                        st.markdown("📚 **No active BUY signals.** 💡 Wait for better entry opportunities.", unsafe_allow_html=True)
                                
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
                                        st.markdown("📚 **No active SELL signals.** 💡 Stock not showing overvaluation.", unsafe_allow_html=True)
                                
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
                                        st.markdown("📚 **Calculate entry signals first.** 💡 Stop loss is essential for risk management.", unsafe_allow_html=True)
                                
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
                                        st.markdown("📚 **Calculate entry signals first.** 💡 Setting profit targets helps lock in gains.", unsafe_allow_html=True)
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
                                    st.info("💡 News data may not be available for this stock. This could be due to:\n"
                                          "- Limited coverage from news sources\n"
                                          "- Newly listed stock\n"
                                          "- Data source limitations")
                        except Exception as e:
                            st.error(f"Error fetching news: {str(e)}")
                            st.info("💡 News data may be temporarily unavailable. Please try again later.")
        
            # Export options
            st.markdown("---")
            st.subheader("💾 Export Results")
            
            csv = summary_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Screener Results",
                data=csv,
                file_name=f"screener_results_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="download_screener_results"
            )
        else:
            st.warning("⚠️ No stocks matched the specified criteria")

with tab_portfolio:
    st.markdown("### 💼 Portfolio Analyzer")
    st.write("Analyze your stock portfolio with comprehensive metrics, allocation, and performance tracking")
    
    st.markdown("---")
    
    # Portfolio input methods
    st.subheader("📝 Enter Your Portfolio Holdings")
    
    # File upload option
    uploaded_file = st.file_uploader(
        "📤 Upload Portfolio File (CSV/Excel)",
        type=['csv', 'xlsx', 'xls', 'txt'],
        help="Upload your IBKR portfolio export or any CSV file with Symbol/Ticker and Quantity/Shares columns"
    )
    
    # Text input option
    st.markdown("**OR paste your portfolio directly:**")
    st.markdown("**Supported formats:**")
    st.markdown("- **IBKR CSV:** Paste directly from IBKR (Symbol, Quantity columns)")
    st.markdown("- **Simple format:** `TICKER:SHARES` or `TICKER SHARES` (comma-separated)")
    st.markdown("- **Example:** `AAPL:10, MSFT:5, GOOGL:3` or `AAPL 10, MSFT 5, GOOGL 3`")
    
    portfolio_input = st.text_area(
        "Portfolio Holdings:",
        value="",
        height=150,
        key="portfolio_input",
        placeholder="Paste your IBKR portfolio here, or use format: AAPL:10, MSFT:5, GOOGL:3"
    )
    
    # Process uploaded file if provided
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                portfolio_input = uploaded_file.read().decode('utf-8')
                st.success(f"✅ File '{uploaded_file.name}' loaded successfully!")
            elif uploaded_file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(uploaded_file)
                portfolio_input = df.to_csv(index=False)
                st.success(f"✅ Excel file '{uploaded_file.name}' loaded successfully!")
            else:
                portfolio_input = uploaded_file.read().decode('utf-8')
                st.success(f"✅ File '{uploaded_file.name}' loaded successfully!")
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")
            portfolio_input = ""
    
    analyze_portfolio_btn = st.button("📊 Analyze Portfolio", type="primary", key="analyze_portfolio")
    
    if analyze_portfolio_btn and portfolio_input:
        with st.spinner("Analyzing portfolio..."):
            # Parse portfolio
            holdings = portfolio_analyzer.parse_portfolio_input(portfolio_input)
            
            if not holdings:
                st.error("❌ Could not parse portfolio. Please check the format.")
                
                # Show debug info
                with st.expander("🔍 Debug: Show parsed CSV structure", expanded=False):
                    try:
                        import io
                        lines = portfolio_input.strip().split('\n')[:10]  # First 10 lines
                        st.code('\n'.join(lines), language='text')
                        st.caption("First 10 lines of your input")
                    except:
                        pass
                
                st.info("""
                **Tips for IBKR exports:**
                - Make sure your CSV has 'Symbol' or 'Ticker' column
                - Make sure it has 'Quantity', 'Qty', or 'Shares' column
                - You can paste the entire CSV content directly
                - The parser looks for columns containing: Symbol, Ticker, Instrument, Quantity, Qty, Shares, Position, Units
                
                **Alternative formats:**
                - `AAPL:10, MSFT:5, GOOGL:3`
                - `AAPL 10, MSFT 5, GOOGL 3`
                - One ticker per line: `AAPL 10\\nMSFT 5\\nGOOGL 3`
                """)
            else:
                st.success(f"✅ Found {len(holdings)} holdings: {', '.join(sorted(holdings.keys()))}")
                
                # Show first few for verification
                if len(holdings) > 0:
                    sample_holdings = dict(list(holdings.items())[:10])
                    with st.expander(f"🔍 Preview: First {min(10, len(holdings))} holdings found", expanded=False):
                        preview_data = [{"Ticker": k, "Shares": v} for k, v in sample_holdings.items()]
                        import pandas as pd
                        st.dataframe(pd.DataFrame(preview_data), use_container_width=True, hide_index=True)
                
                # Analyze each ticker individually (this is the main analysis)
                st.markdown("---")
                st.markdown("### 🔍 Analyzing Individual Holdings...")
                
                analysis_progress = st.progress(0)
                analysis_status = st.empty()
                
                ticker_analyses = {}
                portfolio_data = {}
                total_tickers = len(holdings)
                failed_tickers = []
                
                # Initialize the table placeholder - this will be updated incrementally
                st.markdown("---")
                st.markdown("### 📊 Portfolio Holdings Analysis & Recommendations")
                st.markdown("*Table updates as each ticker is analyzed*")
                
                # Recommendation Summary (compact, above table)
                rec_col1, rec_col2, rec_col3, rec_col4 = st.columns(4)
                summary_metrics = rec_col1.empty(), rec_col2.empty(), rec_col3.empty(), rec_col4.empty()
                
                # Create table placeholder that will be updated
                table_placeholder = st.empty()
                legend_placeholder = st.empty()
                
                summary_df = None  # Initialize for use in export section
                
                for idx, (ticker, shares) in enumerate(holdings.items()):
                    analysis_status.text(f"Analyzing {ticker}... ({idx+1}/{total_tickers})")
                    
                    try:
                        # Get portfolio data (for portfolio-level metrics)
                        portfolio_data_single = portfolio_analyzer.get_portfolio_data({ticker: shares})
                        if portfolio_data_single and ticker in portfolio_data_single:
                            portfolio_data.update(portfolio_data_single)
                        
                        # Get full stock data for analysis
                        stock_data = analyzer.get_stock_data(ticker, period="1y")
                        if stock_data:
                            # Calculate metrics and score
                            metrics = analyzer.get_key_metrics(stock_data)
                            score = analyzer.calculate_score(stock_data)
                            
                            # Get current price and market value
                            current_price = stock_data['info'].get('currentPrice', stock_data['info'].get('regularMarketPrice', 0))
                            if not current_price or current_price == 0:
                                current_price = stock_data['info'].get('previousClose', 0)
                            market_value = shares * current_price if current_price > 0 else 0
                            
                            # Get valuation
                            valuation_result = None
                            try:
                                valuation_result = valuation.comprehensive_valuation(ticker, stock_data['info'], metrics)
                            except:
                                pass
                            
                            # Get ratings
                            ratings_result = None
                            try:
                                ratings_result = ratings_agg.aggregate_ratings(ticker, score, stock_data['info'])
                            except:
                                pass
                            
                            # Determine recommendation
                            recommendation = "HOLD"
                            recommendation_reason = ""
                            
                            if score and score.get('total_score', 0) >= 70:
                                if valuation_result and valuation_result.get('discount_premium', 0) > 10:
                                    recommendation = "STRONG BUY"
                                    recommendation_reason = f"High score ({score['total_score']}/100) + Undervalued ({valuation_result['discount_premium']:.1f}%)"
                                else:
                                    recommendation = "BUY"
                                    recommendation_reason = f"Strong fundamentals (Score: {score['total_score']}/100)"
                            elif score and score.get('total_score', 0) >= 50:
                                if valuation_result and valuation_result.get('discount_premium', 0) < -20:
                                    recommendation = "SELL"
                                    recommendation_reason = f"Moderate score ({score['total_score']}/100) + Overvalued ({abs(valuation_result['discount_premium']):.1f}%)"
                                else:
                                    recommendation = "HOLD"
                                    recommendation_reason = f"Moderate fundamentals (Score: {score['total_score']}/100)"
                            else:
                                recommendation = "SELL"
                                recommendation_reason = f"Weak fundamentals (Score: {score['total_score']}/100)"
                            
                            # Store analysis
                            ticker_analyses[ticker] = {
                                'ticker': ticker,
                                'shares': shares,
                                'current_price': current_price,
                                'market_value': market_value,
                                'score': score,
                                'metrics': metrics,
                                'valuation': valuation_result,
                                'ratings': ratings_result,
                                'recommendation': recommendation,
                                'recommendation_reason': recommendation_reason,
                                'data': stock_data
                            }
                            
                            # Update the table immediately with this new ticker
                            if ticker_analyses:
                                # Rebuild the table with all analyzed tickers so far
                                summary_data = []
                                total_portfolio_value = sum(a['market_value'] for a in ticker_analyses.values())
                                
                                for t, analysis in ticker_analyses.items():
                                    score_val = analysis['score']['total_score'] if analysis['score'] else 0
                                    weight = (analysis['market_value'] / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
                                    
                                    # Get valuation status and discount
                                    valuation_status = "N/A"
                                    discount_premium = 0
                                    if analysis['valuation']:
                                        discount_premium = analysis['valuation'].get('discount_premium', 0)
                                        if discount_premium > 10:
                                            valuation_status = f"Undervalued {discount_premium:.1f}%"
                                        elif discount_premium < -10:
                                            valuation_status = f"Overvalued {abs(discount_premium):.1f}%"
                                        else:
                                            valuation_status = "Fair Value"
                                    
                                    # Get analyst rating
                                    analyst_rating = "N/A"
                                    if analysis['ratings']:
                                        analyst_rating = analysis['ratings'].get('composite_rating', 'N/A')
                                    
                                    # Get key metrics
                                    metrics_data = analysis.get('metrics', {})
                                    pe_ratio = metrics_data.get('P/E Ratio', 0) if metrics_data else 0
                                    forward_pe = metrics_data.get('Forward P/E', 0) if metrics_data else 0
                                    roe = metrics_data.get('ROE', 0) if metrics_data else 0
                                    roa = metrics_data.get('ROA', 0) if metrics_data else 0
                                    gross_margin = metrics_data.get('Gross Margin', 0) if metrics_data else 0
                                    revenue_growth = metrics_data.get('Revenue Growth', 0) if metrics_data else 0
                                    debt_equity = metrics_data.get('Debt to Equity', 0) if metrics_data else 0
                                    beta = metrics_data.get('Beta', 0) if metrics_data else 0
                                    profit_margin = metrics_data.get('Profit Margin', 0) if metrics_data else 0
                                    
                                    # Calculate price target and upside/downside potential
                                    price_target = "N/A"
                                    upside_potential = 0
                                    if analysis['valuation']:
                                        fair_value = analysis['valuation'].get('fair_value', 0)
                                        if fair_value and fair_value > 0:
                                            price_target = f"${fair_value:.2f}"
                                            upside_potential = ((fair_value - analysis['current_price']) / analysis['current_price']) * 100
                                    
                                    # Calculate position impact (value contribution)
                                    position_value = analysis['market_value']
                                    position_impact = f"${position_value:,.0f} ({weight:.1f}%)"
                                    
                                    # Calculate expected return (based on score and valuation)
                                    expected_return = 0
                                    if score_val >= 70 and discount_premium > 5:
                                        expected_return = 15 + min(discount_premium * 0.5, 10)  # High score + undervalued
                                    elif score_val >= 70:
                                        expected_return = 10 + min(discount_premium * 0.3, 5)
                                    elif score_val >= 50 and discount_premium > 5:
                                        expected_return = 5 + min(discount_premium * 0.4, 5)
                                    elif score_val >= 50:
                                        expected_return = 2
                                    elif discount_premium < -10:
                                        expected_return = -5  # Overvalued penalty
                                    else:
                                        expected_return = -2  # Poor score
                                    
                                    # Risk assessment (based on beta, debt, volatility)
                                    risk_score = "Low"
                                    risk_color = "🟢"
                                    if beta > 1.5 or debt_equity > 2:
                                        risk_score = "High"
                                        risk_color = "🔴"
                                    elif beta > 1.2 or debt_equity > 1:
                                        risk_score = "Medium"
                                        risk_color = "🟡"
                                    
                                    # Quality score (composite of profitability, growth, financial strength)
                                    quality_score = 0
                                    if roe > 0:
                                        quality_score += min(roe / 20, 3)  # Max 3 points for ROE
                                    if gross_margin > 0:
                                        quality_score += min(gross_margin / 20, 2)  # Max 2 points for margins
                                    if revenue_growth > 0:
                                        quality_score += min(revenue_growth / 30, 2)  # Max 2 points for growth
                                    if debt_equity > 0 and debt_equity < 1:
                                        quality_score += 1  # Low debt bonus
                                    elif debt_equity >= 1:
                                        quality_score -= 1  # High debt penalty
                                    
                                    quality_rating = "Excellent" if quality_score >= 6 else "Good" if quality_score >= 4 else "Fair" if quality_score >= 2 else "Poor"
                                    
                                    # Get concise recommendation reason (focus on key drivers)
                                    recommendation_reason_text = analysis.get('recommendation_reason', '')
                                    # Extract key points from reason
                                    concise_reason = recommendation_reason_text
                                    if len(recommendation_reason_text) > 80:
                                        # Try to extract first key sentence
                                        sentences = recommendation_reason_text.split('.')
                                        if len(sentences) > 1:
                                            concise_reason = sentences[0] + '.'
                                        else:
                                            concise_reason = recommendation_reason_text[:77] + '...'
                                    
                                    # Action item (what to do)
                                    action_item = ""
                                    if analysis['recommendation'] in ['STRONG BUY', 'BUY']:
                                        if weight < 5:
                                            action_item = f"🔼 Increase to {max(weight * 1.5, 5):.1f}%"
                                        elif weight > 15:
                                            action_item = "⚠️ Over-concentrated"
                                        else:
                                            action_item = "✅ Optimal weight"
                                    elif analysis['recommendation'] == 'HOLD':
                                        action_item = "📊 Monitor closely"
                                    else:  # SELL
                                        action_item = "🔽 Reduce position"
                                    
                                    # Get sector and industry
                                    sector = "N/A"
                                    industry = "N/A"
                                    company_name = t
                                    if t in portfolio_data:
                                        info = portfolio_data[t]['info']
                                        sector = info.get('sector', 'N/A')
                                        industry = info.get('industry', 'N/A')
                                        company_name = info.get('shortName', info.get('longName', t))
                                        if industry and len(industry) > 25:
                                            industry = industry[:25] + '...'
                                        if company_name and len(company_name) > 20:
                                            company_name = company_name[:20] + '...'
                                    
                                    summary_data.append({
                                        'Ticker': t,
                                        'Company': company_name,
                                        'Action': action_item,
                                        'Recommendation': analysis['recommendation'],
                                        'Score': score_val,
                                        'Quality': quality_rating,
                                        'Risk': f"{risk_color} {risk_score}",
                                        'Price': f"${analysis['current_price']:.2f}",
                                        'Target': price_target,
                                        'Upside %': f"{upside_potential:+.1f}%" if upside_potential != 0 else "N/A",
                                        'Position': position_impact,
                                        'Value': f"${position_value:,.0f}",
                                        'Weight %': f"{weight:.1f}%",
                                        'Expected Return %': f"{expected_return:+.1f}%",
                                        'Valuation Gap %': f"{discount_premium:+.1f}%" if analysis['valuation'] else "N/A",
                                        'P/E': f"{pe_ratio:.1f}" if pe_ratio > 0 else "N/A",
                                        'ROE %': f"{roe:.1f}%" if roe != 0 else "N/A",
                                        'Revenue Growth %': f"{revenue_growth:+.1f}%" if revenue_growth != 0 else "N/A",
                                        'Beta': f"{beta:.2f}" if beta != 0 else "N/A",
                                        'Analyst Rating': analyst_rating,
                                        'Sector': sector,
                                        'Key Reason': concise_reason
                                    })
                                
                                summary_df = pd.DataFrame(summary_data)
                                
                                # Sort by recommendation priority and then by expected return
                                recommendation_order = {'STRONG BUY': 0, 'BUY': 1, 'HOLD': 2, 'SELL': 3}
                                summary_df['_sort_order'] = summary_df['Recommendation'].map(recommendation_order)
                                # Extract numeric expected return for sorting
                                summary_df['_expected_return_num'] = summary_df['Expected Return %'].replace('N/A', '0').str.replace('%', '').str.replace('+', '').astype(float)
                                summary_df = summary_df.sort_values(['_sort_order', '_expected_return_num'], ascending=[True, False]).drop(['_sort_order', '_expected_return_num'], axis=1)
                                
                                # Update summary metrics
                                rec_counts = {}
                                for a in ticker_analyses.values():
                                    rec = a['recommendation']
                                    rec_counts[rec] = rec_counts.get(rec, 0) + 1
                                
                                total_positions = len(ticker_analyses) if len(ticker_analyses) > 0 else 1
                                buy_count = rec_counts.get('BUY', 0) + rec_counts.get('STRONG BUY', 0)
                                hold_count = rec_counts.get('HOLD', 0)
                                sell_count = rec_counts.get('SELL', 0)
                                scores = [a['score']['total_score'] for a in ticker_analyses.values() if a.get('score')]
                                avg_score = sum(scores) / len(scores) if scores else 0
                                
                                summary_metrics[0].metric("🟢 Buy", buy_count, delta=f"{buy_count/total_positions*100:.1f}%")
                                summary_metrics[1].metric("🟡 Hold", hold_count, delta=f"{hold_count/total_positions*100:.1f}%")
                                summary_metrics[2].metric("🔴 Sell", sell_count, delta=f"{sell_count/total_positions*100:.1f}%")
                                summary_metrics[3].metric("📊 Avg Score", f"{avg_score:.1f}/100")
                                
                                # Color coding functions
                                def color_recommendation(val):
                                    if val == 'STRONG BUY':
                                        return 'background-color: #2E7D32; color: white; font-weight: bold; text-align: center'
                                    elif val == 'BUY':
                                        return 'background-color: #4CAF50; color: white; font-weight: bold; text-align: center'
                                    elif val == 'HOLD':
                                        return 'background-color: #FFA726; color: white; font-weight: bold; text-align: center'
                                    elif val == 'SELL':
                                        return 'background-color: #EF5350; color: white; font-weight: bold; text-align: center'
                                    return ''
                                
                                def color_score(val):
                                    try:
                                        score = float(val)
                                        if score >= 70:
                                            return 'background-color: #C8E6C9; color: #1B5E20; font-weight: bold'
                                        elif score >= 50:
                                            return 'background-color: #FFF9C4; color: #F57F17; font-weight: bold'
                                        else:
                                            return 'background-color: #FFCDD2; color: #B71C1C; font-weight: bold'
                                    except:
                                        return ''
                                
                                def color_expected_return(val):
                                    try:
                                        if val == "N/A":
                                            return ''
                                        ret = float(val.replace('%', '').replace('+', ''))
                                        if ret >= 10:
                                            return 'background-color: #C8E6C9; color: #1B5E20; font-weight: bold'
                                        elif ret >= 5:
                                            return 'background-color: #FFF9C4; color: #F57F17; font-weight: bold'
                                        elif ret < 0:
                                            return 'background-color: #FFCDD2; color: #B71C1C; font-weight: bold'
                                        else:
                                            return ''
                                    except:
                                        return ''
                                
                                def color_valuation_gap(val):
                                    try:
                                        if val == "N/A":
                                            return ''
                                        gap = float(val.replace('%', '').replace('+', ''))
                                        if gap > 10:
                                            return 'background-color: #C8E6C9; color: #1B5E20; font-weight: bold'
                                        elif gap < -10:
                                            return 'background-color: #FFCDD2; color: #B71C1C; font-weight: bold'
                                        else:
                                            return 'background-color: #FFF9C4; color: #F57F17'
                                    except:
                                        return ''
                                
                                def color_upside(val):
                                    try:
                                        if val == "N/A":
                                            return ''
                                        upside = float(val.replace('%', '').replace('+', ''))
                                        if upside > 20:
                                            return 'background-color: #C8E6C9; color: #1B5E20; font-weight: bold'
                                        elif upside > 10:
                                            return 'background-color: #FFF9C4; color: #F57F17; font-weight: bold'
                                        elif upside < -10:
                                            return 'background-color: #FFCDD2; color: #B71C1C; font-weight: bold'
                                        else:
                                            return ''
                                    except:
                                        return ''
                                
                                # Apply styling and update table
                                styled_df = (summary_df.style
                                            .applymap(color_recommendation, subset=['Recommendation'])
                                            .applymap(color_score, subset=['Score'])
                                            .applymap(color_expected_return, subset=['Expected Return %'])
                                            .applymap(color_upside, subset=['Upside %'])
                                            .applymap(color_valuation_gap, subset=['Valuation Gap %']))
                                
                                table_placeholder.dataframe(styled_df, use_container_width=True, hide_index=True, height=600)
                                
                                # Update legend with enhanced information
                                legend_placeholder.markdown("""
                                <div style="margin-top: 10px; padding: 15px; background-color: #f5f5f5; border-radius: 8px; border-left: 4px solid #1976D2;">
                                <strong>📊 Portfolio Analysis Legend:</strong><br><br>
                                <strong>Recommendations:</strong><br>
                                <span style="background-color: #2E7D32; color: white; padding: 3px 10px; border-radius: 4px; margin-right: 8px; font-weight: bold;">STRONG BUY</span>
                                <span style="background-color: #4CAF50; color: white; padding: 3px 10px; border-radius: 4px; margin-right: 8px; font-weight: bold;">BUY</span>
                                <span style="background-color: #FFA726; color: white; padding: 3px 10px; border-radius: 4px; margin-right: 8px; font-weight: bold;">HOLD</span>
                                <span style="background-color: #EF5350; color: white; padding: 3px 10px; border-radius: 4px; margin-right: 8px; font-weight: bold;">SELL</span>
                                <br><br>
                                <strong>Metric Colors:</strong><br>
                                • <strong>Score:</strong> 🟢 Green (≥70) = Strong | 🟡 Yellow (50-69) = Moderate | 🔴 Red (<50) = Weak<br>
                                • <strong>Expected Return:</strong> 🟢 Green (≥10%) = High Return | 🟡 Yellow (5-10%) = Moderate | 🔴 Red (<0%) = Negative<br>
                                • <strong>Upside Potential:</strong> 🟢 Green (>20%) = High Upside | 🟡 Yellow (10-20%) = Moderate | 🔴 Red (<-10%) = Downside<br>
                                • <strong>Valuation Gap:</strong> 🟢 Green (>10%) = Undervalued | 🟡 Yellow (-10% to 10%) = Fair | 🔴 Red (<-10%) = Overvalued<br>
                                • <strong>Risk:</strong> 🟢 Low | 🟡 Medium | 🔴 High
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            failed_tickers.append(ticker)
                            st.warning(f"⚠️ Could not fetch data for {ticker}")
                    except Exception as e:
                        failed_tickers.append(ticker)
                        st.warning(f"⚠️ Could not analyze {ticker}: {str(e)}")
                    
                    analysis_progress.progress((idx + 1) / total_tickers)
                
                analysis_status.empty()
                analysis_progress.empty()
                
                if failed_tickers:
                    st.warning(f"⚠️ Could not analyze {len(failed_tickers)} ticker(s): {', '.join(failed_tickers)}")
                
                # Table is already displayed and updated incrementally, now show export options
                if ticker_analyses and summary_df is not None:
                    # Export recommendations
                    st.markdown("---")
                    st.markdown("### 💾 Export Recommendations")
                    
                    # Prepare export data
                    export_summary = summary_df.copy()
                    export_summary['Recommendation Reason'] = [ticker_analyses[t]['recommendation_reason'] for t in export_summary['Ticker']]
                    
                    csv_export = export_summary.to_csv(index=False)
                    # Use unique key based on number of tickers to avoid duplicates
                    unique_key = f"download_portfolio_recommendations_{len(ticker_analyses)}_{hash(tuple(sorted(ticker_analyses.keys())))}"
                    st.download_button(
                        label="📥 Download Recommendations (CSV)",
                        data=csv_export,
                        file_name=f"portfolio_recommendations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        key=unique_key
                    )
                
                # Calculate portfolio-level metrics (only if we have ticker analyses)
                portfolio_metrics = None
                performance = None
                risk_metrics = None
                
                if ticker_analyses:
                    portfolio_metrics = portfolio_analyzer.calculate_portfolio_metrics(portfolio_data)
                    performance = portfolio_analyzer.calculate_portfolio_performance(portfolio_data)
                    risk_metrics = portfolio_analyzer.get_portfolio_risk_metrics(portfolio_data)
                
                if portfolio_metrics:
                    # Portfolio Summary
                    st.markdown("---")
                    st.markdown("### 📊 Portfolio-Level Summary")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Value", f"${portfolio_metrics['total_value']:,.2f}")
                    with col2:
                        st.metric("Number of Holdings", portfolio_metrics['num_holdings'])
                    with col3:
                        st.metric("Portfolio Beta", f"{portfolio_metrics['weighted_beta']:.2f}")
                    with col4:
                        st.metric("Concentration (HHI)", f"{portfolio_metrics['concentration_hhi']:.0f}")
                    
                    # Performance Metrics
                    if performance:
                        st.markdown("---")
                        st.markdown("### 📈 Portfolio Performance")
                        
                        perf_col1, perf_col2, perf_col3, perf_col4 = st.columns(4)
                        
                        with perf_col1:
                            delta_color = "normal" if performance['total_return'] >= 0 else "inverse"
                            st.metric("Total Return", f"{performance['total_return']:.2f}%", 
                                     delta=f"{performance['annualized_return']:.2f}% annualized",
                                     delta_color=delta_color)
                            st.caption("💡 Total return over the period with annualized equivalent")
                        
                        with perf_col2:
                            st.metric("Volatility", f"{performance['volatility']:.2f}%")
                            st.caption("💡 Annualized volatility - measures price fluctuation risk")
                        
                        with perf_col3:
                            st.metric("Sharpe Ratio", f"{performance['sharpe_ratio']:.2f}")
                            st.caption("💡 Risk-adjusted return. Over 1.0 is good, over 2.0 is excellent")
                        
                        with perf_col4:
                            st.metric("Max Drawdown", f"{performance['max_drawdown']:.2f}%")
                            st.caption("💡 Largest peak-to-trough decline - measures downside risk")
                        
                        # Performance Chart
                        if 'portfolio_series' in performance and len(performance['portfolio_series']) > 0:
                            st.markdown("---")
                            st.markdown("#### 📈 Portfolio Value Over Time")
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(
                                x=performance['portfolio_series'].index,
                                y=performance['portfolio_series'].values,
                                mode='lines',
                                name='Portfolio Value',
                                line=dict(color='#4CAF50', width=2)
                            ))
                            fig.update_layout(
                                title='Portfolio Value Over Time',
                                xaxis_title='Date',
                                yaxis_title='Portfolio Value ($)',
                                height=400,
                                template='plotly_dark',
                                plot_bgcolor='rgba(0,0,0,0)',
                                paper_bgcolor='rgba(0,0,0,0)'
                            )
                            st.plotly_chart(fig, use_container_width=True)
                    
                    # Sector Allocation
                    if portfolio_metrics['sector_allocation']:
                        st.markdown("---")
                        st.markdown("### 🏢 Sector Allocation")
                        
                        sector_data = []
                        for sector, value in portfolio_metrics['sector_allocation'].items():
                            pct = (value / portfolio_metrics['total_value']) * 100
                            sector_data.append({
                                'Sector': sector,
                                'Value': f"${value:,.2f}",
                                'Allocation %': f"{pct:.2f}%"
                            })
                        
                        sector_df = pd.DataFrame(sector_data)
                        sector_df['Allocation_Numeric'] = sector_df['Allocation %'].str.replace('%', '').astype(float)
                        sector_df_sorted = sector_df.sort_values('Allocation_Numeric', ascending=False).drop('Allocation_Numeric', axis=1)
                        
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.dataframe(sector_df_sorted, use_container_width=True, hide_index=True)
                        
                        with col2:
                            # Pie chart
                            sector_values = [float(v.replace('$', '').replace(',', '')) for v in sector_df_sorted['Value']]
                            fig_pie = px.pie(
                                sector_df_sorted,
                                values=sector_values,
                                names='Sector',
                                title='Sector Allocation',
                                color_discrete_sequence=px.colors.qualitative.Set3
                            )
                            fig_pie.update_layout(height=400, template='plotly_dark')
                            st.plotly_chart(fig_pie, use_container_width=True)
                    
                    # Portfolio Metrics
                    st.markdown("---")
                    st.markdown("### 📊 Portfolio Weighted Metrics")
                    st.markdown("*Metrics are weighted by position size*")
                    
                    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                    
                    with metrics_col1:
                        st.markdown("#### 💰 Valuation")
                        display_enhanced_metric("Weighted P/E", f"{portfolio_metrics['weighted_pe']:.2f}", 
                                               metric_name="P/E Ratio")
                        display_enhanced_metric("Weighted Forward P/E", f"{portfolio_metrics['weighted_forward_pe']:.2f}", 
                                               metric_name="Forward P/E")
                        display_enhanced_metric("Weighted PEG", f"{portfolio_metrics['weighted_peg']:.2f}", 
                                               metric_name="PEG Ratio")
                    
                    with metrics_col2:
                        st.markdown("#### 💵 Returns")
                        display_enhanced_metric("Weighted ROE", f"{portfolio_metrics['weighted_roe']:.2f}%", 
                                               metric_name="ROE")
                        display_enhanced_metric("Weighted ROA", f"{portfolio_metrics['weighted_roa']:.2f}%", 
                                               metric_name="ROA")
                        display_enhanced_metric("Weighted Dividend Yield", f"{portfolio_metrics['weighted_dividend_yield']:.2f}%", 
                                               metric_name="Dividend Yield")
                    
                    with metrics_col3:
                        st.markdown("#### 📈 Profitability")
                        display_enhanced_metric("Weighted Gross Margin", f"{portfolio_metrics['weighted_gross_margin']:.2f}%", 
                                               metric_name="Gross Margin")
                        display_enhanced_metric("Weighted Operating Margin", f"{portfolio_metrics['weighted_operating_margin']:.2f}%", 
                                               metric_name="Operating Margin")
                        display_enhanced_metric("Weighted Profit Margin", f"{portfolio_metrics['weighted_profit_margin']:.2f}%", 
                                               metric_name="Profit Margin")
                    
                    # Risk Analysis
                    if risk_metrics:
                        st.markdown("---")
                        st.markdown("### ⚠️ Portfolio Risk Analysis")
                        
                        risk_col1, risk_col2, risk_col3 = st.columns(3)
                        
                        with risk_col1:
                            st.markdown(f"**Portfolio Beta:** {risk_metrics['portfolio_beta']:.2f}")
                            st.caption("💡 Weighted average beta. 1.0 = market risk, <1.0 = less volatile, >1.0 = more volatile")
                        
                        with risk_col2:
                            st.markdown(f"**Number of Positions:** {risk_metrics['num_positions']}")
                            st.caption("💡 More positions = better diversification (generally)")
                        
                        with risk_col3:
                            st.markdown(f"**Largest Position:** {risk_metrics['largest_position_pct']:.2f}%")
                            st.caption("💡 Concentration risk. Over 25% in single position may indicate high concentration")
                        
                        # Concentration warning
                        if portfolio_metrics['concentration_hhi'] > 2500:
                            st.warning("⚠️ **High Concentration Risk**: HHI above 2500 indicates high portfolio concentration. Consider diversifying.")
                        elif portfolio_metrics['concentration_hhi'] > 1500:
                            st.info("ℹ️ **Moderate Concentration**: Consider adding more positions for better diversification.")
                        else:
                            st.success("✅ **Well Diversified**: Portfolio shows good diversification across holdings.")
                    
                    # Export option
                    st.markdown("---")
                    st.markdown("### 💾 Export Portfolio Analysis")
                    
                    import json
                    # Create holdings_data from summary_df or ticker_analyses for export
                    holdings_data = []
                    if summary_df is not None and len(summary_df) > 0:
                        # Use summary_df if available
                        for _, row in summary_df.iterrows():
                            holdings_data.append({
                                'Ticker': row['Ticker'],
                                'Shares': row['Shares'],
                                'Price': row['Price'],
                                'Value': row['Value'],
                                'Weight %': row['Weight %'],
                                'Sector': row.get('Sector', 'N/A'),
                                'Industry': row.get('Industry', 'N/A'),
                                'Recommendation': row['Recommendation'],
                                'Score': row['Score']
                            })
                    elif ticker_analyses:
                        # Fallback: create from ticker_analyses
                        total_portfolio_value = sum(a['market_value'] for a in ticker_analyses.values())
                        for ticker, analysis in ticker_analyses.items():
                            weight = (analysis['market_value'] / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
                            sector = "N/A"
                            industry = "N/A"
                            if ticker in portfolio_data:
                                sector = portfolio_data[ticker]['info'].get('sector', 'N/A')
                                industry = portfolio_data[ticker]['info'].get('industry', 'N/A')
                            holdings_data.append({
                                'Ticker': ticker,
                                'Shares': f"{analysis['shares']:.2f}",
                                'Price': f"${analysis['current_price']:.2f}",
                                'Value': f"${analysis['market_value']:,.2f}",
                                'Weight %': f"{weight:.2f}%",
                                'Sector': sector,
                                'Industry': industry,
                                'Recommendation': analysis['recommendation'],
                                'Score': analysis['score']['total_score'] if analysis.get('score') else 0
                            })
                    
                    export_data = {
                        'Holdings': holdings_data,
                        'Sector Allocation': sector_data if portfolio_metrics.get('sector_allocation') else [],
                        'Portfolio Metrics': {
                            'Total Value': portfolio_metrics['total_value'],
                            'Number of Holdings': portfolio_metrics['num_holdings'],
                            'Weighted P/E': portfolio_metrics['weighted_pe'],
                            'Weighted Beta': portfolio_metrics['weighted_beta']
                        }
                    }
                    
                    if performance:
                        export_data['Performance'] = {
                            'Total Return': performance['total_return'],
                            'Annualized Return': performance['annualized_return'],
                            'Volatility': performance['volatility'],
                            'Sharpe Ratio': performance['sharpe_ratio'],
                            'Max Drawdown': performance['max_drawdown']
                        }
                    
                    json_str = json.dumps(export_data, indent=2, default=str)
                    
                    # Use unique key based on portfolio data to avoid duplicates
                    portfolio_hash = hash(tuple(sorted(portfolio_data.keys()))) if portfolio_data else 0
                    unique_key_json = f"download_portfolio_analysis_json_{len(portfolio_data)}_{portfolio_hash}"
                    st.download_button(
                        label="📥 Download Portfolio Analysis (JSON)",
                        data=json_str,
                        file_name=f"portfolio_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        key=unique_key_json
                    )

render_footer()
