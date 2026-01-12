"""
Performance Tracking Page
Track analysis history, forecast accuracy, and performance metrics
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils.performance_tracker import PerformanceTracker
from utils.stock_analyzer import StockAnalyzer
from components.styling import apply_platform_theme, render_header, render_footer
from components.navigation import render_navigation

# Page configuration
st.set_page_config(
    page_title="Performance Tracking",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply theme and navigation
apply_platform_theme()
render_navigation()

# Initialize
if 'performance_tracker' not in st.session_state:
    st.session_state.performance_tracker = PerformanceTracker()

if 'analyzer' not in st.session_state:
    st.session_state.analyzer = StockAnalyzer()

tracker = st.session_state.performance_tracker
analyzer = st.session_state.analyzer

# Header
render_header("📊 Performance Tracking", "Track analysis history and forecast accuracy")

# Tabs
tab1, tab2, tab3 = st.tabs(["📈 Analysis History", "🎯 Forecast Accuracy", "📊 Score Trends"])

with tab1:
    st.markdown("### 📈 Analysis History")
    
    ticker = st.text_input("Enter Stock Ticker:", value="NVDA", key="track_ticker").upper()
    days = st.slider("History Period (days):", 7, 90, 30, key="history_days")
    
    col1, col2 = st.columns(2)
    with col1:
        analyze_btn = st.button("Analyze & Save", key="analyze_save")
    with col2:
        view_history_btn = st.button("View History", key="view_history")
    
    if analyze_btn and ticker:
        with st.spinner(f"Analyzing {ticker} and saving to history..."):
            data = analyzer.get_stock_data(ticker, period="1y")
            
            if data:
                metrics = analyzer.get_key_metrics(data)
                score = analyzer.calculate_score(data)
                
                if len(data['history']) >= 20:
                    data['history'] = analyzer.calculate_technical_indicators(data['history'])
                
                forecast = analyzer.calculate_forecast(data, metrics, score)
                
                # Save analysis
                analysis_data = {
                    'score': score,
                    'forecast': forecast,
                    'metrics': metrics,
                    'current_price': metrics['Current Price']
                }
                
                saved = tracker.save_analysis(ticker, analysis_data)
                
                if saved:
                    st.success(f"✅ Analysis saved for {ticker}")
                    st.info("💡 You can track this stock's performance over time using the 'View History' button")
                else:
                    st.warning("Could not save analysis")
            else:
                st.error(f"Could not fetch data for {ticker}")
    
    if view_history_btn and ticker:
        with st.spinner(f"Loading history for {ticker}..."):
            history = tracker.get_analysis_history(ticker, days)
            
            if len(history) > 0:
                st.success(f"Found {len(history)} analysis records for {ticker}")
                
                # Display history table
                st.dataframe(
                    history.style.format({
                        'Score': '{:.0f}',
                        'Price': '${:.2f}',
                        'Forecast Price': '${:.2f}',
                        'Probability': '{:.1f}%'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
                
                # Visualizations
                col1, col2 = st.columns(2)
                
                with col1:
                    # Score over time
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=history['Date'],
                        y=history['Score'],
                        mode='lines+markers',
                        name='Score',
                        line=dict(color='#1f77b4', width=2)
                    ))
                    fig.update_layout(
                        title='Score Trend Over Time',
                        xaxis_title='Date',
                        yaxis_title='Score',
                        height=400,
                        template='plotly_white'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Price vs Forecast
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=history['Date'],
                        y=history['Price'],
                        mode='lines+markers',
                        name='Actual Price',
                        line=dict(color='green', width=2)
                    ))
                    fig.add_trace(go.Scatter(
                        x=history['Date'],
                        y=history['Forecast Price'],
                        mode='lines+markers',
                        name='Forecast Price',
                        line=dict(color='blue', width=2, dash='dash')
                    ))
                    fig.update_layout(
                        title='Price vs Forecast Over Time',
                        xaxis_title='Date',
                        yaxis_title='Price ($)',
                        height=400,
                        template='plotly_white'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"No analysis history found for {ticker}. Run an analysis first and save it.")

with tab2:
    st.markdown("### 🎯 Forecast Accuracy")
    
    accuracy_ticker = st.text_input("Enter Stock Ticker:", value="NVDA", key="accuracy_ticker").upper()
    accuracy_days = st.slider("Analysis Period (days):", 14, 180, 30, key="accuracy_period")
    
    if st.button("Calculate Accuracy", key="calc_accuracy"):
        with st.spinner(f"Calculating forecast accuracy for {accuracy_ticker}..."):
            accuracy = tracker.calculate_forecast_accuracy(accuracy_ticker, accuracy_days)
            
            if accuracy['samples'] > 0:
                st.success(f"Accuracy analysis based on {accuracy['samples']} forecasts")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Forecast Accuracy", f"{accuracy['forecast_accuracy']:.1f}%")
                
                with col2:
                    st.metric("Average Error", f"{accuracy['price_error']:.2f}%")
                
                with col3:
                    st.metric("Direction Accuracy", f"{accuracy['direction_accuracy']:.1f}%")
                
                with col4:
                    st.metric("Sample Size", f"{accuracy['samples']}")
                
                # Accuracy visualization
                st.markdown("---")
                st.markdown("#### 📊 Accuracy Breakdown")
                
                accuracy_df = pd.DataFrame([
                    {'Metric': 'Overall Accuracy', 'Value': accuracy['forecast_accuracy']},
                    {'Metric': 'Price Prediction Error', 'Value': accuracy['price_error']},
                    {'Metric': 'Direction Accuracy', 'Value': accuracy['direction_accuracy']},
                ])
                
                fig = px.bar(accuracy_df, x='Metric', y='Value',
                           title='Forecast Accuracy Metrics',
                           color='Value',
                           color_continuous_scale='RdYlGn')
                fig.update_layout(height=400, template='plotly_white')
                st.plotly_chart(fig, use_container_width=True)
                
                # Interpretation
                if accuracy['forecast_accuracy'] >= 70:
                    st.success("✅ Excellent forecast accuracy!")
                elif accuracy['forecast_accuracy'] >= 50:
                    st.info("📊 Good forecast accuracy")
                else:
                    st.warning("⚠️ Forecast accuracy could be improved")
            else:
                st.info(f"Not enough historical data for {accuracy_ticker}. Need at least 2 saved analyses.")

with tab3:
    st.markdown("### 📊 Score Trends")
    
    trend_ticker = st.text_input("Enter Stock Ticker:", value="NVDA", key="trend_ticker").upper()
    trend_days = st.slider("Trend Period (days):", 7, 90, 30, key="trend_period")
    
    if st.button("Analyze Trend", key="analyze_trend"):
        with st.spinner(f"Analyzing score trend for {trend_ticker}..."):
            trend = tracker.get_score_trend(trend_ticker, trend_days)
            
            if trend['data_points'] > 0:
                st.success(f"Trend analysis based on {trend['data_points']} data points")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    trend_icon = "📈" if trend['trend'] == 'improving' else "📉" if trend['trend'] == 'declining' else "➡️"
                    st.metric("Trend", f"{trend_icon} {trend['trend'].title()}")
                
                with col2:
                    change_color = "normal" if trend['change'] > 0 else "inverse"
                    st.metric("Score Change", f"{trend['change']:+.0f}", delta=f"{trend['change']} points")
                
                with col3:
                    st.metric("Current Score", f"{trend['current_score']:.0f}")
                
                with col4:
                    st.metric("Average Score", f"{trend['average_score']:.1f}")
                
                # Get full history for visualization
                history = tracker.get_analysis_history(trend_ticker, trend_days)
                
                if len(history) > 0:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=history['Date'],
                        y=history['Score'],
                        mode='lines+markers',
                        name='Score',
                        line=dict(color='#1f77b4', width=3),
                        marker=dict(size=8)
                    ))
                    fig.add_hline(
                        y=trend['average_score'],
                        line_dash="dash",
                        line_color="gray",
                        annotation_text=f"Average: {trend['average_score']:.1f}"
                    )
                    fig.update_layout(
                        title=f'Score Trend for {trend_ticker}',
                        xaxis_title='Date',
                        yaxis_title='Score',
                        height=500,
                        template='plotly_white'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"No trend data available for {trend_ticker}. Run analyses and save them first.")

render_footer()

