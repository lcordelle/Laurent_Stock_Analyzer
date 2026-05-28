"""
Enterprise Top Navigation Component
Modern top menu bar with light/dark mode support
"""

import streamlit as st

def render_top_navigation():
    """Render modern top navigation bar with theme toggle"""
    
    # Top navigation bar - use Streamlit buttons for reliable page routing
    st.markdown("""
    <div class="top-nav">
        <div class="nav-brand">
            <span>📈</span>
            <span>Laurent Stock Analyzer</span>
        </div>
    </div>
    <div class="nav-spacer"></div>
    """, unsafe_allow_html=True)
    
    # Navigation buttons (st.switch_page ensures correct page loads)
    nav1, nav2, nav3, nav4, nav5, nav6, nav_spacer = st.columns([1, 1, 1, 1, 1, 0.5, 2])
    with nav1:
        if st.button("🏠 Dashboard", key="nav_btn_dashboard", use_container_width=True):
            st.switch_page("main.py")
    with nav2:
        if st.button("📊 Single Analysis", key="nav_btn_single", use_container_width=True):
            st.switch_page("pages/1_Single_Analysis.py")
    with nav3:
        if st.button("📈 Batch Comparison", key="nav_btn_batch", use_container_width=True):
            st.switch_page("pages/2_Batch_Comparison.py")
    with nav4:
        if st.button("🔍 Stock Screener", key="nav_btn_screener", use_container_width=True):
            st.switch_page("pages/3_Stock_Screener.py")
    with nav5:
        if st.button("🤖 AI Predictor", key="nav_btn_ai", use_container_width=True):
            st.switch_page("pages/5_AI_Predictor.py")
    with nav6:
        if st.session_state.get('authenticated'):
            if st.button("🚪", key="nav_btn_logout", use_container_width=True, help="Sign out"):
                st.session_state.authenticated = False
                st.rerun()

    # Second row: pro trader feature pages
    pn1, pn2, pn3, pn4, pn5, pn_spacer = st.columns([1, 1, 1, 1, 1, 1.5])
    with pn1:
        if st.button("🔬 Advanced", key="nav_btn_advanced", use_container_width=True):
            st.switch_page("pages/6_Advanced_Analysis.py")
    with pn2:
        if st.button("📓 Journal", key="nav_btn_journal", use_container_width=True):
            st.switch_page("pages/7_Trade_Journal.py")
    with pn3:
        if st.button("🔔 Alerts", key="nav_btn_alerts", use_container_width=True):
            st.switch_page("pages/8_Alerts.py")
    with pn4:
        if st.button("⏪ Backtest", key="nav_btn_backtest", use_container_width=True):
            st.switch_page("pages/9_Backtesting.py")
    with pn5:
        if st.button("📋 Reports", key="nav_btn_reports", use_container_width=True):
            st.switch_page("pages/4_Reports.py")

    # Market regime banner — shown on every page automatically
    try:
        from components.market_regime_banner import render_market_regime_banner
        render_market_regime_banner()
    except Exception:
        pass

    # Theme toggle
    col1, col2, col3 = st.columns([1, 1, 0.1])
    with col3:
        theme_icon = "☀️" if st.session_state.get('theme', 'dark') == 'dark' else "🌙"
        theme_toggle = st.button(theme_icon, key="theme_toggle_top", help="Toggle Light/Dark Mode", use_container_width=True)
        if theme_toggle:
            st.session_state.theme = 'light' if st.session_state.get('theme', 'dark') == 'dark' else 'dark'
            st.rerun()

def render_navigation():
    """Legacy function - now renders top navigation"""
    render_top_navigation()


def render_market_regime_inline() -> None:
    """Convenience wrapper — imports and calls the banner component."""
    try:
        from components.market_regime_banner import render_market_regime_banner
        render_market_regime_banner()
    except Exception:
        pass
