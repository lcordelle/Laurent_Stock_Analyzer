"""
Batch Stock Comparison Page
Compare multiple stocks side by side with detailed analysis
"""

import streamlit as st
import pandas as pd
from utils.auth import require_auth
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from utils.stock_analyzer import StockAnalyzer
from utils.cache_helpers import get_cached_stock_data
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
from components.styling import apply_platform_theme, render_header, render_footer, render_trading_signal_card, render_buy_sell_badge, render_analyst_ranking_panel
from components.navigation import render_top_navigation
from components.outcome_sections import render_outcome_sections

require_auth()

# Page configuration
st.set_page_config(
    page_title="Batch Stock Comparison",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply theme and navigation
apply_platform_theme()
render_top_navigation()

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

# Header - explicit Batch Comparison (not Single Stock)
render_header("Batch comparison", "Same dashboard per ticker — executive KPIs, analyst, peers, forecast")

# Input for multiple tickers with form for Enter key submission
with st.form("batch_comparison_form", clear_on_submit=False):
    tickers_input = st.text_area(
        "Stock Tickers or Company Names (comma-separated)",
        value="",
        height=100,
        placeholder="e.g., AAPL, Apple, NVDA, Microsoft, Tesla"
    )
    submitted = st.form_submit_button("📊 Compare Stocks", use_container_width=True)

if submitted and tickers_input:
    tickers = [t.strip() for t in tickers_input.split(',') if t.strip()]
    
    if len(tickers) > 10:
        st.warning("⚠️ Please limit comparison to 10 stocks maximum")
        tickers = tickers[:10]
    
    stocks_data = {}
    failed_tickers = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, ticker in enumerate(tickers):
        status_text.text(f"Fetching data for {ticker}... (max 15s per ticker)")
        try:
            data = analyzer.get_stock_data(ticker, period=time_period)
            if data and data.get('history') is not None and len(data.get('history', [])) > 0:
                stocks_data[ticker] = data
            else:
                failed_tickers.append(ticker)
        except Exception as e:
            failed_tickers.append(ticker)
            print(f"Error fetching {ticker}: {e}", file=__import__('sys').stderr)
        progress_bar.progress((i + 1) / len(tickers))
        # Small delay to avoid rate limiting
        import time
        time.sleep(0.5)
    
    status_text.empty()
    progress_bar.empty()
    
    # Show failed tickers if any
    if failed_tickers:
        st.error(f"❌ Could not fetch data for: {', '.join(failed_tickers)}")
        st.info("💡 **Troubleshooting tips:**\n"
               "- Verify ticker symbols are correct (e.g., AAPL not APPL)\n"
               "- Some stocks may have limited data availability\n"
               "- Try again in a few moments (Yahoo Finance may be rate limiting)\n"
               "- Check that stocks are listed on major exchanges")
    
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
        st.subheader("Cross-ticker snapshot")
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
        st.subheader("Per-ticker dashboards")
        
        # Display detailed analysis for each stock (same layout as Single Analysis)
        for ticker in sorted_tickers:
            info = stocks_analysis[ticker]
            data = info['data']
            metrics = info['metrics']
            score = info['score']
            forecast = info['forecast']
            
            # Get news articles
            news_articles = []
            try:
                news_articles = news_market.get_stock_news(ticker, limit=10)
            except Exception as e:
                pass
            
            # Get analyst ratings
            ratings_result = None
            try:
                ratings_result = ratings_agg.aggregate_ratings(ticker, score, data['info'])
            except Exception as e:
                pass
            
            # Calculate intrinsic value
            intrinsic_value = None
            try:
                valuation_result = valuation.comprehensive_valuation(ticker, data['info'], metrics)
                if valuation_result:
                    intrinsic_value = valuation_result['intrinsic_value']
            except:
                pass
            
            # Get trading signals
            trading_signals_data = None
            try:
                signals_result = create_trading_signals_chart(data, intrinsic_value=intrinsic_value, metrics=metrics, score=score, analyzer=analyzer)
                if signals_result:
                    _, trading_signals_data = signals_result
            except Exception as e:
                pass
            
            # Render outcome sections with clickable boxes (same as Single Analysis)
            render_outcome_sections(
                ticker=ticker,
                data=data,
                metrics=metrics,
                score=score,
                forecast=forecast,
                intrinsic_value=intrinsic_value,
                news_articles=news_articles,
                ratings_result=ratings_result,
                trading_signals=trading_signals_data
            )
            
            st.markdown("---")
        
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

