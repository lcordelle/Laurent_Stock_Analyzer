"""
Navigation Component
Provides consistent navigation across the platform
"""

import streamlit as st

def render_navigation():
    """Render navigation sidebar"""
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 1rem 0;'>
            <h1 style='color: #1f77b4; margin: 0;'>📈 VirtualFusion</h1>
            <p style='color: #666; margin: 0;'>Stock Analyzer Pro</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        
        st.markdown("### 🎯 Navigation")
        st.markdown("""
        **Core Analysis:**
        - 📊 Single Analysis
        - 📈 Batch Comparison
        - 🔍 Stock Screener
        
        **Market Intelligence:**
        - 📰 News & Market
        - 📅 Earnings Calendar
        
        **Advanced Features:**
        - ⚠️ Risk Analysis
        - 📊 Performance Tracking
        - 🔬 Advanced Analysis
        - 📄 Reports
        """)
        
        st.markdown("---")
        
        st.markdown("### ⚙️ Settings")
        
        time_period = st.selectbox(
            "Time Period:",
            ["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
            index=3,
            key="time_period_global"
        )
        
        show_technical = st.checkbox("Show Technical Indicators", value=True, key="show_technical_global")
        show_fundamentals = st.checkbox("Show Fundamental Analysis", value=True, key="show_fundamentals_global")
        
        # Store in session state
        st.session_state.time_period = time_period
        st.session_state.show_technical = show_technical
        st.session_state.show_fundamentals = show_fundamentals
        
        st.markdown("---")
        st.info("💡 **Tip:** Higher scores indicate better overall financial health")
        
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; padding: 1rem 0;'>
            <p style='font-size: 0.8rem; color: #999;'>Version 2.0.0</p>
        </div>
        """, unsafe_allow_html=True)

