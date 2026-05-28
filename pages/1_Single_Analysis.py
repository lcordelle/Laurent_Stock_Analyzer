"""
Single Stock Analysis Page
Deep dive analysis for individual stocks
"""

import streamlit as st
from utils.auth import require_auth
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from utils.stock_analyzer import StockAnalyzer
from utils.cache_helpers import get_cached_stock_data
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
from components.styling import apply_platform_theme, render_header, render_footer, render_trading_signal_card, render_buy_sell_badge, render_analyst_ranking_panel
from components.navigation import render_top_navigation
from components.outcome_sections import render_outcome_sections
from utils.factor_grades import compute_factor_grades
from utils.dividend_scorecard import compute_dividend_scorecard
from utils.earnings_analysis import fetch_earnings_data
from utils.ai_analyst import generate_analyst_report_full
from utils.candlestick_patterns import detect_patterns, patterns_to_df

require_auth()

# Page configuration
st.set_page_config(
    page_title="Single Stock Analysis",
    page_icon="📊",
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
show_technical = st.session_state.get('show_technical', True)
show_fundamentals = st.session_state.get('show_fundamentals', True)

# Header
render_header("Single stock analysis", "Dashboard · forecast · signals — same layout as batch & screener")

# Input section with form for Enter key submission
with st.form("single_analysis_form", clear_on_submit=False):
    ticker = st.text_input("Stock Ticker or Company Name", value="", key="single_ticker", placeholder="e.g., AAPL, Apple, NVDA, Microsoft").strip()
    submitted = st.form_submit_button("🔍 Analyze", use_container_width=True)

if submitted and ticker:
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
            
            # Get trading signals
            trading_signals_data = None
            try:
                signals_result = create_trading_signals_chart(data, intrinsic_value=intrinsic_value, metrics=metrics, score=score, analyzer=analyzer)
                if signals_result:
                    _, trading_signals_data = signals_result
            except Exception as e:
                pass
            
            # Compute new Seeking Alpha-style features
            sector = (data.get("info") or {}).get("sector", "") or ""
            company_name = (data.get("info") or {}).get("longName", ticker) or ticker

            factor_grades = None
            try:
                factor_grades = compute_factor_grades(ticker, sector)
            except Exception as e:
                st.warning(f"Factor grades error: {e}")

            dividend_scorecard = None
            try:
                dividend_scorecard = compute_dividend_scorecard(ticker, sector)
            except Exception as e:
                st.warning(f"Dividend scorecard error: {e}")

            earnings_data = None
            try:
                earnings_data = fetch_earnings_data(ticker)
            except Exception as e:
                st.warning(f"Earnings data error: {e}")

            analyst_report = None
            try:
                analyst_report = generate_analyst_report_full(
                    ticker=ticker,
                    company_name=company_name,
                    sector=sector,
                    metrics=metrics or {},
                    score=score or {},
                    factor_grades=factor_grades,
                    earnings_data=earnings_data,
                    dividend_scorecard=dividend_scorecard,
                    short_interest=None,
                )
            except Exception as e:
                st.warning(f"AI analyst error: {e}")

            # Render outcome sections
            render_outcome_sections(
                ticker=ticker,
                data=data,
                metrics=metrics,
                score=score,
                forecast=forecast,
                intrinsic_value=intrinsic_value,
                news_articles=news_articles,
                ratings_result=ratings_result,
                trading_signals=trading_signals_data,
                factor_grades=factor_grades,
                dividend_scorecard=dividend_scorecard,
                earnings_data=earnings_data,
                analyst_report=analyst_report,
            )

            # Candlestick pattern recognition
            try:
                hist = data.get('history')
                if hist is not None and len(hist) >= 5:
                    patterns = detect_patterns(hist)
                    if patterns:
                        st.markdown("---")
                        st.markdown("### Candlestick Patterns Detected")
                        df_patterns = patterns_to_df(patterns)
                        if not df_patterns.empty:
                            bullish = df_patterns[df_patterns['Signal'].str.contains('Bullish')]
                            bearish = df_patterns[df_patterns['Signal'].str.contains('Bearish')]
                            neutral = df_patterns[df_patterns['Signal'].str.contains('Neutral')]
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                st.metric("Bullish Signals", len(bullish))
                            with c2:
                                st.metric("Bearish Signals", len(bearish))
                            with c3:
                                st.metric("Neutral Signals", len(neutral))
                            st.dataframe(df_patterns, use_container_width=True, hide_index=True)
            except Exception:
                pass

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

render_footer()

