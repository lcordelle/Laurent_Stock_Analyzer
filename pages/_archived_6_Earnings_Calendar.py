"""
Earnings Calendar Page
Track earnings dates, history, and estimates
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.earnings_calendar import EarningsCalendar
from components.styling import apply_platform_theme, render_header, render_footer
from components.navigation import render_navigation

# Page configuration
st.set_page_config(
    page_title="Earnings Calendar",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply theme and navigation
apply_platform_theme()
render_navigation()

# Initialize
if 'earnings_calendar' not in st.session_state:
    st.session_state.earnings_calendar = EarningsCalendar()

earnings_cal = st.session_state.earnings_calendar

# Header
render_header("📅 Earnings Calendar", "Track earnings dates, history, and surprises")

# Tabs
tab1, tab2, tab3 = st.tabs(["📅 Upcoming Earnings", "📊 Stock Earnings", "📈 Earnings Surprises"])

with tab1:
    st.markdown("### 📅 Upcoming Earnings")
    
    days_ahead = st.slider("Show earnings in next N days:", 7, 90, 30)
    
    if st.button("Load Upcoming Earnings", key="load_upcoming"):
        with st.spinner("Fetching upcoming earnings..."):
            upcoming = earnings_cal.get_upcoming_earnings(days_ahead)
            
            if len(upcoming) > 0:
                st.success(f"Found {len(upcoming)} stocks with earnings in the next {days_ahead} days")
                
                # Format dataframe
                display_df = upcoming.copy()
                display_df['Earnings Date'] = pd.to_datetime(display_df['Earnings Date']).dt.strftime('%Y-%m-%d')
                
                # Color code by days until
                def color_days(val):
                    if val <= 7:
                        return 'background-color: #ffcdd2'  # Red - urgent
                    elif val <= 14:
                        return 'background-color: #fff9c4'  # Yellow - soon
                    else:
                        return 'background-color: #c8e6c9'  # Green - upcoming
                
                styled_df = display_df.style.applymap(color_days, subset=['Days Until'])\
                    .format({'Last Close': '${:.2f}'})
                
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
                
                # Timeline view
                st.markdown("#### Timeline View")
                for _, row in upcoming.iterrows():
                    days_until = row['Days Until']
                    days_label = f"{days_until} day{'s' if days_until != 1 else ''}"
                    
                    if days_until <= 7:
                        status = "🔴 This Week"
                    elif days_until <= 14:
                        status = "🟡 Next Week"
                    else:
                        status = "🟢 Upcoming"
                    
                    st.markdown(f"**{row['Ticker']}** - {row['Company']} | {status} | Earnings on {row['Earnings Date']} ({days_label})")
            else:
                st.info("No upcoming earnings found for tracked stocks")

with tab2:
    st.markdown("### 📊 Individual Stock Earnings")
    
    ticker = st.text_input("Enter Stock Ticker:", value="AAPL", key="earnings_ticker").upper()
    
    if st.button("Get Earnings Data", key="get_earnings"):
        with st.spinner(f"Fetching earnings data for {ticker}..."):
            earnings_data = earnings_cal.get_earnings_dates(ticker)
            
            if earnings_data:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 📅 Earnings Dates")
                    if earnings_data.get('last_earnings_date'):
                        st.metric("Last Earnings", str(earnings_data['last_earnings_date']))
                    if earnings_data.get('next_earnings_date'):
                        next_date = earnings_data['next_earnings_date']
                        if isinstance(next_date, pd.Timestamp):
                            next_date = next_date.date()
                        days_away = (next_date - datetime.now().date()).days
                        st.metric("Next Earnings", str(next_date), delta=f"{days_away} days")
                    if earnings_data.get('earnings_quarter'):
                        st.info(f"Quarter: {earnings_data['earnings_quarter']}")
                
                with col2:
                    st.markdown("#### 📈 Analyst Estimates")
                    estimates = earnings_data.get('analyst_estimates', {})
                    if estimates:
                        st.metric("Trailing EPS", f"${estimates.get('eps_estimate', 0):.2f}")
                        st.metric("Forward EPS", f"${estimates.get('forward_eps', 0):.2f}")
                        eps_growth = estimates.get('eps_growth', 0) * 100
                        st.metric("EPS Growth", f"{eps_growth:+.2f}%")
                
                # Earnings History
                if earnings_data.get('earnings_history'):
                    st.markdown("---")
                    st.markdown("#### 📊 Recent Earnings History")
                    history_df = pd.DataFrame(earnings_data['earnings_history'])
                    st.dataframe(history_df, use_container_width=True, hide_index=True)
            else:
                st.warning(f"Earnings data not available for {ticker}")

with tab3:
    st.markdown("### 📈 Earnings Surprises")
    
    surprise_ticker = st.text_input("Enter Stock Ticker:", value="NVDA", key="surprise_ticker").upper()
    
    if st.button("Get Surprises", key="get_surprises"):
        with st.spinner(f"Analyzing earnings surprises for {surprise_ticker}..."):
            surprises = earnings_cal.get_earnings_surprises(surprise_ticker)
            
            if len(surprises) > 0:
                # Format surprises
                display_surprises = surprises.copy()
                
                # Color code surprises
                def color_surprise(val):
                    if val > 5:
                        return 'background-color: #c8e6c9'  # Green - big beat
                    elif val > 0:
                        return 'background-color: #fff9c4'  # Yellow - beat
                    elif val < -5:
                        return 'background-color: #ffcdd2'  # Red - big miss
                    else:
                        return 'background-color: #ffe0b2'  # Orange - miss
                
                styled_surprises = display_surprises.style.applymap(color_surprise, subset=['Surprise %'])\
                    .format({
                        'Actual': '${:.2f}',
                        'Estimate': '${:.2f}',
                        'Surprise': '${:.2f}',
                        'Surprise %': '{:+.2f}%'
                    })
                
                st.dataframe(styled_surprises, use_container_width=True, hide_index=True)
                
                # Summary statistics
                if 'Surprise %' in display_surprises.columns:
                    avg_surprise = display_surprises['Surprise %'].mean()
                    beats = len(display_surprises[display_surprises['Surprise %'] > 0])
                    total = len(display_surprises)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Average Surprise", f"{avg_surprise:+.2f}%")
                    with col2:
                        st.metric("Earnings Beats", f"{beats}/{total}")
                    with col3:
                        st.metric("Beat Rate", f"{(beats/total*100):.1f}%")
            else:
                st.info(f"No earnings surprises data available for {surprise_ticker}")

render_footer()

