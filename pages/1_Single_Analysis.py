"""
Single Stock Analysis Page
Deep dive analysis for individual stocks
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from utils.stock_analyzer import StockAnalyzer
from utils.visualizations import (
    create_price_chart, create_volume_chart, 
    create_score_visualization, create_financial_metrics_chart,
    create_score_breakdown_table, create_trading_signals_chart
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
    page_title="Single Stock Analysis",
    page_icon="📊",
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
show_technical = st.session_state.get('show_technical', True)
show_fundamentals = st.session_state.get('show_fundamentals', True)

# Header
render_header("📊 Single Stock Analysis", "Comprehensive analysis for individual stocks")

# Input section
col1, col2 = st.columns([3, 1])
with col1:
    ticker = st.text_input("Enter Stock Ticker:", value="NVDA", key="single_ticker").upper()
with col2:
    analyze_btn = st.button("🔍 Analyze", type="primary", use_container_width=True)

if analyze_btn and ticker:
    with st.spinner(f"Analyzing {ticker}..."):
        data = analyzer.get_stock_data(ticker, period=time_period)
        
        if data and data.get('history') is not None and len(data.get('history', [])) > 0:
            # Calculate metrics and score
            metrics = analyzer.get_key_metrics(data)
            score = analyzer.calculate_score(data)
            
            # Calculate technical indicators
            if show_technical:
                data['history'] = analyzer.calculate_technical_indicators(data['history'])
            
            # Calculate forecast
            forecast = analyzer.calculate_forecast(data, metrics, score)
            
            # Calculate intrinsic value for fair value tunnel
            intrinsic_value = None
            try:
                valuation_result = valuation.comprehensive_valuation(ticker, data['info'], metrics)
                if valuation_result:
                    intrinsic_value = valuation_result['intrinsic_value']
            except:
                pass  # If valuation fails, continue without fair value tunnel
            
            # Display company info
            st.subheader(f"{data['info'].get('longName', ticker)} ({ticker})")
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
                # Price chart with professional trading features
                price_chart = create_price_chart(data, intrinsic_value=intrinsic_value, metrics=metrics)
                if price_chart:
                    st.plotly_chart(price_chart, use_container_width=True)
                    # Add legend explaining chart features
                    st.caption("💡 **Chart Features:** Fair Value Tunnel (blue shaded area), VWAP (purple), Support/Resistance (green/red), Pivot Points (gray/orange), Moving Averages, Bollinger Bands, Entry/Exit Signals")
                else:
                    st.warning("⚠️ Price chart data not available for this stock.")
                
                # Volume chart
                volume_chart = create_volume_chart(data.get('history'), ticker)
                if volume_chart:
                    st.plotly_chart(volume_chart, use_container_width=True)
                else:
                    st.warning("⚠️ Volume chart data not available for this stock.")
            
            with tab2:
                # Trading Signals Tab
                st.markdown("### 🎯 Professional Trading Signals")
                st.markdown("*Buy/Sell zones with entry/exit points, stop loss, and take profit targets*")
                
                # Create trading signals chart
                signals_result = create_trading_signals_chart(data, intrinsic_value=intrinsic_value, metrics=metrics, score=score)
                
                if signals_result:
                    signals_chart, trading_signals = signals_result
                    
                    # ===== PROMINENT VISUAL SIGNALS DASHBOARD =====
                    st.markdown("---")
                    st.markdown("## 📊 Trading Signals Dashboard")
                    st.markdown("### *Key trading levels at a glance*")
                    
                    # Get current price for calculations
                    current_price = metrics.get('Current Price', 0) if metrics else 0
                    
                    # Create 5-column layout for main signals
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    # 1. ENTRY SIGNAL (Green)
                    with col1:
                        if trading_signals.get('buy_signals'):
                            best_entry = min(trading_signals['buy_signals'], key=lambda x: x['price'])
                            entry_price = best_entry['price']
                            entry_type = best_entry['type']
                            entry_confidence = best_entry['confidence']
                            
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%); 
                                        padding: 25px; border-radius: 15px; text-align: center; 
                                        box-shadow: 0 4px 6px rgba(0,0,0,0.2); border: 3px solid #1B5E20;">
                                <h2 style="color: white; margin: 0 0 10px 0; font-size: 2.5em;">📈</h2>
                                <h3 style="color: white; margin: 0 0 5px 0; font-size: 1.1em; font-weight: bold;">ENTRY</h3>
                                <h1 style="color: white; margin: 10px 0; font-size: 2.2em; font-weight: bold;">${entry_price:.2f}</h1>
                                <p style="color: #C8E6C9; margin: 5px 0; font-size: 0.85em;">{entry_type}</p>
                                <p style="color: #A5D6A7; margin: 5px 0; font-size: 0.75em;">Confidence: {entry_confidence}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div style="background: #f5f5f5; padding: 25px; border-radius: 15px; text-align: center; 
                                        border: 2px dashed #ccc;">
                                <h2 style="color: #999; margin: 0 0 10px 0; font-size: 2.5em;">📈</h2>
                                <h3 style="color: #999; margin: 0; font-size: 1.1em;">ENTRY</h3>
                                <p style="color: #999; margin: 10px 0; font-size: 0.9em;">No signal</p>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # 2. EXIT SIGNAL (Red)
                    with col2:
                        if trading_signals.get('sell_signals'):
                            best_exit = max(trading_signals['sell_signals'], key=lambda x: x['price'])
                            exit_price = best_exit['price']
                            exit_type = best_exit['type']
                            exit_confidence = best_exit['confidence']
                            
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #EF5350 0%, #C62828 100%); 
                                        padding: 25px; border-radius: 15px; text-align: center; 
                                        box-shadow: 0 4px 6px rgba(0,0,0,0.2); border: 3px solid #B71C1C;">
                                <h2 style="color: white; margin: 0 0 10px 0; font-size: 2.5em;">📉</h2>
                                <h3 style="color: white; margin: 0 0 5px 0; font-size: 1.1em; font-weight: bold;">EXIT</h3>
                                <h1 style="color: white; margin: 10px 0; font-size: 2.2em; font-weight: bold;">${exit_price:.2f}</h1>
                                <p style="color: #FFCDD2; margin: 5px 0; font-size: 0.85em;">{exit_type}</p>
                                <p style="color: #EF9A9A; margin: 5px 0; font-size: 0.75em;">Confidence: {exit_confidence}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div style="background: #f5f5f5; padding: 25px; border-radius: 15px; text-align: center; 
                                        border: 2px dashed #ccc;">
                                <h2 style="color: #999; margin: 0 0 10px 0; font-size: 2.5em;">📉</h2>
                                <h3 style="color: #999; margin: 0; font-size: 1.1em;">EXIT</h3>
                                <p style="color: #999; margin: 10px 0; font-size: 0.9em;">No signal</p>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # 3. STOP LOSS (Orange/Red)
                    with col3:
                        if trading_signals.get('stop_loss'):
                            sl_price = trading_signals['stop_loss']['price']
                            if trading_signals.get('buy_signals'):
                                entry_price = min(s['price'] for s in trading_signals['buy_signals'])
                                risk_amount = entry_price - sl_price
                                risk_pct = (risk_amount / entry_price) * 100
                            else:
                                risk_amount = 0
                                risk_pct = 0
                            
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #FF9800 0%, #E65100 100%); 
                                        padding: 25px; border-radius: 15px; text-align: center; 
                                        box-shadow: 0 4px 6px rgba(0,0,0,0.2); border: 3px solid #BF360C;">
                                <h2 style="color: white; margin: 0 0 10px 0; font-size: 2.5em;">🛡️</h2>
                                <h3 style="color: white; margin: 0 0 5px 0; font-size: 1.1em; font-weight: bold;">STOP LOSS</h3>
                                <h1 style="color: white; margin: 10px 0; font-size: 2.2em; font-weight: bold;">${sl_price:.2f}</h1>
                                <p style="color: #FFE0B2; margin: 5px 0; font-size: 0.85em;">Risk: ${risk_amount:.2f}</p>
                                <p style="color: #FFCC80; margin: 5px 0; font-size: 0.75em;">({risk_pct:.1f}% below entry)</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div style="background: #f5f5f5; padding: 25px; border-radius: 15px; text-align: center; 
                                        border: 2px dashed #ccc;">
                                <h2 style="color: #999; margin: 0 0 10px 0; font-size: 2.5em;">🛡️</h2>
                                <h3 style="color: #999; margin: 0; font-size: 1.1em;">STOP LOSS</h3>
                                <p style="color: #999; margin: 10px 0; font-size: 0.9em;">Calculate entry first</p>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # 4. BUY SIGNAL (Bright Green)
                    with col4:
                        if trading_signals.get('buy_signals'):
                            buy_count = len(trading_signals['buy_signals'])
                            avg_buy = sum(s['price'] for s in trading_signals['buy_signals']) / buy_count
                            
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #66BB6A 0%, #388E3C 100%); 
                                        padding: 25px; border-radius: 15px; text-align: center; 
                                        box-shadow: 0 4px 6px rgba(0,0,0,0.2); border: 3px solid #2E7D32;">
                                <h2 style="color: white; margin: 0 0 10px 0; font-size: 2.5em;">🟢</h2>
                                <h3 style="color: white; margin: 0 0 5px 0; font-size: 1.1em; font-weight: bold;">BUY</h3>
                                <h1 style="color: white; margin: 10px 0; font-size: 2.2em; font-weight: bold;">${avg_buy:.2f}</h1>
                                <p style="color: #C8E6C9; margin: 5px 0; font-size: 0.85em;">{buy_count} signal(s)</p>
                                <p style="color: #A5D6A7; margin: 5px 0; font-size: 0.75em;">Avg price</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div style="background: #f5f5f5; padding: 25px; border-radius: 15px; text-align: center; 
                                        border: 2px dashed #ccc;">
                                <h2 style="color: #999; margin: 0 0 10px 0; font-size: 2.5em;">🟢</h2>
                                <h3 style="color: #999; margin: 0; font-size: 1.1em;">BUY</h3>
                                <p style="color: #999; margin: 10px 0; font-size: 0.9em;">No signals</p>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # 5. TAKE PROFIT (Gold/Orange)
                    with col5:
                        if trading_signals.get('take_profit'):
                            best_tp = max(trading_signals['take_profit'], key=lambda x: x['price'])
                            tp_price = best_tp['price']
                            tp_count = len(trading_signals['take_profit'])
                            
                            if trading_signals.get('buy_signals'):
                                entry_price = min(s['price'] for s in trading_signals['buy_signals'])
                                profit_amount = tp_price - entry_price
                                profit_pct = (profit_amount / entry_price) * 100
                            else:
                                profit_amount = 0
                                profit_pct = 0
                            
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #FFB74D 0%, #F57C00 100%); 
                                        padding: 25px; border-radius: 15px; text-align: center; 
                                        box-shadow: 0 4px 6px rgba(0,0,0,0.2); border: 3px solid #E65100;">
                                <h2 style="color: white; margin: 0 0 10px 0; font-size: 2.5em;">🎯</h2>
                                <h3 style="color: white; margin: 0 0 5px 0; font-size: 1.1em; font-weight: bold;">TAKE PROFIT</h3>
                                <h1 style="color: white; margin: 10px 0; font-size: 2.2em; font-weight: bold;">${tp_price:.2f}</h1>
                                <p style="color: #FFE0B2; margin: 5px 0; font-size: 0.85em;">+{profit_pct:.1f}% gain</p>
                                <p style="color: #FFCC80; margin: 5px 0; font-size: 0.75em;">{tp_count} target(s)</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div style="background: #f5f5f5; padding: 25px; border-radius: 15px; text-align: center; 
                                        border: 2px dashed #ccc;">
                                <h2 style="color: #999; margin: 0 0 10px 0; font-size: 2.5em;">🎯</h2>
                                <h3 style="color: #999; margin: 0; font-size: 1.1em;">TAKE PROFIT</h3>
                                <p style="color: #999; margin: 10px 0; font-size: 0.9em;">Calculate entry first</p>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    st.markdown("## 📈 Trading Chart")
                    
                    if signals_chart:
                        st.plotly_chart(signals_chart, use_container_width=True)
                        
                        st.markdown("---")
                        
                        # Display detailed signals breakdown
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### 🟢 BUY Signals - Educational Guide")
                            st.caption("💡 Hover over chart markers for detailed explanations")
                            
                            if trading_signals['buy_signals']:
                                for i, signal in enumerate(trading_signals['buy_signals'], 1):
                                    confidence_color = "#4CAF50" if signal['confidence'] == 'High' else "#FFA726"
                                    confidence_icon = "🟢" if signal['confidence'] == 'High' else "🟡"
                                    
                                    # Create instructional content based on signal type
                                    if signal['type'] == 'Value Buy':
                                        instruction = "📚 <b>What is a Value Buy?</b><br>This signal appears when the stock price is below its calculated fair value. It suggests the stock may be undervalued based on fundamental analysis."
                                        action = "✅ <b>What to do:</b> Consider entering a position. This is a long-term investment opportunity based on intrinsic value."
                                    elif signal['type'] == 'Technical Buy':
                                        instruction = "📚 <b>What is a Technical Buy?</b><br>This signal appears when technical indicators (RSI, Support) suggest the stock is oversold and may bounce back."
                                        action = "✅ <b>What to do:</b> Consider a short to medium-term trade. Watch for confirmation with volume."
                                    else:  # Momentum Buy
                                        instruction = "📚 <b>What is a Momentum Buy?</b><br>This signal appears when moving averages show bullish momentum (Golden Cross) and price is above VWAP."
                                        action = "✅ <b>What to do:</b> Consider riding the momentum. Use trailing stop losses to protect gains."
                                    
                                    st.markdown(f"""
                                    <div style="background-color: #e8f5e9; padding: 20px; border-radius: 8px; border-left: 5px solid {confidence_color}; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                        <h4 style="margin: 0 0 10px 0; color: #1B5E20;">{confidence_icon} {signal['type']} - ${signal['price']:.2f}</h4>
                                        <p style="margin: 8px 0; color: #2E7D32; font-weight: bold;">📊 Signal Details:</p>
                                        <p style="margin: 5px 0; color: #2E7D32;">{signal['reason']}</p>
                                        <p style="margin: 10px 0 5px 0; color: #4CAF50; font-weight: bold;">{confidence_icon} Confidence: {signal['confidence']}</p>
                                        <hr style="margin: 10px 0; border-color: #a5d6a7;">
                                        <p style="margin: 8px 0; color: #1B5E20; font-size: 0.9em;">{instruction}</p>
                                        <p style="margin: 8px 0; color: #1B5E20; font-size: 0.9em;">{action}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.markdown("📚 **No active BUY signals at this time.**<br><br>💡 **Learning Tip:** Wait for better entry opportunities. Patience is key in trading. Look for stocks trading below fair value or showing technical support.", unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown("#### 🔴 SELL Signals - Educational Guide")
                            st.caption("💡 Hover over chart markers for detailed explanations")
                            
                            if trading_signals['sell_signals']:
                                for i, signal in enumerate(trading_signals['sell_signals'], 1):
                                    confidence_color = "#EF5350" if signal['confidence'] == 'High' else "#FF9800"
                                    confidence_icon = "🔴" if signal['confidence'] == 'High' else "🟠"
                                    
                                    # Create instructional content based on signal type
                                    if signal['type'] == 'Value Sell':
                                        instruction = "📚 <b>What is a Value Sell?</b><br>This signal appears when the stock price is above its calculated fair value. It suggests the stock may be overvalued and profit-taking opportunity."
                                        action = "✅ <b>What to do:</b> Consider taking profits. You can sell partially or fully depending on your strategy."
                                    elif signal['type'] == 'Technical Sell':
                                        instruction = "📚 <b>What is a Technical Sell?</b><br>This signal appears when technical indicators (RSI, Resistance) suggest the stock is overbought and may pull back."
                                        action = "✅ <b>What to do:</b> Consider taking profits near resistance. Watch for bearish confirmation."
                                    else:  # Momentum Sell
                                        instruction = "📚 <b>What is a Momentum Sell?</b><br>This signal appears when moving averages show bearish momentum (Death Cross) and price is below VWAP."
                                        action = "✅ <b>What to do:</b> Consider exiting to protect capital. Trend reversal may be starting."
                                    
                                    st.markdown(f"""
                                    <div style="background-color: #ffebee; padding: 20px; border-radius: 8px; border-left: 5px solid {confidence_color}; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                        <h4 style="margin: 0 0 10px 0; color: #B71C1C;">{confidence_icon} {signal['type']} - ${signal['price']:.2f}</h4>
                                        <p style="margin: 8px 0; color: #C62828; font-weight: bold;">📊 Signal Details:</p>
                                        <p style="margin: 5px 0; color: #C62828;">{signal['reason']}</p>
                                        <p style="margin: 10px 0 5px 0; color: #EF5350; font-weight: bold;">{confidence_icon} Confidence: {signal['confidence']}</p>
                                        <hr style="margin: 10px 0; border-color: #ef9a9a;">
                                        <p style="margin: 8px 0; color: #B71C1C; font-size: 0.9em;">{instruction}</p>
                                        <p style="margin: 8px 0; color: #B71C1C; font-size: 0.9em;">{action}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.markdown("📚 **No active SELL signals at this time.**<br><br>💡 **Learning Tip:** This means the stock is not showing overvaluation or technical weakness. Continue monitoring for exit signals.", unsafe_allow_html=True)
                        
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
                                    <p style="margin: 8px 0; color: #F57C00; font-weight: bold;">📊 Calculation:</p>
                                    <p style="margin: 5px 0; color: #F57C00;">{sl['reason']}</p>
                                    <hr style="margin: 10px 0; border-color: #ffb74d;">
                                    <p style="margin: 8px 0; color: #E65100; font-size: 0.9em;">
                                        <b>📚 What is a Stop Loss?</b><br>
                                        A stop loss is a predetermined price at which you will exit a position to limit losses. 
                                        It's a crucial risk management tool that protects your capital.<br><br>
                                        <b>✅ How to use:</b><br>
                                        • Set your stop loss order at ${sl['price']:.2f}<br>
                                        • This limits your maximum loss per share<br>
                                        • Never move your stop loss further away (only closer)
                                    </p>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown("📚 **Calculate entry signals first to determine stop loss.**<br><br>💡 **Learning Tip:** A stop loss is essential for risk management. Always set one before entering a trade.", unsafe_allow_html=True)
                        
                        with col2:
                            st.markdown("#### 🎯 Take Profit Targets - Educational Guide")
                            if trading_signals['take_profit']:
                                for tp in trading_signals['take_profit']:
                                    st.markdown(f"""
                                    <div style="background-color: #e8f5e9; padding: 20px; border-radius: 8px; border-left: 5px solid #4CAF50; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                        <h4 style="margin: 0 0 10px 0; color: #1B5E20;">🎯 {tp['label']}</h4>
                                        <p style="margin: 8px 0; color: #2E7D32; font-size: 0.9em;">
                                            <b>📚 What is a Take Profit Target?</b><br>
                                            A take profit target is a predetermined price at which you will exit a position to lock in gains. 
                                            It helps you realize profits before the market reverses.<br><br>
                                            <b>✅ Strategy:</b><br>
                                            • Consider taking partial profits at each target<br>
                                            • Let remaining position run to higher targets<br>
                                            • Adjust targets based on market conditions
                                        </p>
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.markdown("📚 **Calculate entry signals first to determine take profit targets.**<br><br>💡 **Learning Tip:** Setting profit targets helps you lock in gains and avoid greed-driven decisions.", unsafe_allow_html=True)
                        
                        # ===== PROFESSIONAL TRADING TOOLS FOR 90% SUCCESS =====
                        st.markdown("---")
                        st.markdown("## 🎯 Professional Trading Tools - Maximize Success Probability")
                        
                        if trading_signals['buy_signals']:
                            best_buy = min(trading_signals['buy_signals'], key=lambda x: x['price'])
                            entry_price = best_buy['price']
                            
                            # Calculate comprehensive metrics
                            risk = best_buy['price'] - trading_signals['stop_loss']['price'] if trading_signals['stop_loss'] else 0
                            risk_pct = (risk / best_buy['price']) * 100 if best_buy['price'] > 0 else 0
                            
                            best_tp = max(trading_signals['take_profit'], key=lambda x: x['price']) if trading_signals['take_profit'] else None
                            reward = (best_tp['price'] - best_buy['price']) if best_tp else 0
                            reward_pct = (reward / best_buy['price']) * 100 if best_buy['price'] > 0 else 0
                            risk_reward = reward / risk if risk > 0 else 0
                            
                            # Calculate trade probability score (0-100%)
                            probability_score = 50  # Base score
                            if score and score.get('total_score'):
                                probability_score += (score['total_score'] - 50) * 0.3  # Fundamental strength
                            if best_buy['confidence'] == 'High':
                                probability_score += 15
                            elif best_buy['confidence'] == 'Medium':
                                probability_score += 5
                            if risk_reward >= 3:
                                probability_score += 15
                            elif risk_reward >= 2:
                                probability_score += 10
                            elif risk_reward >= 1.5:
                                probability_score += 5
                            if risk_pct <= 3:
                                probability_score += 10  # Low risk
                            elif risk_pct > 7:
                                probability_score -= 10  # High risk
                            
                            # Volume analysis
                            hist = data.get('history')
                            volume_confirmation = "Neutral"
                            if hist is not None and len(hist) > 20:
                                recent_volume = hist['Volume'].iloc[-5:].mean()
                                avg_volume = hist['Volume'].iloc[-20:].mean()
                                if recent_volume > avg_volume * 1.2:
                                    volume_confirmation = "Strong"
                                    probability_score += 10
                                elif recent_volume < avg_volume * 0.8:
                                    volume_confirmation = "Weak"
                                    probability_score -= 5
                            
                            # Market context (SPY trend)
                            try:
                                import yfinance as yf
                                spy = yf.Ticker('SPY')
                                spy_hist = spy.history(period='1mo')
                                if len(spy_hist) > 0:
                                    spy_current = spy_hist['Close'].iloc[-1]
                                    spy_20d = spy_hist['Close'].iloc[-20] if len(spy_hist) >= 20 else spy_current
                                    spy_trend = "Bullish" if spy_current > spy_20d else "Bearish"
                                    if spy_trend == "Bullish":
                                        probability_score += 5
                                    else:
                                        probability_score -= 5
                                else:
                                    spy_trend = "Unknown"
                            except:
                                spy_trend = "Unknown"
                            
                            probability_score = max(20, min(95, probability_score))  # Clamp between 20-95%
                            
                            # Display in prominent cards
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                # Trade Probability Score
                                prob_color = "#4CAF50" if probability_score >= 70 else "#FFA726" if probability_score >= 50 else "#FF9800"
                                prob_status = "Excellent" if probability_score >= 70 else "Good" if probability_score >= 50 else "Fair"
                                
                                st.markdown(f"""
                                <div style="background: linear-gradient(135deg, {prob_color} 0%, #2E7D32 100%); 
                                            padding: 25px; border-radius: 15px; text-align: center; 
                                            box-shadow: 0 4px 6px rgba(0,0,0,0.2); border: 3px solid #1B5E20;">
                                    <h2 style="color: white; margin: 0 0 10px 0; font-size: 2.5em;">📊</h2>
                                    <h3 style="color: white; margin: 0 0 5px 0; font-size: 1.1em; font-weight: bold;">SUCCESS PROBABILITY</h3>
                                    <h1 style="color: white; margin: 10px 0; font-size: 3em; font-weight: bold;">{probability_score:.0f}%</h1>
                                    <p style="color: #C8E6C9; margin: 5px 0; font-size: 0.9em;">{prob_status} Setup</p>
                                    <p style="color: #A5D6A7; margin: 5px 0; font-size: 0.75em;">Based on multiple factors</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with col2:
                                # Risk/Reward Ratio (Prominent)
                                rr_color = "#4CAF50" if risk_reward >= 3 else "#FFA726" if risk_reward >= 2 else "#FF9800"
                                rr_status = "Excellent" if risk_reward >= 3 else "Good" if risk_reward >= 2 else "Fair"
                                
                                st.markdown(f"""
                                <div style="background: linear-gradient(135deg, {rr_color} 0%, #E65100 100%); 
                                            padding: 25px; border-radius: 15px; text-align: center; 
                                            box-shadow: 0 4px 6px rgba(0,0,0,0.2); border: 3px solid #BF360C;">
                                    <h2 style="color: white; margin: 0 0 10px 0; font-size: 2.5em;">⚖️</h2>
                                    <h3 style="color: white; margin: 0 0 5px 0; font-size: 1.1em; font-weight: bold;">RISK/REWARD</h3>
                                    <h1 style="color: white; margin: 10px 0; font-size: 3em; font-weight: bold;">{risk_reward:.2f}:1</h1>
                                    <p style="color: #FFE0B2; margin: 5px 0; font-size: 0.9em;">{rr_status} Ratio</p>
                                    <p style="color: #FFCC80; margin: 5px 0; font-size: 0.75em;">Risk: ${risk:.2f} | Reward: ${reward:.2f}</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with col3:
                                # Volume & Market Context
                                vol_color = "#4CAF50" if volume_confirmation == "Strong" else "#FF9800" if volume_confirmation == "Weak" else "#FFA726"
                                market_color = "#4CAF50" if spy_trend == "Bullish" else "#EF5350" if spy_trend == "Bearish" else "#FFA726"
                                
                                st.markdown(f"""
                                <div style="background: linear-gradient(135deg, {vol_color} 0%, #2E7D32 100%); 
                                            padding: 25px; border-radius: 15px; text-align: center; 
                                            box-shadow: 0 4px 6px rgba(0,0,0,0.2); border: 3px solid #1B5E20;">
                                    <h2 style="color: white; margin: 0 0 10px 0; font-size: 2.5em;">📈</h2>
                                    <h3 style="color: white; margin: 0 0 5px 0; font-size: 1.1em; font-weight: bold;">MARKET CONTEXT</h3>
                                    <p style="color: white; margin: 10px 0; font-size: 1.2em; font-weight: bold;">Volume: {volume_confirmation}</p>
                                    <p style="color: white; margin: 5px 0; font-size: 1.2em; font-weight: bold;">SPY: {spy_trend}</p>
                                    <p style="color: #C8E6C9; margin: 5px 0; font-size: 0.75em;">Confirmation factors</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            st.markdown("---")
                            
                            # Position Sizing Calculator
                            st.markdown("### 💰 Position Sizing Calculator - Critical for Risk Management")
                            st.markdown("*Calculate optimal position size based on your account and risk tolerance*")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                account_size = st.number_input("💰 Account Size ($)", min_value=1000.0, value=10000.0, step=1000.0, key="account_size")
                            
                            with col2:
                                risk_per_trade = st.slider("⚠️ Risk Per Trade (%)", min_value=0.5, max_value=5.0, value=1.0, step=0.5, key="risk_pct")
                                st.caption("💡 Professional traders risk 1-2% per trade")
                            
                            with col3:
                                risk_amount = account_size * (risk_per_trade / 100)
                                max_loss_per_share = risk
                                if max_loss_per_share > 0:
                                    shares_to_buy = int(risk_amount / max_loss_per_share)
                                    position_value = shares_to_buy * entry_price
                                    position_pct = (position_value / account_size) * 100
                                else:
                                    shares_to_buy = 0
                                    position_value = 0
                                    position_pct = 0
                                
                                st.markdown(f"""
                                <div style="background-color: #e3f2fd; padding: 20px; border-radius: 8px; border-left: 5px solid #2196F3; margin-top: 20px;">
                                    <h4 style="margin: 0 0 10px 0; color: #1565C0;">📊 Recommended Position</h4>
                                    <p style="margin: 5px 0; color: #1976D2; font-size: 1.3em;"><b>Shares:</b> {shares_to_buy}</p>
                                    <p style="margin: 5px 0; color: #1976D2; font-size: 1.1em;"><b>Position Value:</b> ${position_value:,.2f}</p>
                                    <p style="margin: 5px 0; color: #1976D2;"><b>% of Account:</b> {position_pct:.1f}%</p>
                                    <p style="margin: 5px 0; color: #1976D2;"><b>Max Loss:</b> ${risk_amount:.2f} ({risk_per_trade}%)</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            st.markdown("---")
                            
                            # Trade Checklist
                            st.markdown("### ✅ Pre-Trade Checklist - Validate Before Entering")
                            
                            checklist_items = []
                            checklist_items.append(("✅ Risk/Reward ≥ 2:1", risk_reward >= 2, f"Current: {risk_reward:.2f}:1"))
                            checklist_items.append(("✅ Risk per trade ≤ 2%", risk_per_trade <= 2.0, f"Current: {risk_per_trade}%"))
                            checklist_items.append(("✅ Stop loss set", trading_signals['stop_loss'] is not None, "Stop loss calculated"))
                            checklist_items.append(("✅ Take profit targets set", len(trading_signals['take_profit']) > 0, f"{len(trading_signals['take_profit'])} targets"))
                            checklist_items.append(("✅ Volume confirmation", volume_confirmation in ["Strong", "Neutral"], f"Volume: {volume_confirmation}"))
                            checklist_items.append(("✅ Market trend favorable", spy_trend == "Bullish" or spy_trend == "Unknown", f"SPY: {spy_trend}"))
                            checklist_items.append(("✅ Fundamental score ≥ 60", score and score.get('total_score', 0) >= 60, f"Score: {score.get('total_score', 0) if score else 0}/100"))
                            checklist_items.append(("✅ Entry price below fair value", intrinsic_value and entry_price < intrinsic_value, f"Entry: ${entry_price:.2f} vs Fair: ${intrinsic_value:.2f}" if intrinsic_value else "N/A"))
                            
                            passed = sum(1 for _, check, _ in checklist_items if check)
                            total = len(checklist_items)
                            checklist_pct = (passed / total) * 100
                            
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                for label, check, detail in checklist_items:
                                    icon = "✅" if check else "❌"
                                    color = "#4CAF50" if check else "#EF5350"
                                    bg_color = "#e8f5e9" if check else "#ffebee"
                                    
                                    st.markdown(f"""
                                    <div style="background-color: {bg_color}; padding: 12px; border-radius: 8px; border-left: 4px solid {color}; margin-bottom: 8px;">
                                        <p style="margin: 0; color: {'#1B5E20' if check else '#B71C1C'}; font-size: 1em;">
                                            <b>{icon} {label}</b> - {detail}
                                        </p>
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            with col2:
                                checklist_color = "#4CAF50" if checklist_pct >= 75 else "#FFA726" if checklist_pct >= 50 else "#EF5350"
                                
                                st.markdown(f"""
                                <div style="background: linear-gradient(135deg, {checklist_color} 0%, #2E7D32 100%); 
                                            padding: 30px; border-radius: 15px; text-align: center; 
                                            box-shadow: 0 4px 6px rgba(0,0,0,0.2); border: 3px solid #1B5E20;">
                                    <h3 style="color: white; margin: 0 0 10px 0; font-size: 1.2em;">CHECKLIST</h3>
                                    <h1 style="color: white; margin: 10px 0; font-size: 3.5em; font-weight: bold;">{passed}/{total}</h1>
                                    <p style="color: #C8E6C9; margin: 5px 0; font-size: 1.1em; font-weight: bold;">{checklist_pct:.0f}% Complete</p>
                                    <p style="color: #A5D6A7; margin: 10px 0 0 0; font-size: 0.9em;">{'✅ Ready to trade!' if checklist_pct >= 75 else '⚠️ Review items' if checklist_pct >= 50 else '❌ Not ready'}</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            st.markdown("---")
                            
                            # Complete Trading Strategy Summary
                            st.markdown("#### 📋 Complete Trading Strategy Summary")
                            
                            st.markdown(f"""
                            <div style="background-color: #e3f2fd; padding: 20px; border-radius: 8px; border-left: 5px solid #2196F3; margin-bottom: 15px;">
                                <h4 style="margin: 0 0 10px 0; color: #1565C0;">📚 Recommended Entry Strategy</h4>
                                <p style="margin: 5px 0; color: #1976D2; font-size: 1.1em;"><b>Entry Price:</b> ${entry_price:.2f}</p>
                                <p style="margin: 5px 0; color: #1976D2;"><b>Reason:</b> {best_buy['reason']}</p>
                                <p style="margin: 5px 0; color: #1976D2;"><b>Signal Type:</b> {best_buy['type']}</p>
                                <p style="margin: 5px 0; color: #1976D2;"><b>Confidence:</b> {best_buy['confidence']}</p>
                                <p style="margin: 5px 0; color: #1976D2;"><b>Success Probability:</b> {probability_score:.0f}%</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if trading_signals['stop_loss']:
                                st.markdown(f"""
                                <div style="background-color: #fff3e0; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                                    <p style="margin: 0; color: #E65100;"><b>⚠️ Risk per Share:</b> ${risk:.2f} ({risk_pct:.1f}%)</p>
                                    <p style="margin: 5px 0 0 0; color: #F57C00; font-size: 0.9em;">💡 This is the maximum you could lose per share if stop loss is hit</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            if trading_signals['take_profit']:
                                st.markdown(f"""
                                <div style="background-color: #e8f5e9; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                                    <p style="margin: 0; color: #1B5E20;"><b>🎯 Reward per Share:</b> ${reward:.2f} ({reward_pct:.1f}%)</p>
                                    <p style="margin: 5px 0 0 0; color: #2E7D32;"><b>📊 Risk/Reward Ratio:</b> {risk_reward:.2f}:1</p>
                                    <p style="margin: 5px 0 0 0; color: #4CAF50; font-size: 0.9em;">💡 A ratio above 2:1 is generally considered good. This means potential reward is {risk_reward:.1f}x the risk.</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # Exit Strategy Options
                            st.markdown("---")
                            st.markdown("#### 🎯 Multiple Exit Strategies - Professional Approach")
                            
                            exit_col1, exit_col2, exit_col3 = st.columns(3)
                            
                            with exit_col1:
                                st.markdown("""
                                <div style="background-color: #e8f5e9; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50;">
                                    <h4 style="margin: 0 0 10px 0; color: #1B5E20;">📊 Strategy 1: Partial Exits</h4>
                                    <p style="margin: 5px 0; color: #2E7D32; font-size: 0.9em;">
                                        <b>Recommended:</b><br>
                                        • Take 33% profit at TP1<br>
                                        • Take 33% profit at TP2<br>
                                        • Let 34% run to TP3 or trailing stop
                                    </p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with exit_col2:
                                st.markdown("""
                                <div style="background-color: #fff3e0; padding: 15px; border-radius: 8px; border-left: 4px solid #FF9800;">
                                    <h4 style="margin: 0 0 10px 0; color: #E65100;">🛡️ Strategy 2: Trailing Stop</h4>
                                    <p style="margin: 5px 0; color: #F57C00; font-size: 0.9em;">
                                        <b>After TP1 hit:</b><br>
                                        • Move stop loss to break-even<br>
                                        • After TP2: Trail stop 5% below high<br>
                                        • Protects profits automatically
                                    </p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with exit_col3:
                                st.markdown("""
                                <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; border-left: 4px solid #2196F3;">
                                    <h4 style="margin: 0 0 10px 0; color: #1565C0;">📈 Strategy 3: Let Winners Run</h4>
                                    <p style="margin: 5px 0; color: #1976D2; font-size: 0.9em;">
                                        <b>For strong trends:</b><br>
                                        • Hold full position to TP3<br>
                                        • Use trailing stop only<br>
                                        • Exit on resistance or reversal signal
                                    </p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            st.markdown("""
                            <div style="background-color: #f3e5f5; padding: 15px; border-radius: 8px; margin-top: 15px;">
                                <h4 style="margin: 0 0 10px 0; color: #6A1B9A;">💡 Professional Trading Rules for 90% Success:</h4>
                                <ul style="margin: 0; padding-left: 20px; color: #7B1FA2;">
                                    <li><b>Always use position sizing calculator</b> - Never risk more than 1-2% per trade</li>
                                    <li><b>Complete the checklist</b> - Only trade when 75%+ items pass</li>
                                    <li><b>Respect stop losses</b> - Never move them further away</li>
                                    <li><b>Use partial exits</b> - Lock in profits at each target</li>
                                    <li><b>Monitor volume</b> - Strong volume confirms moves</li>
                                    <li><b>Check market context</b> - Trade with the trend, not against it</li>
                                    <li><b>Wait for high probability setups</b> - Patience beats FOMO</li>
                                    <li><b>Review your trades</b> - Learn from wins and losses</li>
                                </ul>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("⚠️ 📚 **No active buy signals. Wait for better entry opportunities.**<br><br>💡 **Learning Tip:** Patience is a trader's best friend. Better to wait for high-probability setups than to force trades.", unsafe_allow_html=True)
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
                
                # Financial metrics chart
                chart = create_financial_metrics_chart(metrics)
                if chart:
                    st.plotly_chart(chart, use_container_width=True)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("#### 💰 Profitability")
                    # Gross Margin with visual indicator
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
                hist = data.get('history')
                if show_technical and hist is not None and len(hist) > 0 and 'RSI' in hist.columns:
                    st.markdown("### Technical Indicators")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # RSI
                        latest_rsi = hist['RSI'].iloc[-1]
                        rsi_status = "Oversold" if latest_rsi < 30 else "Overbought" if latest_rsi > 70 else "Neutral"
                        display_enhanced_metric("RSI (14)", f"{latest_rsi:.2f}", delta=rsi_status, metric_name="RSI")
                        
                        # MACD
                        latest_macd = hist['MACD'].iloc[-1]
                        latest_signal = hist['Signal'].iloc[-1]
                        macd_trend = "Bullish" if latest_macd > latest_signal else "Bearish"
                        display_enhanced_metric("MACD", f"{latest_macd:.2f}", delta=macd_trend, metric_name="MACD")
                    
                    with col2:
                        # Moving Average Analysis
                        current_price = hist['Close'].iloc[-1]
                        sma_20 = hist['SMA_20'].iloc[-1]
                        sma_50 = hist['SMA_50'].iloc[-1]
                        
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
                    
                    # RSI Chart
                    import plotly.graph_objects as go
                    fig_rsi = go.Figure()
                    fig_rsi.add_trace(go.Scatter(x=hist.index, y=hist['RSI'],
                                                mode='lines', name='RSI'))
                    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
                    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
                    fig_rsi.update_layout(title='RSI Indicator', height=300, template='plotly_white')
                    st.plotly_chart(fig_rsi, use_container_width=True)
                else:
                    if not show_technical:
                        st.info("Enable 'Show Technical Indicators' in settings to view technical analysis")
                    elif hist is None or len(hist) == 0:
                        st.warning("⚠️ Historical price data not available for technical analysis")
                    else:
                        st.warning("⚠️ Technical indicators not calculated. Historical data may be insufficient.")
            
            with tab5:
                # Risk Analysis
                st.markdown("### ⚠️ Risk Analysis")
                st.markdown("*Color-coded risk levels: 🟢 Low Risk | 🟡 Moderate Risk | 🟠 High Risk | 🔴 Very High Risk*")
                
                hist = data.get('history')
                if hist is not None and len(hist) > 0:
                    prices = hist['Close']
                    
                    # Get market data for beta
                    import yfinance as yf
                    market = yf.Ticker('SPY')
                    market_hist = market.history(period=time_period)
                    market_prices = market_hist['Close'] if len(market_hist) > 0 else None
                    
                    risk_metrics = risk_analyzer.comprehensive_risk_analysis(prices, market_prices)
                    
                    if risk_metrics:
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.markdown("#### 📊 Volatility")
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
                            display_enhanced_metric("Annualized Volatility", f"{vol:.2f}%", 
                                                   help_text="💡 Annual price volatility. Under 20% is low (stable), 20-40% is moderate, over 40% is high volatility (risky).")
                        
                        with col2:
                            st.markdown("#### 📉 Value at Risk")
                            var5 = risk_metrics.get('var_5pct', 0) * 100
                            var1 = risk_metrics.get('var_1pct', 0) * 100
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
                            st.markdown(f"**VaR (1%):** {var1:+.2f}%")
                            st.caption("💡 Maximum expected loss with 99% confidence (more conservative estimate)")
                        
                        with col3:
                            st.markdown("#### 📈 Risk-Adjusted Returns")
                            sharpe = risk_metrics.get('sharpe_ratio', 0)
                            sortino = risk_metrics.get('sortino_ratio', 0)
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
                            st.markdown(f"**Sortino Ratio:** {sortino:.2f}")
                            st.caption("💡 Similar to Sharpe but only considers downside volatility. Over 1.0 is good, measures risk-adjusted returns focusing on negative volatility.")
                        
                        with col4:
                            st.markdown("#### 📊 Drawdown")
                            mdd = risk_metrics.get('max_drawdown_pct', 0)
                            recovery = risk_metrics.get('recovery_days', 0)
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
                            recovery_indicator = "🟢" if recovery < 30 else "🟡" if recovery < 90 else "🟠" if recovery < 180 else "🔴"
                            st.markdown(f"**Recovery Days:** {recovery_indicator} {recovery} days")
                            st.caption("💡 Days taken to recover from maximum drawdown - lower is better")
                        
                        # Detailed table with color coding
                        st.markdown("---")
                        st.markdown("#### 📋 Complete Risk Metrics")
                        
                        # Create color-coded risk metrics table
                        risk_data = []
                        vol_val = risk_metrics.get('volatility', 0)
                        beta_val = risk_metrics.get('beta', 0)
                        sharpe_val = risk_metrics.get('sharpe_ratio', 0)
                        sortino_val = risk_metrics.get('sortino_ratio', 0)
                        mdd_val = risk_metrics.get('max_drawdown_pct', 0)
                        var5_val = risk_metrics.get('var_5pct', 0) * 100
                        cvar5_val = risk_metrics.get('cvar_5pct', 0) * 100
                        
                        def get_risk_indicator(value, metric_type):
                            if metric_type == 'volatility':
                                if value < 20: return "🟢 Low Risk"
                                elif value < 40: return "🟡 Moderate Risk"
                                elif value < 60: return "🟠 High Risk"
                                else: return "🔴 Very High Risk"
                            elif metric_type == 'beta':
                                if 0.8 <= value <= 1.2: return "🟢 Market Risk"
                                elif value < 0.8: return "🟡 Low Risk"
                                elif value <= 1.5: return "🟠 Moderate Risk"
                                else: return "🔴 High Risk"
                            elif metric_type in ['sharpe', 'sortino']:
                                if value >= 2.0: return "🟢 Excellent"
                                elif value >= 1.0: return "🟡 Good"
                                elif value >= 0.5: return "🟠 Fair"
                                else: return "🔴 Poor"
                            elif metric_type in ['mdd', 'var']:
                                abs_val = abs(value)
                                if abs_val < 5: return "🟢 Low Risk"
                                elif abs_val < 10: return "🟡 Moderate Risk"
                                elif abs_val < 20: return "🟠 High Risk"
                                else: return "🔴 Very High Risk"
                            return "N/A"
                        
                        risk_data.append({
                            'Metric': 'Volatility (Annualized)',
                            'Value': f"{vol_val:.2f}%",
                            'Risk Level': get_risk_indicator(vol_val, 'volatility')
                        })
                        risk_data.append({
                            'Metric': 'Beta (vs S&P 500)',
                            'Value': f"{beta_val:.2f}",
                            'Risk Level': get_risk_indicator(beta_val, 'beta')
                        })
                        risk_data.append({
                            'Metric': 'Sharpe Ratio',
                            'Value': f"{sharpe_val:.2f}",
                            'Risk Level': get_risk_indicator(sharpe_val, 'sharpe')
                        })
                        risk_data.append({
                            'Metric': 'Sortino Ratio',
                            'Value': f"{sortino_val:.2f}",
                            'Risk Level': get_risk_indicator(sortino_val, 'sortino')
                        })
                        risk_data.append({
                            'Metric': 'Maximum Drawdown',
                            'Value': f"{mdd_val:.2f}%",
                            'Risk Level': get_risk_indicator(mdd_val, 'mdd')
                        })
                        risk_data.append({
                            'Metric': 'VaR (5% Confidence)',
                            'Value': f"{var5_val:+.2f}%",
                            'Risk Level': get_risk_indicator(var5_val, 'var')
                        })
                        risk_data.append({
                            'Metric': 'Conditional VaR (5%)',
                            'Value': f"{cvar5_val:+.2f}%",
                            'Risk Level': get_risk_indicator(cvar5_val, 'var')
                        })
                        
                        risk_df = pd.DataFrame(risk_data)
                        
                        # Apply color coding to the dataframe
                        def color_risk_level(val):
                            if '🟢' in str(val):
                                return 'background-color: #e8f5e9; color: #1B5E20; font-weight: bold'
                            elif '🟡' in str(val):
                                return 'background-color: #fff9c4; color: #F57F17; font-weight: bold'
                            elif '🟠' in str(val):
                                return 'background-color: #ffe0b2; color: #E65100; font-weight: bold'
                            elif '🔴' in str(val):
                                return 'background-color: #ffebee; color: #B71C1C; font-weight: bold'
                            return ''
                        
                        styled_risk_df = risk_df.style.applymap(color_risk_level, subset=['Risk Level'])
                        st.dataframe(styled_risk_df, use_container_width=True, hide_index=True)
            
            with tab6:
                # Stock Valuation Analysis
                st.markdown("### 💎 Stock Valuation Analysis")
                st.markdown("*Color-coded valuation: 🟢 Undervalued (Buy) | 🟡 Fair Value | 🔴 Overvalued (Sell)*")
                
                try:
                    valuation_result = valuation.comprehensive_valuation(ticker, data['info'], metrics)
                    
                    if valuation_result:
                        intrinsic_value = valuation_result['intrinsic_value']
                        current_price = valuation_result['current_price']
                        discount_premium = valuation_result['discount_premium']
                        valuation_status = valuation_result['valuation_status']
                        methods = valuation_result['methods']
                        
                        # Display main valuation metrics with color coding
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.markdown(f"**Current Market Price:** ${current_price:.2f}")
                            st.caption("💡 The current trading price of the stock")
                        
                        with col2:
                            st.markdown(f"**Intrinsic Value:** ${intrinsic_value:.2f}")
                            st.caption("💡 Estimated true value based on fundamental analysis - what the stock should be worth")
                        
                        with col3:
                            # Valuation Gap with color coding
                            if discount_premium > 20:
                                gap_indicator = "🟢"
                                gap_status = "Strong Buy Opportunity"
                                gap_color = "#4CAF50"
                                bg_color = "#e8f5e9"
                                text_color = "#1B5E20"
                            elif discount_premium > 10:
                                gap_indicator = "🟢"
                                gap_status = "Buy Opportunity"
                                gap_color = "#4CAF50"
                                bg_color = "#e8f5e9"
                                text_color = "#1B5E20"
                            elif discount_premium > -10:
                                gap_indicator = "🟡"
                                gap_status = "Fair Value"
                                gap_color = "#FFA726"
                                bg_color = "#fff9c4"
                                text_color = "#F57F17"
                            elif discount_premium > -20:
                                gap_indicator = "🟠"
                                gap_status = "Caution - Overvalued"
                                gap_color = "#FF9800"
                                bg_color = "#ffe0b2"
                                text_color = "#E65100"
                            else:
                                gap_indicator = "🔴"
                                gap_status = "Significantly Overvalued"
                                gap_color = "#EF5350"
                                bg_color = "#ffebee"
                                text_color = "#B71C1C"
                            
                            st.markdown(f"""
                            <div style="background-color: {bg_color}; 
                                        padding: 15px; border-radius: 8px; border-left: 5px solid {gap_color}; 
                                        margin-bottom: 10px;">
                                <h4 style="margin: 0; color: {text_color};">
                                    {gap_indicator} Valuation Gap: {discount_premium:+.1f}% - {gap_status}
                                </h4>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            delta_color = "normal" if discount_premium > 0 else "inverse"
                            delta_text = "Undervalued" if discount_premium > 0 else "Overvalued"
                            st.metric("Valuation Gap", f"{discount_premium:+.1f}%", 
                                     delta=delta_text, delta_color=delta_color)
                            if discount_premium > 0:
                                st.caption("💡 Stock is trading below intrinsic value - potential buying opportunity")
                            else:
                                st.caption("💡 Stock is trading above intrinsic value - may be expensive")
                        
                        with col4:
                            status_color = "🟢" if "Undervalued" in valuation_status else "🔴" if "Overvalued" in valuation_status else "🟡"
                            status_bg = "#e8f5e9" if "Undervalued" in valuation_status else "#ffebee" if "Overvalued" in valuation_status else "#fff9c4"
                            status_border = "#4CAF50" if "Undervalued" in valuation_status else "#EF5350" if "Overvalued" in valuation_status else "#FFA726"
                            status_text = "#1B5E20" if "Undervalued" in valuation_status else "#B71C1C" if "Overvalued" in valuation_status else "#F57F17"
                            
                            st.markdown(f"""
                            <div style="background-color: {status_bg}; 
                                        padding: 15px; border-radius: 8px; border-left: 5px solid {status_border}; 
                                        margin-bottom: 10px;">
                                <h4 style="margin: 0; color: {status_text};">
                                    {status_color} Valuation Status: {valuation_status}
                                </h4>
                            </div>
                            """, unsafe_allow_html=True)
                            st.caption("💡 Overall valuation assessment based on multiple valuation methods")
                        
                        st.markdown("---")
                        
                        # Valuation methods breakdown with color coding
                        st.markdown("#### 📊 Valuation Methods Breakdown")
                        methods_data = []
                        for method_name, method_data in methods.items():
                            method_gap = ((method_data['intrinsic_value'] - current_price) / current_price * 100)
                            if method_gap > 20:
                                gap_indicator = "🟢 Strong Buy"
                            elif method_gap > 10:
                                gap_indicator = "🟢 Buy"
                            elif method_gap > -10:
                                gap_indicator = "🟡 Fair"
                            elif method_gap > -20:
                                gap_indicator = "🟠 Overvalued"
                            else:
                                gap_indicator = "🔴 Very Overvalued"
                            
                            methods_data.append({
                                'Method': method_name,
                                'Intrinsic Value': f"${method_data['intrinsic_value']:.2f}",
                                'Valuation Gap': f"{method_gap:+.1f}%",
                                'Assessment': gap_indicator,
                                'Details': method_data.get('method', 'N/A')
                            })
                        
                        methods_df = pd.DataFrame(methods_data)
                        
                        # Color code the assessment column
                        def color_valuation_assessment(val):
                            if '🟢' in str(val):
                                return 'background-color: #e8f5e9; color: #1B5E20; font-weight: bold'
                            elif '🟡' in str(val):
                                return 'background-color: #fff9c4; color: #F57F17; font-weight: bold'
                            elif '🟠' in str(val):
                                return 'background-color: #ffe0b2; color: #E65100; font-weight: bold'
                            elif '🔴' in str(val):
                                return 'background-color: #ffebee; color: #B71C1C; font-weight: bold'
                            return ''
                        
                        styled_methods_df = methods_df.style.applymap(color_valuation_assessment, subset=['Assessment'])
                        st.dataframe(styled_methods_df, use_container_width=True, hide_index=True)
                        
                        # Visual comparison
                        st.markdown("---")
                        st.markdown("#### 📈 Market Price vs Intrinsic Value")
                        import plotly.graph_objects as go
                        fig = go.Figure()
                        fig.add_trace(go.Bar(
                            x=['Current Price', 'Intrinsic Value'],
                            y=[current_price, intrinsic_value],
                            marker_color=['#ff6b6b' if discount_premium < 0 else '#51cf66', '#667eea'],
                            text=[f"${current_price:.2f}", f"${intrinsic_value:.2f}"],
                            textposition='auto'
                        ))
                        fig.update_layout(
                            title='Market Price vs Intrinsic Value Comparison',
                            yaxis_title='Price ($)',
                            height=400,
                            template='plotly_white'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Valuation assessment with enhanced color coding
                        st.markdown("---")
                        st.markdown("#### 📋 Valuation Assessment Summary")
                        
                        if discount_premium > 20:
                            st.markdown(f"""
                            <div style="background-color: #e8f5e9; padding: 20px; border-radius: 10px; border-left: 6px solid #4CAF50; margin: 10px 0;">
                                <h3 style="color: #1B5E20; margin: 0;">🟢 ✅ <strong>Strong Buy Opportunity</strong></h3>
                                <p style="color: #2E7D32; font-size: 16px; margin: 10px 0 0 0;">
                                    Stock is significantly <strong>undervalued by {abs(discount_premium):.1f}%</strong>. 
                                    This represents an excellent buying opportunity based on fundamental analysis.
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                        elif discount_premium > 10:
                            st.markdown(f"""
                            <div style="background-color: #e8f5e9; padding: 20px; border-radius: 10px; border-left: 6px solid #4CAF50; margin: 10px 0;">
                                <h3 style="color: #1B5E20; margin: 0;">🟢 ✅ <strong>Buy Opportunity</strong></h3>
                                <p style="color: #2E7D32; font-size: 16px; margin: 10px 0 0 0;">
                                    Stock is <strong>undervalued by {abs(discount_premium):.1f}%</strong>. 
                                    Trading below intrinsic value - good buying opportunity.
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                        elif discount_premium > -10:
                            st.markdown(f"""
                            <div style="background-color: #fff9c4; padding: 20px; border-radius: 10px; border-left: 6px solid #FFA726; margin: 10px 0;">
                                <h3 style="color: #F57F17; margin: 0;">🟡 ℹ️ <strong>Fair Valuation</strong></h3>
                                <p style="color: #F9A825; font-size: 16px; margin: 10px 0 0 0;">
                                    Stock is trading <strong>close to intrinsic value ({discount_premium:+.1f}%)</strong>. 
                                    Price appears reasonable based on fundamentals.
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                        elif discount_premium > -20:
                            st.markdown(f"""
                            <div style="background-color: #ffe0b2; padding: 20px; border-radius: 10px; border-left: 6px solid #FF9800; margin: 10px 0;">
                                <h3 style="color: #E65100; margin: 0;">🟠 ⚠️ <strong>Caution - Overvalued</strong></h3>
                                <p style="color: #EF6C00; font-size: 16px; margin: 10px 0 0 0;">
                                    Stock may be <strong>overvalued by {abs(discount_premium):.1f}%</strong>. 
                                    Consider waiting for a better entry point or reducing position size.
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style="background-color: #ffebee; padding: 20px; border-radius: 10px; border-left: 6px solid #EF5350; margin: 10px 0;">
                                <h3 style="color: #B71C1C; margin: 0;">🔴 ❌ <strong>Significantly Overvalued</strong></h3>
                                <p style="color: #C62828; font-size: 16px; margin: 10px 0 0 0;">
                                    Stock is <strong>significantly overvalued by {abs(discount_premium):.1f}%</strong>. 
                                    High risk of price correction. Consider selling or avoiding new positions.
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown(f"**Based on {valuation_result['number_of_methods']} validated valuation methods**")
                    else:
                        st.warning("⚠️ Valuation calculation not available. Required financial data may be missing.")
                        st.info("💡 This may occur for newer companies or those with limited financial history.")
                except Exception as e:
                    st.error(f"Error calculating valuation: {str(e)}")
            
            with tab7:
                # Ratings Summary Table
                st.markdown("### ⭐ Rating Summary Table")
                st.markdown("*Color-coded ratings: 🟢 Strong Buy/Buy | 🟡 Hold | 🔴 Sell*")
                
                try:
                    ratings_result = ratings_agg.aggregate_ratings(ticker, score, data['info'])
                    
                    if ratings_result:
                        # Display composite rating with color coding
                        composite = ratings_result['composite_rating']
                        avg_score = ratings_result['average_rating_score']
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if "STRONG BUY" in composite.upper() or "STRONG BUY" in composite:
                                rating_emoji = "🟢"
                                rating_color = "#4CAF50"
                                rating_bg = "#e8f5e9"
                                rating_text = "#1B5E20"
                                rating_status = "Strong Buy"
                            elif "BUY" in composite.upper():
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
                                        padding: 20px; border-radius: 10px; border-left: 6px solid {rating_color}; 
                                        margin-bottom: 10px;">
                                <h3 style="color: {rating_text}; margin: 0;">{rating_emoji} <strong>Composite Rating: {composite}</strong></h3>
                                <p style="color: {rating_text}; margin: 5px 0 0 0; font-size: 14px;">Status: {rating_status}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            # Average score with color coding
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
                                        padding: 20px; border-radius: 10px; border-left: 6px solid {score_color}; 
                                        margin-bottom: 10px;">
                                <h3 style="color: {score_text}; margin: 0;">{score_indicator} <strong>Average Score: {avg_score:.2f}/5.0</strong></h3>
                                <p style="color: {score_text}; margin: 5px 0 0 0; font-size: 14px;">Rating: {score_status}</p>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col3:
                            st.metric("Sources", f"{ratings_result['number_of_sources']}")
                        
                        st.markdown("---")
                        
                        # Ratings table with color coding
                        st.markdown("#### 📊 Ratings by Source")
                        ratings_df = ratings_result['ratings_df']
                        
                        # Format for display with color coding
                        display_ratings = []
                        for _, row in ratings_df.iterrows():
                            rating_val = str(row['rating']).upper()
                            rating_score_val = row['rating_score']
                            
                            if "STRONG BUY" in rating_val or rating_score_val >= 4.5:
                                rating_indicator = "🟢 Strong Buy"
                            elif "BUY" in rating_val or rating_score_val >= 3.5:
                                rating_indicator = "🟢 Buy"
                            elif "HOLD" in rating_val or 2.5 <= rating_score_val < 3.5:
                                rating_indicator = "🟡 Hold"
                            elif "SELL" in rating_val or rating_score_val < 2.5:
                                rating_indicator = "🔴 Sell"
                            else:
                                rating_indicator = "🟡 Neutral"
                            
                            display_ratings.append({
                                'Source': row['source'],
                                'Rating': f"{rating_indicator} {row['rating']}",
                                'Rating Score': f"{rating_score_val:.1f}/5.0",
                                'Analysts': row.get('analysts', 'N/A'),
                                'Target Price': f"${row.get('target_price', 0):.2f}" if row.get('target_price', 0) > 0 else 'N/A',
                                'Additional Info': f"Score: {row.get('score', 'N/A')}" if row.get('score') else f"Mean: {row.get('mean_rating', 'N/A'):.2f}" if row.get('mean_rating') else 'N/A'
                            })
                        
                        ratings_display_df = pd.DataFrame(display_ratings)
                        
                        # Color code the Rating column
                        def color_rating(val):
                            if '🟢' in str(val):
                                return 'background-color: #e8f5e9; color: #1B5E20; font-weight: bold'
                            elif '🟡' in str(val):
                                return 'background-color: #fff9c4; color: #F57F17; font-weight: bold'
                            elif '🔴' in str(val):
                                return 'background-color: #ffebee; color: #B71C1C; font-weight: bold'
                            return ''
                        
                        styled_ratings_df = ratings_display_df.style.applymap(color_rating, subset=['Rating'])
                        st.dataframe(styled_ratings_df, use_container_width=True, hide_index=True)
                        
                        # Consensus summary with color coding
                        st.markdown("---")
                        st.markdown("#### 🎯 Consensus Summary")
                        consensus = ratings_result['consensus']
                        consensus_rating = consensus['rating'].upper()
                        consensus_score = consensus['score']
                        
                        if "STRONG BUY" in consensus_rating or "BUY" in consensus_rating or consensus_score >= 3.5:
                            consensus_indicator = "🟢"
                            consensus_color = "#4CAF50"
                            consensus_bg = "#e8f5e9"
                            consensus_text = "#1B5E20"
                            consensus_status = "Positive"
                        elif "SELL" in consensus_rating or consensus_score < 2.5:
                            consensus_indicator = "🔴"
                            consensus_color = "#EF5350"
                            consensus_bg = "#ffebee"
                            consensus_text = "#B71C1C"
                            consensus_status = "Negative"
                        else:
                            consensus_indicator = "🟡"
                            consensus_color = "#FFA726"
                            consensus_bg = "#fff9c4"
                            consensus_text = "#F57F17"
                            consensus_status = "Neutral"
                        
                        st.markdown(f"""
                        <div style="background-color: {consensus_bg}; 
                                    padding: 20px; border-radius: 10px; border-left: 6px solid {consensus_color}; 
                                    margin: 10px 0;">
                            <h3 style="color: {consensus_text}; margin: 0;">{consensus_indicator} <strong>Overall Consensus: {consensus['rating']}</strong></h3>
                            <p style="color: {consensus_text}; font-size: 16px; margin: 10px 0 0 0;">
                                Score: <strong>{consensus['score']:.2f}/5.0</strong> | 
                                Based on <strong>{consensus['sources']} verified sources</strong> | 
                                Status: <strong>{consensus_status}</strong>
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning("⚠️ Ratings data not available from all sources.")
                        st.info("💡 Some rating sources may have limited data for this stock.")
                except Exception as e:
                    st.error(f"Error aggregating ratings: {str(e)}")
            
            with tab8:
                # Peer Benchmarking
                st.markdown("### 🔗 Peer Benchmarking")
                st.markdown("*Compare performance against sector competitors*")
                
                try:
                    with st.spinner("Analyzing peers..."):
                        peers = peer_bench.get_sector_peers(ticker, data['info'].get('sector'))
                        
                        if peers:
                            benchmark_result = peer_bench.benchmark_against_peers(ticker, metrics, score, peers)
                            
                            if benchmark_result:
                                comparison_df = benchmark_result['peer_comparison']
                                summary = benchmark_result['benchmark_summary']
                                
                                # Display benchmark summary
                                if summary:
                                    col1, col2, col3 = st.columns(3)
                                    
                                    with col1:
                                        percentile = summary['percentile']
                                        percentile_emoji = "🟢" if percentile >= 75 else "🟡" if percentile >= 50 else "🔴"
                                        st.metric("Peer Ranking", f"{percentile_emoji} {summary['position']}/{summary['total_peers']}")
                                    
                                    with col2:
                                        st.metric("Percentile Rank", f"{percentile:.0f}th percentile")
                                    
                                    with col3:
                                        st.metric("Performance", f"Better than {summary['better_than']}")
                                
                                st.markdown("---")
                                
                                # Peer comparison table
                                st.markdown("#### 📊 Peer Comparison Table")
                                
                                # Prepare display dataframe
                                display_cols = ['ticker', 'score', 'pe_ratio', 'roe', 'revenue_growth', 'profit_margin', 'current_price']
                                if 'company_name' in comparison_df.columns:
                                    display_cols.insert(1, 'company_name')
                                
                                comparison_display = comparison_df[display_cols].copy()
                                comparison_display = comparison_display.rename(columns={
                                    'ticker': 'Ticker',
                                    'company_name': 'Company',
                                    'score': 'Score',
                                    'pe_ratio': 'P/E Ratio',
                                    'roe': 'ROE (%)',
                                    'revenue_growth': 'Revenue Growth (%)',
                                    'profit_margin': 'Profit Margin (%)',
                                    'current_price': 'Price ($)'
                                })
                                
                                # Highlight main stock
                                def highlight_main_stock(row):
                                    if row['Ticker'] == ticker.upper():
                                        return ['background-color: #e3f2fd'] * len(row)
                                    return [''] * len(row)
                                
                                st.dataframe(
                                    comparison_display.style.apply(highlight_main_stock, axis=1)
                                    .format({
                                        'Score': '{:.0f}',
                                        'P/E Ratio': '{:.2f}',
                                        'ROE (%)': '{:.2f}',
                                        'Revenue Growth (%)': '{:.2f}',
                                        'Profit Margin (%)': '{:.2f}',
                                        'Price ($)': '${:.2f}'
                                    })
                                    .background_gradient(subset=['Score'], cmap='RdYlGn', vmin=0, vmax=100),
                                    use_container_width=True,
                                    hide_index=True
                                )
                                
                                # Ranking visualization
                                st.markdown("---")
                                st.markdown("#### 📈 Score Comparison")
                                
                                fig = px.bar(
                                    comparison_df.sort_values('score', ascending=True),
                                    x='score',
                                    y='ticker',
                                    orientation='h',
                                    color='score',
                                    color_continuous_scale='RdYlGn',
                                    title='Peer Score Comparison',
                                    labels={'score': 'Score', 'ticker': 'Ticker'}
                                )
                                fig.update_layout(height=400, template='plotly_white')
                                fig.add_vline(x=score['total_score'], line_dash="dash", 
                                            line_color="blue", annotation_text=f"{ticker} Score")
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.warning("⚠️ Could not complete peer benchmarking. Limited peer data available.")
                        else:
                            st.info(f"💡 Could not identify sector peers for {ticker}. Peer comparison unavailable.")
                except Exception as e:
                    st.error(f"Error performing peer benchmarking: {str(e)}")
            
            with tab9:
                # Top News for Stock
                st.markdown("### 📰 Top News for {}".format(ticker.upper()))
                st.markdown("*Latest news articles and market updates related to this stock*")
                
                try:
                    # Get top news articles
                    news_limit = st.slider("Number of articles to display", 5, 20, 10, key=f"news_limit_{ticker}")
                    
                    with st.spinner(f"Fetching latest news for {ticker}..."):
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
                            st.info("💡 This may be due to:\n"
                                  "- Limited news coverage for this stock\n"
                                  "- Temporary unavailability of news data\n"
                                  "- Newly listed stock with no news yet\n\n"
                                  "**Tip:** Try a major stock ticker like AAPL, MSFT, or GOOGL to test the news feature.")
                        else:
                            st.warning(f"⚠️ Unable to fetch news for {ticker}.")
                            st.info("💡 News data may not be available for this stock. This could be due to:\n"
                                  "- Limited coverage from news sources\n"
                                  "- Newly listed stock\n"
                                  "- Data source limitations")
                except Exception as e:
                    st.error(f"Error fetching news: {str(e)}")
                    st.info("💡 News data may be temporarily unavailable. Please try again later.")
        else:
            st.error(f"❌ Error fetching data for {ticker}")
            st.markdown("""
            <div style="background-color: #fff3cd; padding: 20px; border-radius: 8px; border-left: 5px solid #ffc107; margin: 15px 0;">
                <h4 style="margin: 0 0 10px 0; color: #856404;">🔍 Troubleshooting Guide</h4>
                <ul style="margin: 0; padding-left: 20px; color: #856404;">
                    <li><b>Check ticker symbol:</b> Make sure it's correct (e.g., AAPL not APPL, MSFT not MFT)</li>
                    <li><b>Verify stock exists:</b> Stock must be listed on a major exchange (NYSE, NASDAQ)</li>
                    <li><b>Network issues:</b> Yahoo Finance may be temporarily unavailable - try again in a moment</li>
                    <li><b>Rate limiting:</b> Too many requests - wait 30 seconds and try again</li>
                    <li><b>Try common tickers:</b> AAPL, MSFT, GOOGL, NVDA, TSLA usually work</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.info("💡 **Common working tickers to test:**\n"
                   "- **AAPL** (Apple)\n"
                   "- **MSFT** (Microsoft)\n"
                   "- **GOOGL** (Google)\n"
                   "- **NVDA** (NVIDIA)\n"
                   "- **TSLA** (Tesla)\n"
                   "- **AMZN** (Amazon)")

