"""
VirtualFusion Stock Analyzer Pro
Main Entry Point - Platform Dashboard
"""

import streamlit as st
from components.styling import apply_platform_theme, render_header, render_footer
from components.navigation import render_navigation

# Page configuration
st.set_page_config(
    page_title="VirtualFusion Stock Analyzer Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply platform theme
apply_platform_theme()

# Render navigation
render_navigation()

# Main content
render_header("📈 VirtualFusion Stock Analyzer Pro", "Advanced AI-Powered Stock Analysis Platform")

# Dashboard content
st.markdown("""
<div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; border-radius: 1rem; margin: 2rem 0;'>
    <h2 style='color: white; margin-bottom: 1rem;'>Welcome to Your Stock Analysis Platform</h2>
    <p style='font-size: 1.2rem;'>Comprehensive tools for professional stock analysis and investment research</p>
</div>
""", unsafe_allow_html=True)

# Feature cards
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="info-card">
        <h3 style='color: white;'>📊 Single Analysis</h3>
        <p style='color: white;'>Deep dive into individual stocks with comprehensive metrics, charts, and scoring</p>
        <p style='color: #ccc; font-size: 0.9rem; margin-top: 0.5rem;'>💡 Use the sidebar to navigate to "📊 Single Analysis"</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="success-card">
        <h3 style='color: white;'>📈 Batch Comparison</h3>
        <p style='color: white;'>Compare multiple stocks side-by-side to identify the best opportunities</p>
        <p style='color: #ccc; font-size: 0.9rem; margin-top: 0.5rem;'>💡 Use the sidebar to navigate to "📈 Batch Comparison"</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="warning-card">
        <h3 style='color: white;'>🔍 Stock Screener</h3>
        <p style='color: white;'>Filter stocks by custom criteria to find investment opportunities</p>
        <p style='color: #ccc; font-size: 0.9rem; margin-top: 0.5rem;'>💡 Use the sidebar to navigate to "🔍 Stock Screener"</p>
    </div>
    """, unsafe_allow_html=True)

# Reports section
st.markdown("---")

col_report = st.columns([1, 1, 1])[1]  # Center column

with col_report:
    st.markdown("""
    <div class="warning-card">
        <h3 style='color: white;'>📄 Reports</h3>
        <p style='color: white;'>Generate professional PDF reports</p>
        <p style='color: #ccc; font-size: 0.9rem; margin-top: 0.5rem;'>💡 Use the sidebar to navigate to "📄 Reports"</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Quick stats section
st.markdown("### 🚀 Quick Start")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    #### 📋 Recent Features
    - ✅ Advanced scoring system (0-100)
    - ✅ Technical indicator analysis
    - ✅ Batch stock comparison
    - ✅ Custom stock screener
    - ✅ Professional PDF reports
    - ✅ Interactive visualizations
    - ✅ **Integrated News & Market Context** (in ticker views)
    - ✅ **Integrated Earnings Calendar** (in ticker views)
    - ✅ **Integrated Risk Analysis** (in ticker views)
    - ✅ **Integrated Performance Tracking** (in ticker views)
    - ✅ **Integrated Advanced Financials** (in ticker views)
    """)

with col2:
    st.markdown("""
    #### 📊 Analysis Capabilities
    - 💰 **30+ Financial Metrics**
    - 📈 **Technical Indicators** (RSI, MACD, Moving Averages)
    - 📉 **Valuation Analysis** (P/E, PEG, Price/Book)
    - 💵 **Profitability Metrics** (Margins, ROE, ROA)
    - 📊 **Growth Analysis** (Revenue & Earnings Growth)
    """)

st.markdown("---")

# Getting started section
st.markdown("### 📖 Getting Started")

tab1, tab2, tab3 = st.tabs(["Quick Analysis", "Compare Stocks", "Screen Stocks"])

with tab1:
    st.markdown("""
    #### Analyze a Single Stock
    
    1. Click **"Go to Single Analysis"** button above
    2. Enter a stock ticker (e.g., NVDA, AAPL, MSFT)
    3. Click **"Analyze"** to see comprehensive analysis
    4. Explore all tabs: Charts, Metrics, Financials, Technical, **News**, **Earnings**, **Risk**, **Performance**, and **Advanced**
    
    **All features integrated:**
    - 📰 News & Market Context tab
    - 📅 Earnings Calendar tab
    - ⚠️ Risk Analysis tab
    - 📊 Performance Tracking tab
    - 🔬 Advanced Financial Analysis tab
    
    **Example tickers to try:**
    - `NVDA` - NVIDIA Corporation
    - `AAPL` - Apple Inc.
    - `MSFT` - Microsoft Corporation
    - `GOOGL` - Alphabet Inc.
    """)

with tab2:
    st.markdown("""
    #### Compare Multiple Stocks
    
    1. Click **"Go to Batch Comparison"** button above
    2. Enter multiple tickers separated by commas
    3. Click **"Compare Stocks"** to see side-by-side comparison
    4. Expand each stock to view full analysis with all integrated features
    5. Export results to CSV or Excel
    
    **Each stock includes:** News, Earnings, Risk, Performance, and Advanced tabs
    
    **Example:** `NVDA, AMD, SOFI, PLTR`
    """)

with tab3:
    st.markdown("""
    #### Screen Stocks by Criteria
    
    1. Click **"Go to Stock Screener"** button above
    2. Set your filtering criteria (P/E, margins, growth, etc.)
    3. Enter stock universe to screen
    4. Review matching stocks with full integrated analysis
    
    **Each matching stock includes:** News, Earnings, Risk, Performance, and Advanced tabs
    
    **Example filters:**
    - P/E Ratio: 5-20 (Value stocks)
    - Min Gross Margin: 30%
    - Min ROE: 15%
    """)

render_footer()

