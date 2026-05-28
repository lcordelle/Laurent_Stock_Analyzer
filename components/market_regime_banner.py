"""
Market Regime Banner Component
Displays VIX, regime label, and SPY change at the top of every page.
"""

import streamlit as st
from utils.market_breadth import get_market_regime


@st.cache_data(ttl=300)
def _fetch_regime() -> dict:
    return get_market_regime()


def render_market_regime_banner() -> None:
    """Render a compact market regime status bar."""
    try:
        data = _fetch_regime()
    except Exception:
        return

    vix = data.get('vix')
    regime = data.get('regime', 'Unknown')
    color = data.get('color', '#6b7280')
    spy_change = data.get('spy_change')
    description = data.get('description', '')

    vix_str = f"VIX {vix:.1f}" if vix is not None else "VIX —"
    spy_str = ''
    if spy_change is not None:
        arrow = '▲' if spy_change >= 0 else '▼'
        spy_color = '#22c55e' if spy_change >= 0 else '#ef4444'
        spy_str = f'<span style="color:{spy_color};margin-left:16px;">{arrow} SPY {spy_change:+.2f}%</span>'

    st.markdown(f"""
    <div style="
        background: linear-gradient(90deg, {color}22 0%, transparent 100%);
        border-left: 4px solid {color};
        border-radius: 4px;
        padding: 6px 14px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        font-size: 13px;
        line-height: 1.4;
    ">
        <span style="font-weight:700;color:{color};font-size:14px;">{regime}</span>
        <span style="color:#6b7280;margin-left:12px;">{vix_str}</span>
        {spy_str}
        <span style="color:#9ca3af;margin-left:16px;font-size:11px;">{description}</span>
    </div>
    """, unsafe_allow_html=True)
