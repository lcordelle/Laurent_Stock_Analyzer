"""
Outcome Sections Component
Independent, full-screen sections with focused visibility using tabs
"""

import streamlit as st
import pandas as pd


def _safe_float_format(value, format_str="{:.2f}", default="N/A"):
    """Safely convert and format a value to float"""
    if value is None:
        return default
    try:
        if isinstance(value, str):
            # Try to convert string to float
            value = float(value)
        elif not isinstance(value, (int, float)):
            return default
        return format_str.format(value)
    except (ValueError, TypeError):
        return default

def render_outcome_sections(ticker, data, metrics, score, forecast, intrinsic_value, 
                            news_articles, ratings_result, trading_signals):
    """
    Render independent, full-screen sections using tabs
    Each section opens independently and closes others for full visibility
    """
    
    # Main navigation using tabs (most reliable in Streamlit)
    st.markdown("### 📊 Analysis Dashboard")
    st.markdown("Select a section to view full-screen analysis:")
    st.markdown("---")
    
    # Use tabs for main navigation
    section_options = {
        "📰 Top News": "news",
        "📊 Analyst Insights": "analyst",
        "⭐ Overall Score": "score",
        "🎯 Forecast Analysis": "forecast"
    }
    
    # Create tabs - Streamlit automatically handles which tab is active
    tab_labels = list(section_options.keys())
    tabs = st.tabs(tab_labels)
    
    # Render content in each tab (only active tab content is shown)
    for tab, (label, value) in zip(tabs, section_options.items()):
        with tab:
            if value == "news":
                render_news_section_fullscreen(ticker, news_articles)
            elif value == "analyst":
                render_analyst_section_fullscreen(ticker, data, ratings_result, intrinsic_value, metrics)
            elif value == "score":
                render_score_section_fullscreen(ticker, score, metrics, forecast)
            elif value == "forecast":
                render_forecast_analysis_fullscreen(ticker, data, metrics, score, intrinsic_value, trading_signals)


def render_news_section_fullscreen(ticker, news_articles):
    """Full-screen news section"""
    st.markdown("### 📰 Top News Articles")
    st.markdown("---")
    
    if news_articles and len(news_articles) > 0:
        from datetime import datetime
        
        for idx, article in enumerate(news_articles, 1):
            with st.container():
                st.markdown(f"#### {idx}. {article.get('title', 'No title')}")
                
                col_info, col_link = st.columns([3, 1])
                
                with col_info:
                    publisher = article.get('publisher', 'Unknown')
                    published = article.get('published')
                    if published:
                        time_ago = datetime.now() - published if isinstance(published, datetime) else None
                        if time_ago:
                            if time_ago.days > 0:
                                time_str = f"{time_ago.days}d ago"
                            elif time_ago.seconds > 3600:
                                time_str = f"{time_ago.seconds // 3600}h ago"
                            else:
                                time_str = f"{time_ago.seconds // 60}m ago"
                        else:
                            time_str = "Recently"
                    else:
                        time_str = "Recently"
                    
                    st.markdown(f"**📅 {time_str}** | **📰 {publisher}**")
                
                with col_link:
                    if article.get('link'):
                        st.markdown(f"[🔗 Read Full Article →]({article.get('link')})", unsafe_allow_html=True)
                
                if article.get('summary'):
                    summary = article.get('summary', '')
                    st.markdown(f"<p style='color: var(--text-secondary); line-height: 1.6;'>{summary}</p>", unsafe_allow_html=True)
                
                if idx < len(news_articles):
                    st.markdown("---")
    else:
        st.warning("📰 No recent news articles available for this stock.")


def render_analyst_section_fullscreen(ticker, data, ratings_result, intrinsic_value, metrics):
    """Full-screen analyst insights section"""
    st.markdown("### 📊 Analyst Insights, Trends & Price Probabilities")
    st.markdown("---")
    
    from components.styling import render_analyst_ranking_panel
    current_price = metrics.get('Current Price', 0) if metrics else 0
    
    if ratings_result:
        render_analyst_ranking_panel(ratings_result, current_price, ticker, data, intrinsic_value)
    else:
        st.warning("⚠️ Analyst ratings not available for this stock.")


def render_score_section_fullscreen(ticker, score, metrics, forecast):
    """Full-screen overall score section"""
    st.markdown("### ⭐ Overall Score & Rating")
    st.markdown("---")
    
    # Score display
    col1, col2, col3 = st.columns(3)
    
    with col1:
        score_value = score.get('total_score', 0)
        score_color = '#00ff88' if score_value >= 70 else '#ffaa00' if score_value >= 50 else '#ff3366'
        st.markdown(f"""
        <div style="background: var(--bg-secondary); padding: 2rem; border-radius: 12px; border: 2px solid {score_color}; text-align: center;">
            <h1 style="color: {score_color}; margin: 0; font-size: 4rem; font-weight: bold;">{score_value}</h1>
            <p style="color: var(--text-secondary); margin: 0.5rem 0 0 0; font-size: 1.2rem;">/ 100</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        current_price = _safe_float_format(metrics.get('Current Price', 0), "${:.2f}", "$0.00")
        st.metric("Current Price", current_price)
        if forecast:
            forecast_price = _safe_float_format(forecast.get('forecast_price', 0), "${:.2f}", "$0.00")
            forecast_pct = _safe_float_format(forecast.get('forecast_change_pct', 0), "{:+.2f}%", "N/A")
            st.metric("Forecast Price", forecast_price, delta=forecast_pct)
    
    with col3:
        market_cap = metrics.get('Market Cap', 0)
        try:
            if isinstance(market_cap, str):
                market_cap = float(market_cap)
            if isinstance(market_cap, (int, float)) and market_cap > 0:
                if market_cap > 1e9:
                    st.metric("Market Cap", f"${market_cap/1e9:.2f}B")
                elif market_cap > 1e6:
                    st.metric("Market Cap", f"${market_cap/1e6:.2f}M")
                else:
                    st.metric("Market Cap", f"${market_cap:.2f}")
            else:
                st.metric("Market Cap", "N/A")
        except (ValueError, TypeError):
            st.metric("Market Cap", "N/A")
        if forecast:
            probability = _safe_float_format(forecast.get('probability', 0), "{:.1f}%", "N/A")
            st.metric("Probability", probability)
    
    st.markdown("---")
    
    # Score breakdown
    from utils.visualizations import create_score_breakdown_table
    create_score_breakdown_table(score, forecast)


def render_forecast_analysis_fullscreen(ticker, data, metrics, score, intrinsic_value, trading_signals):
    """Full-screen forecast analysis with independent subsections"""
    st.markdown("### 🎯 Price Forecast Analysis")
    st.markdown("---")
    
    # Subsection navigation using tabs
    subsection_options = {
        "📈 Charts": "charts",
        "🎯 Trading Signals": "signals",
        "📊 Analysis": "analysis",
        "🔗 Peers": "peers"
    }
    
    # Use tabs for subsections
    sub_tabs = st.tabs(list(subsection_options.keys()))
    
    # Render content in each subsection tab
    for sub_tab, (label, value) in zip(sub_tabs, subsection_options.items()):
        with sub_tab:
            if value == "charts":
                render_charts_subsection_fullscreen(data, metrics, intrinsic_value, ticker, trading_signals)
            elif value == "signals":
                render_signals_subsection_fullscreen(data, metrics, score, intrinsic_value, trading_signals)
            elif value == "analysis":
                render_analysis_subsection_fullscreen(ticker, data, metrics, score)
            elif value == "peers":
                render_peers_subsection_fullscreen(ticker, data, metrics, score)


def render_charts_subsection_fullscreen(data, metrics, intrinsic_value, ticker="", trading_signals=None):
    """Full-screen charts subsection"""
    st.markdown("#### 📈 Price & Volume Charts")
    
    from utils.visualizations import create_price_chart, create_volume_chart
    
    if data and data.get('history') is not None and len(data.get('history', [])) > 0:
        price_chart = create_price_chart(data, intrinsic_value=intrinsic_value, metrics=metrics)
        if price_chart:
            st.plotly_chart(price_chart, use_container_width=True, height=600, config={"displayModeBar": True, "displaylogo": False})
            st.caption("💡 **Chart Features:** Fair Value Tunnel (blue shaded area), VWAP (purple), Support/Resistance (green/red), Pivot Points (gray/orange), Moving Averages, Bollinger Bands, Entry/Exit Signals")
        
        st.markdown("---")
        
        volume_chart = create_volume_chart(data.get('history'), ticker)
        if volume_chart:
            st.plotly_chart(volume_chart, use_container_width=True, height=400, config={"displayModeBar": True, "displaylogo": False})
    else:
        st.warning("⚠️ Chart data not available.")


def render_signals_subsection_fullscreen(data, metrics, score, intrinsic_value, trading_signals):
    """Full-screen trading signals subsection"""
    st.markdown("#### 🎯 Trading Signals")
    
    from utils.visualizations import create_trading_signals_chart
    
    # Get analyzer from session state if available
    from utils.stock_analyzer import StockAnalyzer
    analyzer = st.session_state.get('analyzer', StockAnalyzer())
    signals_result = create_trading_signals_chart(data, intrinsic_value=intrinsic_value, metrics=metrics, score=score, analyzer=analyzer)
    
    if signals_result:
        _, trading_signals = signals_result
        current_price = metrics.get('Current Price', 0) if metrics else 0
        
        # Summary table: recommendation + key levels
        is_buy = len(trading_signals.get('buy_signals', [])) > 0
        is_sell = len(trading_signals.get('sell_signals', [])) > 0
        entry_price = current_price
        entry_reason = "Current price"
        if is_buy and trading_signals.get('buy_signals'):
            b = min(trading_signals['buy_signals'], key=lambda x: x['price'])
            entry_price, entry_reason = b['price'], b.get('type', 'Buy Signal')
        elif is_sell and trading_signals.get('sell_signals'):
            b = max(trading_signals['sell_signals'], key=lambda x: x['price'])
            entry_price, entry_reason = b['price'], b.get('type', 'Sell Signal')
        sl_price = trading_signals.get('stop_loss', {}).get('price') if trading_signals.get('stop_loss') else None
        tp_list = trading_signals.get('take_profit', [])
        # Fallback when no stop_loss/take_profit from signals (HOLD or SELL without computed levels)
        if not sl_price and entry_price:
            sl_price = entry_price * 1.05 if is_sell else entry_price * 0.95  # SELL: SL above entry; BUY/HOLD: SL below
        if not tp_list and entry_price:
            if is_sell:
                tp_list = [
                    {'price': entry_price * 0.90, 'label': 'TP1 -10%'},
                    {'price': entry_price * 0.80, 'label': 'TP2 -20%'},
                    {'price': intrinsic_value if intrinsic_value and intrinsic_value < entry_price else entry_price * 0.70, 'label': 'TP3'}
                ]
            else:
                tp_list = [
                    {'price': entry_price * 1.10, 'label': 'TP1 +10%'},
                    {'price': entry_price * 1.20, 'label': 'TP2 +20%'},
                    {'price': intrinsic_value if intrinsic_value and intrinsic_value > entry_price else entry_price * 1.30, 'label': 'TP3'}
                ]
        tp1 = tp_list[0]['price'] if len(tp_list) > 0 else None
        tp2 = tp_list[1]['price'] if len(tp_list) > 1 else None
        tp3 = tp_list[2]['price'] if len(tp_list) > 2 else None
        risk_pct = abs((entry_price - sl_price) / entry_price * 100) if entry_price and sl_price else None
        best_tp = (max(tp_list, key=lambda x: x['price'])['price'] if is_buy else min(tp_list, key=lambda x: x['price'])['price']) if tp_list else None
        reward_pct = abs((best_tp - entry_price) / entry_price * 100) if entry_price and best_tp else None
        rec = "BUY" if is_buy else "SELL" if is_sell else "HOLD"
        rec_color = "#10b981" if rec == "BUY" else "#ef4444" if rec == "SELL" else "#f59e0b"
        rec_bg = "rgba(16, 185, 129, 0.15)" if rec == "BUY" else "rgba(239, 68, 68, 0.15)" if rec == "SELL" else "rgba(245, 158, 11, 0.15)"
        conf = trading_signals.get('confidence_score', 0)
        conf_level = trading_signals.get('confidence_level', 'Low')
        st.markdown(f"""<div style="background: {rec_bg}; border: 2px solid {rec_color}; border-radius: 12px; padding: 1rem 1.5rem; margin-bottom: 1rem;">
            <p style="margin: 0 0 0.5rem 0; font-size: 0.75rem; text-transform: uppercase; color: #64748b;">Recommendation</p>
            <p style="margin: 0; font-size: 1.75rem; font-weight: 700; color: {rec_color};">{rec}</p>
            <p style="margin: 0.25rem 0 0 0; font-size: 0.875rem; color: #475569;">{entry_reason} • Confidence: {conf:.0f}/100 ({conf_level})</p>
        </div>
        <table style="width: 100%; border-collapse: collapse; font-size: 0.9375rem; margin-bottom: 1.5rem;">
            <thead><tr style="background: #f8fafc; border-bottom: 2px solid #e2e8f0;">
                <th style="text-align: left; padding: 0.75rem; color: #0f172a;">Metric</th>
                <th style="text-align: right; padding: 0.75rem; color: #0f172a;">Value</th>
            </tr></thead>
            <tbody>
                <tr style="border-bottom: 1px solid #e2e8f0;"><td style="padding: 0.75rem; color: #475569;">Entry</td><td style="padding: 0.75rem; text-align: right; font-weight: 600;">{f"${entry_price:.2f}" if entry_price else "—"}</td></tr>
                <tr style="border-bottom: 1px solid #e2e8f0;"><td style="padding: 0.75rem; color: #475569;">Stop Loss</td><td style="padding: 0.75rem; text-align: right; font-weight: 600; color: #ef4444;">{f"${sl_price:.2f}" if sl_price else "—"}</td></tr>
                <tr style="border-bottom: 1px solid #e2e8f0;"><td style="padding: 0.75rem; color: #475569;">Take Profit 1</td><td style="padding: 0.75rem; text-align: right; font-weight: 600; color: #10b981;">{f"${tp1:.2f}" if tp1 else "—"}</td></tr>
                <tr style="border-bottom: 1px solid #e2e8f0;"><td style="padding: 0.75rem; color: #475569;">Take Profit 2</td><td style="padding: 0.75rem; text-align: right; font-weight: 600; color: #10b981;">{f"${tp2:.2f}" if tp2 else "—"}</td></tr>
                <tr style="border-bottom: 1px solid #e2e8f0;"><td style="padding: 0.75rem; color: #475569;">Take Profit 3</td><td style="padding: 0.75rem; text-align: right; font-weight: 600; color: #10b981;">{f"${tp3:.2f}" if tp3 else "—"}</td></tr>
                <tr style="border-bottom: 1px solid #e2e8f0;"><td style="padding: 0.75rem; color: #475569;">Risk %</td><td style="padding: 0.75rem; text-align: right; font-weight: 600; color: #ef4444;">{f"{risk_pct:.1f}%" if risk_pct is not None else "—"}</td></tr>
                <tr><td style="padding: 0.75rem; color: #475569;">Reward %</td><td style="padding: 0.75rem; text-align: right; font-weight: 600; color: #10b981;">{f"{reward_pct:.1f}%" if reward_pct is not None else "—"}</td></tr>
            </tbody>
        </table>""", unsafe_allow_html=True)
        
        # Multi-timeframe analysis (optional, in expander)
        if trading_signals.get('multi_timeframe'):
            with st.expander("📊 Multi-Timeframe Analysis", expanded=False):
                mtf = trading_signals['multi_timeframe']
                for tf_name, tf_data in mtf.items():
                    trend_emoji = "📈" if tf_data.get('trend') == 'Bullish' else "📉" if tf_data.get('trend') == 'Bearish' else "➡️"
                    st.markdown(f"""
                    <div style="background: #f8fafc; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem; border-left: 4px solid #3b82f6;">
                        <strong>{tf_name}:</strong> {trend_emoji} {tf_data.get('trend', 'Neutral')}<br>
                        <small>RSI: {tf_data.get('rsi', 0):.1f} | MACD: {tf_data.get('macd_signal', 'Neutral')} | ADX: {tf_data.get('adx', 0):.1f}</small>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Trading Strategy Chart (single main chart)
        st.markdown("---")
        st.markdown("#### 📊 Trading Strategy Visualization")
        st.markdown("**Visual guide showing when to buy/sell with entry, stop loss, and take profit targets**")
        
        from utils.trading_strategy_chart import create_trading_strategy_chart
        strategy_chart = create_trading_strategy_chart(
            data, 
            trading_signals=trading_signals, 
            intrinsic_value=intrinsic_value, 
            metrics=metrics, 
            score=score
        )
        
        if strategy_chart:
            st.plotly_chart(strategy_chart, use_container_width=True, height=700, config={"displayModeBar": True, "displaylogo": False})
            st.caption("""
            **Chart Features:**
            - 🔵 **Entry Point:** Recommended buy/sell price with rationale
            - 🔴 **Stop Loss (SL):** Risk management level (red zone = potential loss)
            - 🟢 **Take Profit Targets (TP1, TP2, TP3):** Profit targets (green zone = potential profit)
            - **Risk/Reward Ratio:** Visual comparison of risk vs reward
            - **Rationale Box:** Data-driven explanation of the strategy
            """)
        else:
            st.info("Trading strategy chart not available. Ensure trading signals are calculated.")
    else:
        st.warning("⚠️ Trading signals not available.")


def render_analysis_subsection_fullscreen(ticker, data, metrics, score):
    """Full-screen analysis subsection"""
    st.markdown("#### 📊 Comprehensive Analysis")
    
    from utils.metric_display import display_enhanced_metric
    
    # Use expanders for organization
    with st.expander("📍 Key Metrics & Valuation", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 📍 Price Information")
            st.markdown(f"**Today's Range:** {metrics.get('Today Range', 'N/A')}")
            st.markdown(f"**52 Week Range:** {metrics.get('52 Week Range', 'N/A')}")
            if 'Target Price' in metrics:
                target_price = _safe_float_format(metrics['Target Price'], "${:.2f}")
                display_enhanced_metric("Target Price", target_price, metric_name="Target Price")
            if 'Beta' in metrics:
                beta = _safe_float_format(metrics['Beta'], "{:.2f}")
                display_enhanced_metric("Beta", beta, metric_name="Beta")
        
        with col2:
            st.markdown("### 📊 Valuation")
            if 'P/E Ratio' in metrics:
                pe_ratio = _safe_float_format(metrics['P/E Ratio'], "{:.2f}")
                display_enhanced_metric("P/E Ratio", pe_ratio, metric_name="P/E Ratio")
            if 'Forward P/E' in metrics:
                forward_pe = _safe_float_format(metrics['Forward P/E'], "{:.2f}")
                display_enhanced_metric("Forward P/E", forward_pe, metric_name="Forward P/E")
            if 'PEG Ratio' in metrics:
                peg_ratio = _safe_float_format(metrics['PEG Ratio'], "{:.2f}")
                display_enhanced_metric("PEG Ratio", peg_ratio, metric_name="PEG Ratio")
            if 'Price to Book' in metrics:
                price_book = _safe_float_format(metrics['Price to Book'], "{:.2f}")
                display_enhanced_metric("Price/Book", price_book, metric_name="Price to Book")
        
        with col3:
            st.markdown("### 💰 Financial Health")
            if 'Current Price' in metrics:
                current_price = _safe_float_format(metrics['Current Price'], "${:.2f}")
                st.metric("Current Price", current_price)
            if 'Market Cap' in metrics:
                market_cap = metrics['Market Cap']
                try:
                    if isinstance(market_cap, str):
                        market_cap = float(market_cap)
                    if isinstance(market_cap, (int, float)) and market_cap > 0:
                        if market_cap > 1e9:
                            st.metric("Market Cap", f"${market_cap/1e9:.2f}B")
                        elif market_cap > 1e6:
                            st.metric("Market Cap", f"${market_cap/1e6:.2f}M")
                        else:
                            st.metric("Market Cap", f"${market_cap:.2f}")
                except (ValueError, TypeError):
                    st.metric("Market Cap", "N/A")
    
    st.info("💡 Full comprehensive analysis with all metrics, technical indicators, risk analysis, and valuation models. Expand sections above for detailed information.")


def render_peers_subsection_fullscreen(ticker, data, metrics, score):
    """Full-screen peers subsection"""
    st.markdown("#### 🔗 Peer Comparison")
    
    from utils.peer_benchmark import PeerBenchmark
    
    peer_bench = PeerBenchmark()
    try:
        # Get sector peers
        sector = data.get('info', {}).get('sector', '')
        peers = peer_bench.get_sector_peers(ticker, sector)
        
        if not peers:
            st.info("🔗 No sector peers found for comparison.")
            return
        
        # Benchmark against peers
        benchmark_result = peer_bench.benchmark_against_peers(ticker, metrics, score, peers)
        
        if benchmark_result and benchmark_result.get('benchmark_summary'):
            summary = benchmark_result['benchmark_summary']
            
            # Display summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Peer Rank", f"{summary['position']}/{summary['total_peers']}")
            with col2:
                st.metric("Percentile", f"{summary['percentile']:.0f}th")
            with col3:
                st.metric("Better Than", summary['better_than'])
            
            st.markdown("---")
        
        # Display peer comparison table
        if benchmark_result and benchmark_result.get('peer_comparison') is not None:
            comparison_df = benchmark_result['peer_comparison']
            
            # Select relevant columns for display
            display_columns = ['ticker', 'score', 'pe_ratio', 'roe', 'revenue_growth', 'profit_margin', 'current_price']
            available_columns = [col for col in display_columns if col in comparison_df.columns]
            
            if available_columns:
                display_df = comparison_df[available_columns].copy()
                
                # Rename columns for better display
                column_mapping = {
                    'ticker': 'Ticker',
                    'score': 'Score',
                    'pe_ratio': 'P/E Ratio',
                    'roe': 'ROE (%)',
                    'revenue_growth': 'Revenue Growth (%)',
                    'profit_margin': 'Profit Margin (%)',
                    'current_price': 'Price ($)'
                }
                display_df.rename(columns=column_mapping, inplace=True)
                
                # Format numeric columns
                if 'P/E Ratio' in display_df.columns:
                    display_df['P/E Ratio'] = display_df['P/E Ratio'].apply(lambda x: f"{x:.2f}" if pd.notna(x) and x != 0 else "N/A")
                if 'ROE (%)' in display_df.columns:
                    display_df['ROE (%)'] = display_df['ROE (%)'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
                if 'Revenue Growth (%)' in display_df.columns:
                    display_df['Revenue Growth (%)'] = display_df['Revenue Growth (%)'].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "N/A")
                if 'Profit Margin (%)' in display_df.columns:
                    display_df['Profit Margin (%)'] = display_df['Profit Margin (%)'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
                if 'Price ($)' in display_df.columns:
                    display_df['Price ($)'] = display_df['Price ($)'].apply(lambda x: f"${x:.2f}" if pd.notna(x) else "N/A")
                if 'Score' in display_df.columns:
                    display_df['Score'] = display_df['Score'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")
                
                # Highlight the main ticker
                st.markdown("**Peer Comparison Table**")
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # Add note about main ticker
                st.caption(f"💡 **{ticker}** is highlighted in the comparison above. Lower rank = better performance.")
            else:
                st.info("🔗 Peer comparison data structure is incomplete.")
        else:
            st.info("🔗 Peer comparison data not available.")
            
    except Exception as e:
        st.warning(f"⚠️ Could not load peer data: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
