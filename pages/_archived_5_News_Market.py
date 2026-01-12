"""
News & Market Context Page
Display news, market overview, sector performance, and market movers
"""

import streamlit as st
import pandas as pd
from utils.news_market import NewsMarketData
from utils.stock_analyzer import StockAnalyzer
from components.styling import apply_platform_theme, render_header, render_footer
from components.navigation import render_navigation

# Page configuration
st.set_page_config(
    page_title="News & Market Context",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply theme and navigation
apply_platform_theme()
render_navigation()

# Initialize
if 'news_market' not in st.session_state:
    st.session_state.news_market = NewsMarketData()

news_market = st.session_state.news_market

# Header
render_header("📰 News & Market Context", "Stay informed with market news and insights")

# Market Overview Section
st.subheader("📊 Market Overview")
market_overview = news_market.get_market_overview()

if market_overview:
    cols = st.columns(len(market_overview))
    for idx, (name, data) in enumerate(market_overview.items()):
        with cols[idx]:
            change_color = "normal" if data['change'] >= 0 else "inverse"
            st.metric(
                name,
                f"${data['price']:.2f}",
                delta=f"{data['change_pct']:+.2f}%",
                delta_color=change_color
            )

st.markdown("---")

# Tabs for different views
tab1, tab2, tab3, tab4 = st.tabs(["📰 Stock News", "📈 Sector Performance", "🚀 Market Movers", "📊 Stock Search"])

with tab1:
    st.markdown("### 📰 Stock News Feed")
    ticker_input = st.text_input("Enter Stock Ticker:", value="NVDA", key="news_ticker").upper()
    news_limit = st.slider("Number of articles", 5, 20, 10)
    
    if st.button("Get News", key="get_news"):
        with st.spinner(f"Fetching news for {ticker_input}..."):
            news = news_market.get_stock_news(ticker_input, news_limit)
            
            if news:
                for article in news:
                    with st.expander(f"📄 {article['title']}", expanded=False):
                        st.markdown(f"**Publisher:** {article['publisher']}")
                        if article['published']:
                            st.markdown(f"**Published:** {article['published'].strftime('%Y-%m-%d %H:%M')}")
                        st.markdown(f"**Summary:** {article['summary']}")
                        st.markdown(f"[Read Full Article →]({article['link']})")
            else:
                st.info(f"No news found for {ticker_input}")

with tab2:
    st.markdown("### 📈 Sector Performance (Last 5 Days)")
    
    if st.button("Refresh Sector Data", key="refresh_sectors"):
        with st.spinner("Fetching sector data..."):
            sector_data = news_market.get_sector_performance()
            
            if len(sector_data) > 0:
                # Style the dataframe
                def color_sector(val):
                    if val > 2:
                        return 'background-color: #c8e6c9'  # Green
                    elif val > 0:
                        return 'background-color: #fff9c4'  # Yellow
                    elif val > -2:
                        return 'background-color: #ffe0b2'  # Orange
                    else:
                        return 'background-color: #ffcdd2'  # Red
                
                styled_df = sector_data.style.applymap(color_sector, subset=['Change %'])\
                    .format({'Price': '${:.2f}', 'Change %': '{:+.2f}%'})
                
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
                
                # Bar chart
                import plotly.express as px
                fig = px.bar(sector_data, x='Sector', y='Change %',
                           title='Sector Performance',
                           color='Change %',
                           color_continuous_scale='RdYlGn')
                fig.update_layout(height=400, template='plotly_white')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sector data temporarily unavailable")

with tab3:
    st.markdown("### 🚀 Market Movers")
    
    direction = st.radio("Show:", ["📈 Top Gainers", "📉 Top Losers"], horizontal=True)
    
    if st.button("Refresh Movers", key="refresh_movers"):
        with st.spinner("Fetching market movers..."):
            movers = news_market.get_market_movers('gainers' if direction == "📈 Top Gainers" else 'losers')
            
            if len(movers) > 0:
                st.dataframe(
                    movers.style.format({
                        'Price': '${:.2f}',
                        'Change %': '{:+.2f}%',
                        'Volume': '{:,.0f}'
                    }).background_gradient(subset=['Change %'], cmap='RdYlGn'),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Market movers data temporarily unavailable")

with tab4:
    st.markdown("### 📊 Search Stock News")
    
    search_ticker = st.text_input("Stock Ticker:", value="", key="search_ticker").upper()
    if search_ticker:
        if st.button("Search", key="search_news"):
            news = news_market.get_stock_news(search_ticker, 15)
            
            if news:
                st.success(f"Found {len(news)} articles for {search_ticker}")
                for article in news:
                    st.markdown(f"### {article['title']}")
                    st.markdown(f"*{article['publisher']} - {article['published'].strftime('%Y-%m-%d') if article['published'] else 'Unknown date'}*")
                    st.markdown(article['summary'])
                    st.markdown(f"[Read more →]({article['link']})")
                    st.markdown("---")
            else:
                st.warning(f"No news found for {search_ticker}")

render_footer()

