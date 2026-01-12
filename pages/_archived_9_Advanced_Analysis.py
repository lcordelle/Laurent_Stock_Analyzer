"""
Advanced Analysis Page
Sector comparison, peer analysis, and advanced financial metrics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.advanced_financials import AdvancedFinancials
from utils.stock_analyzer import StockAnalyzer
from components.styling import apply_platform_theme, render_header, render_footer
from components.navigation import render_navigation

# Page configuration
st.set_page_config(
    page_title="Advanced Analysis",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply theme and navigation
apply_platform_theme()
render_navigation()

# Initialize
if 'advanced_financials' not in st.session_state:
    st.session_state.advanced_financials = AdvancedFinancials()

if 'analyzer' not in st.session_state:
    st.session_state.analyzer = StockAnalyzer()

advanced = st.session_state.advanced_financials
analyzer = st.session_state.analyzer

# Header
render_header("🔬 Advanced Analysis", "Sector comparison, peer analysis, and advanced financial metrics")

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔗 Peer Comparison", "💰 Dividends", "📊 Insider Trading", 
    "📈 Analyst Data", "🌍 ESG & More"
])

with tab1:
    st.markdown("### 🔗 Sector Peer Comparison")
    
    peer_ticker = st.text_input("Enter Stock Ticker:", value="AAPL", key="peer_ticker").upper()
    
    if st.button("Compare with Peers", key="compare_peers"):
        with st.spinner(f"Finding peers and comparing {peer_ticker}..."):
            peers = advanced.get_sector_peers(peer_ticker)
            
            if peers:
                st.success(f"Found {len(peers)} sector peers for comparison")
                
                # Analyze main stock
                main_data = analyzer.get_stock_data(peer_ticker, period="1y")
                if main_data:
                    main_metrics = analyzer.get_key_metrics(main_data)
                    main_score = analyzer.calculate_score(main_data)
                else:
                    main_metrics = {}
                    main_score = {'total_score': 0}
                
                # Analyze peers
                peer_comparison = []
                peer_comparison.append({
                    'Ticker': peer_ticker,
                    'Company': main_data['info'].get('longName', peer_ticker) if main_data else peer_ticker,
                    'Score': main_score['total_score'],
                    'Price': main_metrics.get('Current Price', 0),
                    'P/E Ratio': main_metrics.get('P/E Ratio', 0),
                    'Market Cap': main_metrics.get('Market Cap', 0),
                    'ROE': main_metrics.get('ROE', 0),
                    'Gross Margin': main_metrics.get('Gross Margin', 0),
                })
                
                for peer_tick in peers[:5]:  # Limit to 5 peers
                    peer_data = analyzer.get_stock_data(peer_tick, period="1y")
                    if peer_data:
                        peer_metrics = analyzer.get_key_metrics(peer_data)
                        peer_score = analyzer.calculate_score(peer_data)
                        
                        peer_comparison.append({
                            'Ticker': peer_tick,
                            'Company': peer_data['info'].get('longName', peer_tick),
                            'Score': peer_score['total_score'],
                            'Price': peer_metrics['Current Price'],
                            'P/E Ratio': peer_metrics['P/E Ratio'],
                            'Market Cap': peer_metrics['Market Cap'],
                            'ROE': peer_metrics['ROE'],
                            'Gross Margin': peer_metrics['Gross Margin'],
                        })
                
                if len(peer_comparison) > 1:
                    comparison_df = pd.DataFrame(peer_comparison)
                    comparison_df = comparison_df.sort_values('Score', ascending=False)
                    
                    st.dataframe(
                        comparison_df.style.background_gradient(subset=['Score'], cmap='RdYlGn', vmin=0, vmax=100)
                        .format({
                            'Price': '${:.2f}',
                            'P/E Ratio': '{:.2f}',
                            'Market Cap': '${:,.0f}',
                            'ROE': '{:.2f}%',
                            'Gross Margin': '{:.2f}%'
                        }),
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Visualization
                    fig = px.bar(comparison_df, x='Ticker', y='Score',
                               title='Peer Score Comparison',
                               color='Score',
                               color_continuous_scale='RdYlGn')
                    fig.update_layout(height=400, template='plotly_white')
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"Could not find sector peers for {peer_ticker}")

with tab2:
    st.markdown("### 💰 Dividend Analysis")
    
    div_ticker = st.text_input("Enter Stock Ticker:", value="AAPL", key="div_ticker").upper()
    
    if st.button("Get Dividend Data", key="get_dividend"):
        with st.spinner(f"Fetching dividend data for {div_ticker}..."):
            div_data = advanced.get_dividend_data(div_ticker)
            
            if div_data:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("#### 💵 Current Dividend")
                    st.metric("Dividend Yield", f"{div_data.get('dividend_yield', 0):.2f}%")
                    st.metric("Annual Dividend", f"${div_data.get('annual_dividend', 0):.2f}")
                
                with col2:
                    st.markdown("#### 📊 Dividend Metrics")
                    st.metric("Payout Ratio", f"{div_data.get('payout_ratio', 0):.2f}%")
                    if div_data.get('ex_dividend_date'):
                        st.metric("Ex-Dividend Date", str(div_data['ex_dividend_date']))
                
                with col3:
                    st.markdown("#### 📈 Growth")
                    growth = div_data.get('dividend_growth', 0)
                    growth_color = "normal" if growth > 0 else "inverse"
                    st.metric("Dividend Growth", f"{growth:+.2f}%", delta=f"{growth:+.2f}%")
                
                # Dividend history
                if div_data.get('dividend_history'):
                    st.markdown("---")
                    st.markdown("#### 📅 Recent Dividend History")
                    hist_df = pd.DataFrame(list(div_data['dividend_history'].items()), 
                                         columns=['Date', 'Dividend'])
                    hist_df['Date'] = pd.to_datetime(hist_df['Date'])
                    hist_df = hist_df.sort_values('Date', ascending=False)
                    
                    st.dataframe(
                        hist_df.style.format({'Dividend': '${:.2f}'}),
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Chart
                    fig = px.bar(hist_df, x='Date', y='Dividend',
                               title='Dividend History',
                               color='Dividend',
                               color_continuous_scale='Greens')
                    fig.update_layout(height=400, template='plotly_white')
                    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown("### 📊 Insider Trading & Institutional Holdings")
    
    insider_ticker = st.text_input("Enter Stock Ticker:", value="AAPL", key="insider_ticker").upper()
    
    if st.button("Get Insider Data", key="get_insider"):
        with st.spinner(f"Fetching insider data for {insider_ticker}..."):
            # Insider transactions
            insider_trans = advanced.get_insider_transactions(insider_ticker)
            
            if len(insider_trans) > 0:
                st.markdown("#### 👥 Insider Transactions")
                st.dataframe(insider_trans.head(10), use_container_width=True, hide_index=True)
            else:
                st.info("No recent insider transactions data available")
            
            st.markdown("---")
            
            # Institutional holdings
            institutional = advanced.get_institutional_holdings(insider_ticker)
            
            if len(institutional) > 0:
                st.markdown("#### 🏦 Institutional Holdings")
                st.dataframe(institutional.head(15), use_container_width=True, hide_index=True)
            else:
                st.info("Institutional holdings data not available")

with tab4:
    st.markdown("### 📈 Analyst Data & Estimates")
    
    analyst_ticker = st.text_input("Enter Stock Ticker:", value="NVDA", key="analyst_ticker").upper()
    
    if st.button("Get Analyst Data", key="get_analyst"):
        with st.spinner(f"Fetching analyst data for {analyst_ticker}..."):
            analyst_data = advanced.get_analyst_data(analyst_ticker)
            
            if analyst_data:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 📊 Current Recommendations")
                    st.metric("Recommendation", analyst_data.get('recommendation', 'N/A').upper())
                    st.metric("Number of Analysts", analyst_data.get('number_of_analysts', 0))
                    st.metric("Recommendation Mean", f"{analyst_data.get('recommendation_mean', 0):.2f}")
                
                with col2:
                    st.markdown("#### 🎯 Price Targets")
                    current = analyst_data.get('current_price', 0)
                    target = analyst_data.get('target_price', 0)
                    upside = analyst_data.get('upside_potential', 0)
                    
                    st.metric("Current Price", f"${current:.2f}")
                    st.metric("Target Price", f"${target:.2f}")
                    st.metric("Upside Potential", f"{upside:+.2f}%", 
                             delta=f"{upside:+.2f}%")
                
                # Target range
                if analyst_data.get('target_high') and analyst_data.get('target_low'):
                    st.markdown("---")
                    st.markdown("#### 📊 Target Price Range")
                    target_df = pd.DataFrame([
                        {'Metric': 'Target Low', 'Price': analyst_data['target_low']},
                        {'Metric': 'Target Mean', 'Price': analyst_data['target_price']},
                        {'Metric': 'Target High', 'Price': analyst_data['target_high']},
                        {'Metric': 'Current Price', 'Price': current},
                    ])
                    
                    fig = px.bar(target_df, x='Metric', y='Price',
                               title='Analyst Price Targets',
                               color='Price',
                               color_continuous_scale='RdYlGn')
                    fig.update_layout(height=400, template='plotly_white')
                    st.plotly_chart(fig, use_container_width=True)
                
                # Short interest
                st.markdown("---")
                st.markdown("#### 📉 Short Interest")
                short_data = advanced.get_short_interest(analyst_ticker)
                if short_data:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Short Ratio", f"{short_data.get('short_ratio', 0):.2f}")
                    with col2:
                        st.metric("Short % of Float", f"{short_data.get('short_percent_of_float', 0):.2f}%")
                    with col3:
                        change = short_data.get('short_percent_change', 0)
                        st.metric("Short Change", f"{change:+.2f}%")

with tab5:
    st.markdown("### 🌍 ESG Scores & Additional Metrics")
    
    esg_ticker = st.text_input("Enter Stock Ticker:", value="AAPL", key="esg_ticker").upper()
    
    if st.button("Get ESG Data", key="get_esg"):
        with st.spinner(f"Fetching ESG data for {esg_ticker}..."):
            esg_data = advanced.get_esg_score(esg_ticker)
            
            if esg_data and any(esg_data.values()):
                st.markdown("#### 🌍 ESG Scores")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    env_score = esg_data.get('environment_score')
                    if env_score:
                        st.metric("Environment", f"{env_score:.0f}")
                
                with col2:
                    social_score = esg_data.get('social_score')
                    if social_score:
                        st.metric("Social", f"{social_score:.0f}")
                
                with col3:
                    gov_score = esg_data.get('governance_score')
                    if gov_score:
                        st.metric("Governance", f"{gov_score:.0f}")
                
                with col4:
                    total_esg = esg_data.get('total_esg_score')
                    if total_esg:
                        st.metric("Total ESG", f"{total_esg:.0f}")
                
                # ESG Chart
                if total_esg:
                    esg_components = pd.DataFrame([
                        {'Component': 'Environment', 'Score': env_score or 0},
                        {'Component': 'Social', 'Score': social_score or 0},
                        {'Component': 'Governance', 'Score': gov_score or 0},
                    ])
                    
                    fig = px.bar(esg_components, x='Component', y='Score',
                               title='ESG Component Scores',
                               color='Score',
                               color_continuous_scale='Greens')
                    fig.update_layout(height=400, template='plotly_white')
                    st.plotly_chart(fig, use_container_width=True)
                
                # Controversy score
                if esg_data.get('controversy_score'):
                    st.markdown("---")
                    st.markdown("#### ⚠️ Controversy Score")
                    controversy = esg_data['controversy_score']
                    st.metric("Controversy Level", f"{controversy:.0f}/5")
                    
                    if controversy >= 4:
                        st.warning("⚠️ High controversy level")
                    elif controversy >= 3:
                        st.info("ℹ️ Moderate controversy level")
                    else:
                        st.success("✅ Low controversy level")
            else:
                st.info(f"ESG data not available for {esg_ticker}")
            
            # Additional financial metrics
            st.markdown("---")
            st.markdown("#### 📊 Additional Financial Data")
            
            data = analyzer.get_stock_data(esg_ticker, period="1y")
            if data:
                metrics = analyzer.get_key_metrics(data)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("##### 💼 Company Info")
                    st.write(f"**Sector:** {data['info'].get('sector', 'N/A')}")
                    st.write(f"**Industry:** {data['info'].get('industry', 'N/A')}")
                    st.write(f"**Employees:** {data['info'].get('fullTimeEmployees', 'N/A'):,}" if data['info'].get('fullTimeEmployees') else "**Employees:** N/A")
                
                with col2:
                    st.markdown("##### 📈 Trading Info")
                    st.write(f"**52W High:** ${data['info'].get('fiftyTwoWeekHigh', 0):.2f}")
                    st.write(f"**52W Low:** ${data['info'].get('fiftyTwoWeekLow', 0):.2f}")
                    st.write(f"**Average Volume:** {metrics.get('Average Volume', 0):,}")
                
                with col3:
                    st.markdown("##### 📊 Valuation")
                    st.write(f"**Enterprise Value:** ${data['info'].get('enterpriseValue', 0):,.0f}")
                    st.write(f"**Book Value:** ${data['info'].get('bookValue', 0):.2f}")
                    st.write(f"**Price/Sales:** {data['info'].get('priceToSalesTrailing12Months', 0):.2f}")

render_footer()

