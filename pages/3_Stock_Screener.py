"""
Stock Screener Page
Filter stocks based on custom criteria with detailed analysis
"""

import re
import streamlit as st
from utils.auth import require_auth
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
from components.styling import apply_platform_theme, render_header, render_footer, render_trading_signal_card, render_buy_sell_badge, render_analyst_ranking_panel
from components.navigation import render_top_navigation
from components.outcome_sections import render_outcome_sections

require_auth()

# Page configuration
st.set_page_config(
    page_title="Stock Screener",
    page_icon="🔍",
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
render_header("Stock screener", "Filter universe — screened names use the same dashboard as single & batch")

# Tabs for Screener, Portfolio Analysis, and Risk Dashboard
tab_screener, tab_portfolio, tab_risk = st.tabs(["🔍 Stock Screener", "💼 Portfolio Analyzer", "📊 Risk Dashboard"])

with tab_screener:
    # Saved criteria section
    if 'saved_criteria' not in st.session_state:
        st.session_state.saved_criteria = {}
    
    col_save, col_load = st.columns([3, 1])
    with col_save:
        criteria_name = st.text_input("💾 Save Criteria As:", placeholder="e.g., Growth Stocks, Value Plays")
    with col_load:
        if st.session_state.saved_criteria:
            selected_criteria = st.selectbox("📂 Load Saved:", ["-- Select --"] + list(st.session_state.saved_criteria.keys()))
            if selected_criteria != "-- Select --" and st.button("Load"):
                saved = st.session_state.saved_criteria[selected_criteria]
                st.session_state.current_criteria = saved
                st.rerun()
    
    # Initialize current criteria from session state or defaults
    if 'current_criteria' not in st.session_state:
        st.session_state.current_criteria = {}
    
    current = st.session_state.current_criteria
    
    # Filters in tabs
    filter_tab1, filter_tab2, filter_tab3, filter_tab4 = st.tabs(["💰 Valuation", "📊 Profitability", "📈 Growth", "📉 Technical"])
    
    with filter_tab1:
        col1, col2 = st.columns(2)
        with col1:
            pe_min = st.number_input("Min P/E Ratio", value=current.get('pe_min', 0.0), step=1.0, key='pe_min')
            pe_max = st.number_input("Max P/E Ratio", value=current.get('pe_max', 100.0), step=1.0, key='pe_max')
        with col2:
            market_cap_min = st.selectbox(
                "Min Market Cap",
                ["Any", "1M", "10M", "100M", "1B", "10B", "100B"],
                index=["Any", "1M", "10M", "100M", "1B", "10B", "100B"].index(current.get('market_cap_min', "Any")) if current.get('market_cap_min', "Any") in ["Any", "1M", "10M", "100M", "1B", "10B", "100B"] else 0,
                key='market_cap_min'
            )
    
    with filter_tab2:
        col1, col2 = st.columns(2)
        with col1:
            margin_min = st.slider("Min Gross Margin %", 0, 100, current.get('margin_min', 20), key='margin_min')
            roe_min = st.slider("Min ROE %", 0, 100, current.get('roe_min', 10), key='roe_min')
        with col2:
            profit_margin_min = st.slider("Min Profit Margin %", -50, 100, current.get('profit_margin_min', 0), key='profit_margin_min')
    
    with filter_tab3:
        col1, col2 = st.columns(2)
        with col1:
            revenue_growth_min = st.slider("Min Revenue Growth %", -50, 100, current.get('revenue_growth_min', 0), key='revenue_growth_min')
            earnings_growth_min = st.slider("Min Earnings Growth %", -50, 100, current.get('earnings_growth_min', 0), key='earnings_growth_min')
        with col2:
            score_min = st.slider("Min Overall Score", 0, 100, current.get('score_min', 0), key='score_min')
    
    with filter_tab4:
        st.markdown("**Technical Indicator Filters**")
        col1, col2, col3 = st.columns(3)
        with col1:
            rsi_min = st.slider("RSI Min", 0, 100, current.get('rsi_min', 0), key='rsi_min')
            rsi_max = st.slider("RSI Max", 0, 100, current.get('rsi_max', 100), key='rsi_max')
            rsi_oversold = st.checkbox("RSI Oversold (<30)", value=current.get('rsi_oversold', False), key='rsi_oversold')
            rsi_overbought = st.checkbox("RSI Overbought (>70)", value=current.get('rsi_overbought', False), key='rsi_overbought')
        with col2:
            macd_bullish = st.checkbox("MACD Bullish Crossover", value=current.get('macd_bullish', False), key='macd_bullish')
            macd_bearish = st.checkbox("MACD Bearish Crossover", value=current.get('macd_bearish', False), key='macd_bearish')
            stoch_oversold = st.checkbox("Stochastic Oversold (<20)", value=current.get('stoch_oversold', False), key='stoch_oversold')
            stoch_overbought = st.checkbox("Stochastic Overbought (>80)", value=current.get('stoch_overbought', False), key='stoch_overbought')
        with col3:
            adx_min = st.slider("ADX Min (Trend Strength)", 0, 100, current.get('adx_min', 0), key='adx_min')
            price_above_sma20 = st.checkbox("Price > SMA 20", value=current.get('price_above_sma20', False), key='price_above_sma20')
            price_above_sma50 = st.checkbox("Price > SMA 50", value=current.get('price_above_sma50', False), key='price_above_sma50')
            golden_cross = st.checkbox("Golden Cross (SMA20 > SMA50)", value=current.get('golden_cross', False), key='golden_cross')
    
    # Save criteria button
    col_save_btn, _ = st.columns([1, 4])
    with col_save_btn:
        if criteria_name and st.button("💾 Save Criteria"):
            criteria_dict = {
                'pe_min': pe_min, 'pe_max': pe_max, 'market_cap_min': market_cap_min,
                'margin_min': margin_min, 'roe_min': roe_min, 'profit_margin_min': profit_margin_min,
                'revenue_growth_min': revenue_growth_min, 'earnings_growth_min': earnings_growth_min, 'score_min': score_min,
                'rsi_min': rsi_min, 'rsi_max': rsi_max, 'rsi_oversold': rsi_oversold, 'rsi_overbought': rsi_overbought,
                'macd_bullish': macd_bullish, 'macd_bearish': macd_bearish,
                'stoch_oversold': stoch_oversold, 'stoch_overbought': stoch_overbought,
                'adx_min': adx_min, 'price_above_sma20': price_above_sma20, 'price_above_sma50': price_above_sma50,
                'golden_cross': golden_cross
            }
            st.session_state.saved_criteria[criteria_name] = criteria_dict
            st.success(f"✅ Criteria '{criteria_name}' saved!")
            st.session_state.current_criteria = criteria_dict
    
    st.markdown("---")

    # Stock universe input with form for Enter key submission
    with st.form("stock_screener_form", clear_on_submit=False):
        stock_universe = st.text_area(
            "Stock Universe",
            value="",
            height=100,
            placeholder="e.g., AAPL, Apple, NVDA, Microsoft, Tesla"
        )
        submitted = st.form_submit_button("🔍 Run Screener", use_container_width=True)

    if submitted and stock_universe:
        tickers = [t.strip() for t in stock_universe.split(',') if t.strip()]
        
        if not tickers:
            st.warning("⚠️ Please enter at least one ticker symbol")
        else:
            passed_stocks_analysis = {}
            failed_tickers = []
            filtered_out_tickers = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, ticker in enumerate(tickers):
                status_text.text(f"Screening {ticker}... ({i+1}/{len(tickers)})")
                try:
                    data = analyzer.get_stock_data(ticker, period="1y")
                    
                    if data and data.get('history') is not None and len(data.get('history', [])) > 0:
                        try:
                            metrics = analyzer.get_key_metrics(data)
                            
                            # Calculate technical indicators if needed for technical filters
                            hist_with_indicators = data['history']
                            if show_technical and len(hist_with_indicators) >= 20:
                                hist_with_indicators = analyzer.calculate_technical_indicators(hist_with_indicators.copy())
                            
                            # Apply filters
                            passes = True
                            filter_reasons = []
                            
                            # Check P/E Ratio (handle None/invalid values)
                            pe_ratio = metrics.get('P/E Ratio', 0)
                            if pe_ratio is None or (pe_ratio < pe_min or pe_ratio > pe_max):
                                passes = False
                                filter_reasons.append(f"P/E Ratio ({pe_ratio})")
                            
                            # Check Gross Margin
                            gross_margin = metrics.get('Gross Margin', 0)
                            if gross_margin is None or gross_margin < margin_min:
                                passes = False
                                filter_reasons.append(f"Gross Margin ({gross_margin}%)")
                            
                            # Check ROE
                            roe = metrics.get('ROE', 0)
                            if roe is None or roe < roe_min:
                                passes = False
                                filter_reasons.append(f"ROE ({roe}%)")
                            
                            # Check Profit Margin
                            profit_margin = metrics.get('Profit Margin', 0)
                            if profit_margin is None or profit_margin < profit_margin_min:
                                passes = False
                                filter_reasons.append(f"Profit Margin ({profit_margin}%)")
                            
                            # Check Revenue Growth
                            revenue_growth = metrics.get('Revenue Growth', 0)
                            if revenue_growth is None or revenue_growth < revenue_growth_min:
                                passes = False
                                filter_reasons.append(f"Revenue Growth ({revenue_growth}%)")
                            
                            # Check Earnings Growth
                            earnings_growth = metrics.get('Earnings Growth', 0)
                            if earnings_growth is None or earnings_growth < earnings_growth_min:
                                passes = False
                                filter_reasons.append(f"Earnings Growth ({earnings_growth}%)")
                            
                            # Technical Indicator Filters
                            if show_technical and len(hist_with_indicators) >= 20:
                                current_price_val = hist_with_indicators['Close'].iloc[-1]
                                
                                # RSI filters
                                if 'RSI' in hist_with_indicators.columns:
                                    rsi_val = float(hist_with_indicators['RSI'].iloc[-1]) if not pd.isna(hist_with_indicators['RSI'].iloc[-1]) else 50.0
                                    if rsi_val < rsi_min or rsi_val > rsi_max:
                                        passes = False
                                        filter_reasons.append(f"RSI ({rsi_val:.1f})")
                                    if rsi_oversold and rsi_val >= 30:
                                        passes = False
                                        filter_reasons.append(f"RSI not oversold ({rsi_val:.1f})")
                                    if rsi_overbought and rsi_val <= 70:
                                        passes = False
                                        filter_reasons.append(f"RSI not overbought ({rsi_val:.1f})")
                                
                                # MACD filters
                                if 'MACD' in hist_with_indicators.columns and 'Signal' in hist_with_indicators.columns:
                                    macd_val = float(hist_with_indicators['MACD'].iloc[-1]) if not pd.isna(hist_with_indicators['MACD'].iloc[-1]) else 0.0
                                    signal_val = float(hist_with_indicators['Signal'].iloc[-1]) if not pd.isna(hist_with_indicators['Signal'].iloc[-1]) else 0.0
                                    if macd_bullish and macd_val <= signal_val:
                                        passes = False
                                        filter_reasons.append("MACD not bullish")
                                    if macd_bearish and macd_val >= signal_val:
                                        passes = False
                                        filter_reasons.append("MACD not bearish")
                                
                                # Stochastic filters
                                if 'Stoch_K' in hist_with_indicators.columns:
                                    stoch_k = float(hist_with_indicators['Stoch_K'].iloc[-1]) if not pd.isna(hist_with_indicators['Stoch_K'].iloc[-1]) else 50.0
                                    if stoch_oversold and stoch_k >= 20:
                                        passes = False
                                        filter_reasons.append(f"Stochastic not oversold ({stoch_k:.1f})")
                                    if stoch_overbought and stoch_k <= 80:
                                        passes = False
                                        filter_reasons.append(f"Stochastic not overbought ({stoch_k:.1f})")
                                
                                # ADX filter
                                if 'ADX' in hist_with_indicators.columns:
                                    adx_val = float(hist_with_indicators['ADX'].iloc[-1]) if not pd.isna(hist_with_indicators['ADX'].iloc[-1]) else 25.0
                                    if adx_val < adx_min:
                                        passes = False
                                        filter_reasons.append(f"ADX too low ({adx_val:.1f})")
                                
                                # Moving average filters
                                if 'SMA_20' in hist_with_indicators.columns:
                                    sma_20_val = float(hist_with_indicators['SMA_20'].iloc[-1]) if not pd.isna(hist_with_indicators['SMA_20'].iloc[-1]) else current_price_val
                                    if price_above_sma20 and current_price_val <= sma_20_val:
                                        passes = False
                                        filter_reasons.append("Price not above SMA 20")
                                
                                if 'SMA_50' in hist_with_indicators.columns:
                                    sma_50_val = float(hist_with_indicators['SMA_50'].iloc[-1]) if not pd.isna(hist_with_indicators['SMA_50'].iloc[-1]) else current_price_val
                                    if price_above_sma50 and current_price_val <= sma_50_val:
                                        passes = False
                                        filter_reasons.append("Price not above SMA 50")
                                    
                                    # Golden Cross
                                    if golden_cross and 'SMA_20' in hist_with_indicators.columns:
                                        if sma_20_val <= sma_50_val:
                                            passes = False
                                            filter_reasons.append("No Golden Cross")
                            
                            # Check Overall Score (calculate once)
                            score = analyzer.calculate_score(data)
                            if score and score.get('total_score', 0) < score_min:
                                passes = False
                                filter_reasons.append(f"Score ({score.get('total_score', 0)})")
                            
                            if passes:
                                # Full analysis already calculated above
                                
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
                                filtered_out_tickers.append((ticker, filter_reasons))
                        except Exception as e:
                            # Data fetched but metrics calculation failed
                            failed_tickers.append(ticker)
                            st.warning(f"⚠️ Could not analyze {ticker}: {str(e)}")
                    else:
                        # No data returned
                        failed_tickers.append(ticker)
                except Exception as e:
                    # Failed to fetch data
                    failed_tickers.append(ticker)
                    st.warning(f"⚠️ Could not fetch data for {ticker}: {str(e)}")
                
                progress_bar.progress((i + 1) / len(tickers))
                # Small delay to avoid rate limiting
                import time
                time.sleep(0.5)
            
            status_text.empty()
            progress_bar.empty()
            
            # Show results summary
            if failed_tickers:
                st.warning(f"⚠️ Could not fetch data for: {', '.join(failed_tickers)}")
                st.info("💡 **Troubleshooting tips:**\n"
                       "- Verify ticker symbols are correct (e.g., AAPL not APPL)\n"
                       "- Some stocks may have limited data availability\n"
                       "- Try again in a few moments (Yahoo Finance may be rate limiting)\n"
                       "- Check that stocks are listed on major exchanges")
            
            if filtered_out_tickers:
                with st.expander(f"📋 {len(filtered_out_tickers)} ticker(s) filtered out (did not meet criteria)", expanded=False):
                    for ticker, reasons in filtered_out_tickers:
                        st.text(f"• {ticker}: {', '.join(reasons)}")
            
            if passed_stocks_analysis:
                st.success(f"✅ Found {len(passed_stocks_analysis)} stocks matching criteria")
                
                # Sort by score
                sorted_tickers = sorted(passed_stocks_analysis.keys(), 
                                   key=lambda t: passed_stocks_analysis[t]['score']['total_score'], 
                                   reverse=True)
                
                # Summary table
                st.subheader("Screening snapshot")
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
                st.subheader("Screened names — dashboards")
                
                # Display detailed analysis for each stock (same layout as Single / Batch)
                for ticker in sorted_tickers:
                    info = passed_stocks_analysis[ticker]
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
    st.markdown("- **Example:** `AAPL:10, Apple:5, Microsoft 3` or `AAPL 10, MSFT 5`")
    
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
                            st.plotly_chart(fig, width="stretch")
                    
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

with tab_risk:
    st.markdown("### 📊 Portfolio Risk Dashboard")
    st.write("Professional risk analysis: VaR, correlation, stress testing, and risk metrics")
    
    from utils.portfolio_risk import PortfolioRiskManager
    
    if 'risk_manager' not in st.session_state:
        st.session_state.risk_manager = PortfolioRiskManager()
    
    risk_manager = st.session_state.risk_manager
    
    st.markdown("---")
    
    # Portfolio input
    st.markdown("#### 📝 Enter Portfolio Positions")
    st.caption("Enter your portfolio positions to analyze risk metrics")
    
    num_positions = st.number_input("Number of Positions", min_value=1, max_value=50, value=3, step=1)
    
    positions = []
    for i in range(num_positions):
        col1, col2, col3 = st.columns(3)
        with col1:
            ticker = st.text_input(f"Ticker or Name {i+1}", key=f"risk_ticker_{i}", placeholder="e.g., AAPL or Apple")
        with col2:
            shares = st.number_input(f"Shares {i+1}", min_value=0.0, value=100.0, step=1.0, key=f"risk_shares_{i}")
        with col3:
            entry_price = st.number_input(f"Entry Price {i+1}", min_value=0.0, value=100.0, step=0.01, key=f"risk_entry_{i}")
        
        if ticker:
            from utils.ticker_resolver import resolve_to_ticker
            resolved = resolve_to_ticker(ticker) or ticker.upper()
            try:
                stock = yf.Ticker(resolved)
                current_price = stock.history(period="1d")['Close'].iloc[-1] if len(stock.history(period="1d")) > 0 else entry_price
            except:
                current_price = entry_price
            
            positions.append({
                'ticker': resolved,
                'shares': shares,
                'entry_price': entry_price,
                'current_price': current_price
            })
    
    if st.button("🔍 Analyze Portfolio Risk", use_container_width=True):
        if positions:
            with st.spinner("Calculating risk metrics..."):
                # Portfolio metrics
                portfolio_metrics = risk_manager.calculate_portfolio_metrics(positions)
                
                if portfolio_metrics:
                    st.markdown("---")
                    st.markdown("### 💼 Portfolio Overview")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Value", f"${portfolio_metrics['total_value']:,.2f}")
                    with col2:
                        st.metric("Total Cost", f"${portfolio_metrics['total_cost']:,.2f}")
                    with col3:
                        st.metric("Total P&L", f"${portfolio_metrics['total_pnl']:,.2f}", 
                                 f"{portfolio_metrics['total_pnl_pct']:.2f}%")
                    with col4:
                        st.metric("Positions", portfolio_metrics['num_positions'])
                    
                    # Position breakdown
                    st.markdown("---")
                    st.markdown("### 📊 Position Breakdown")
                    pos_df = pd.DataFrame(portfolio_metrics['positions'])
                    pos_df['Weight %'] = pos_df['weight'].apply(lambda x: f"{x:.2f}%")
                    pos_df['Value'] = pos_df['value'].apply(lambda x: f"${x:,.2f}")
                    pos_df['P&L'] = pos_df['pnl'].apply(lambda x: f"${x:,.2f}")
                    pos_df['P&L %'] = pos_df['pnl_pct'].apply(lambda x: f"{x:.2f}%")
                    display_df = pos_df[['ticker', 'Weight %', 'Value', 'P&L', 'P&L %']]
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
                    # VaR Calculation
                    st.markdown("---")
                    st.markdown("### ⚠️ Value at Risk (VaR)")
                    
                    var_95 = risk_manager.calculate_var(positions, confidence_level=0.95, time_horizon=1)
                    var_99 = risk_manager.calculate_var(positions, confidence_level=0.99, time_horizon=1)
                    
                    if var_95:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("#### 95% Confidence (1 Day)")
                            st.metric("VaR (Parametric)", f"${var_95['var_dollar']:,.2f}", f"{var_95['var_percentage']:.2f}%")
                            st.metric("VaR (Historical)", f"${var_95['historical_var_dollar']:,.2f}", f"{var_95['historical_var_percentage']:.2f}%")
                            st.caption("💡 Maximum expected loss with 95% confidence over 1 day")
                        
                        with col2:
                            st.markdown("#### 99% Confidence (1 Day)")
                            if var_99:
                                st.metric("VaR (Parametric)", f"${var_99['var_dollar']:,.2f}", f"{var_99['var_percentage']:.2f}%")
                                st.metric("VaR (Historical)", f"${var_99['historical_var_dollar']:,.2f}", f"{var_99['historical_var_percentage']:.2f}%")
                                st.caption("💡 Maximum expected loss with 99% confidence over 1 day")
                        
                        st.info(f"📊 Portfolio Volatility: {var_95['portfolio_volatility']:.2f}% (Annualized)")
                    
                    # Correlation Matrix
                    st.markdown("---")
                    st.markdown("### 🔗 Correlation Analysis")
                    tickers = [p['ticker'] for p in positions]
                    corr_matrix = risk_manager.calculate_correlation_matrix(tickers)
                    
                    if corr_matrix is not None and not corr_matrix.empty:
                        st.dataframe(corr_matrix.style.background_gradient(cmap='RdYlGn', vmin=-1, vmax=1).format("{:.2f}"),
                                   use_container_width=True)
                        st.caption("💡 Correlation ranges from -1 (inverse) to +1 (perfect correlation). Lower correlation = better diversification.")
                    
                    # Beta Analysis
                    st.markdown("---")
                    st.markdown("### 📈 Beta Analysis")
                    beta_analysis = risk_manager.calculate_portfolio_beta(positions)
                    
                    if beta_analysis:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Portfolio Beta", f"{beta_analysis['beta']:.2f}")
                            st.caption(f"vs {beta_analysis['benchmark_ticker']}")
                        with col2:
                            st.metric("Alpha", f"{beta_analysis['alpha']:.2f}%")
                            st.caption("Risk-adjusted return")
                        with col3:
                            st.metric("Portfolio Volatility", f"{beta_analysis['portfolio_volatility']:.2f}%")
                            st.caption("Annualized")
                    
                    # Sharpe Ratio
                    st.markdown("---")
                    st.markdown("### 📊 Risk-Adjusted Returns")
                    sharpe_metrics = risk_manager.calculate_sharpe_ratio(positions)
                    
                    if sharpe_metrics:
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Sharpe Ratio", f"{sharpe_metrics['sharpe_ratio']:.2f}")
                            st.caption("Higher is better (>1 is good)")
                        with col2:
                            st.metric("Sortino Ratio", f"{sharpe_metrics['sortino_ratio']:.2f}")
                            st.caption("Downside risk adjusted")
                        with col3:
                            st.metric("Annual Return", f"{sharpe_metrics['annualized_return']:.2f}%")
                        with col4:
                            st.metric("Annual Volatility", f"{sharpe_metrics['annualized_volatility']:.2f}%")
                    
                    # Stress Testing
                    st.markdown("---")
                    st.markdown("### 💥 Stress Testing")
                    scenarios = {
                        'Market Crash (-20%)': -0.20,
                        'Correction (-10%)': -0.10,
                        'Rally (+10%)': 0.10,
                        'Bull Run (+20%)': 0.20
                    }
                    
                    stress_results = risk_manager.stress_test(positions, scenarios)
                    
                    if stress_results:
                        stress_df = pd.DataFrame([
                            {
                                'Scenario': name,
                                'Stressed Value': f"${r['stressed_value']:,.2f}",
                                'P&L Change': f"${r['pnl_change']:,.2f}",
                                'P&L Change %': f"{r['pnl_change_pct']:.2f}%"
                            }
                            for name, r in stress_results.items()
                        ])
                        st.dataframe(stress_df, use_container_width=True, hide_index=True)
                        st.caption("💡 Impact of different market scenarios on portfolio value")
        else:
            st.warning("⚠️ Please enter at least one position")

render_footer()
