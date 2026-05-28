"""
Laurent Stock Analyzer Pro
Enterprise-Grade Trading Intelligence Platform
"""

import streamlit as st
from utils.auth import require_auth
from components.styling import apply_platform_theme
from components.navigation import render_top_navigation

# Auth check (in-app login for mobile compatibility)
require_auth()

# Start background cache pre-warmer once per session
if "warmer_started" not in st.session_state:
    st.session_state.warmer_started = True
    from utils.startup_warmer import start_warmer
    start_warmer()

# Start alert engine background thread once per session
if "alert_engine_started" not in st.session_state:
    st.session_state.alert_engine_started = True
    from utils.alert_engine import start_alert_engine
    start_alert_engine()

# Page configuration
st.set_page_config(
    page_title="Laurent Stock Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply enterprise theme (includes top nav)
apply_platform_theme()

# Render top navigation
render_top_navigation()

# Enhanced feature cards styling is now in components/styling.py
# Additional enhancements for main page
st.markdown("""
    <style>
        /* Additional enhancements for main page feature cards */
        button[kind="secondary"][data-testid*="nav"] {
            position: relative !important;
            overflow: hidden !important;
        }
        
        /* Add subtle glow effect on hover */
        button[kind="secondary"][data-testid*="nav"]:hover {
            box-shadow: 0 16px 40px rgba(59, 130, 246, 0.35), 
                        0 0 0 1px rgba(59, 130, 246, 0.1) !important;
        }
        
        /* Ensure text is always visible */
        button[kind="secondary"][data-testid*="nav"] * {
            position: relative !important;
            z-index: 1 !important;
        }
    </style>
""", unsafe_allow_html=True)

# Center the cards
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    if st.button("**Single Analysis**\n\nDeep analysis with trading signals, charts, and metrics", 
                 key="main_card_single", use_container_width=True, type="secondary"):
        st.switch_page("pages/1_Single_Analysis.py")

with col2:
    if st.button("**Batch Comparison**\n\nCompare multiple stocks side-by-side with instant signals", 
                 key="main_card_batch", use_container_width=True, type="secondary"):
        st.switch_page("pages/2_Batch_Comparison.py")

with col3:
    if st.button("**Stock Screener**\n\nFilter stocks by criteria with automated analysis", 
                 key="main_card_screener", use_container_width=True, type="secondary"):
        st.switch_page("pages/3_Stock_Screener.py")
