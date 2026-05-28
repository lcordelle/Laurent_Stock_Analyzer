"""
Price & Signal Alerts — set conditions, get Telegram notifications
"""

import streamlit as st
import pandas as pd
from utils.auth import require_auth
from utils.alert_engine import (
    get_alerts, add_alert, delete_alert, reset_alert,
    CONDITION_LABELS,
)
from components.styling import apply_platform_theme, render_header, render_footer
from components.navigation import render_top_navigation
require_auth()

st.set_page_config(
    page_title="Alerts",
    page_icon="🔔",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_platform_theme()
render_top_navigation()
render_header("Price & Signal Alerts", "Set conditions · get Telegram notifications when triggered")

import os
has_telegram = bool(os.environ.get('TELEGRAM_BOT_TOKEN') and os.environ.get('TELEGRAM_CHAT_ID'))
if not has_telegram:
    st.info(
        "Telegram not configured. Set environment variables **TELEGRAM_BOT_TOKEN** and "
        "**TELEGRAM_CHAT_ID** to receive push notifications. Alerts still fire and are logged here."
    )

tab_active, tab_add = st.tabs(["🔔 Active Alerts", "➕ Add Alert"])

# ── Add Alert ─────────────────────────────────────────────────────────────────
with tab_add:
    st.markdown("### Create a New Alert")
    with st.form("add_alert_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            a_ticker = st.text_input("Ticker", placeholder="AAPL").upper()
        with c2:
            a_condition = st.selectbox("Condition", list(CONDITION_LABELS.keys()),
                                       format_func=lambda k: CONDITION_LABELS[k])
        with c3:
            a_threshold = st.number_input("Threshold", value=100.0, step=0.01)

        st.caption({
            'price_above': "Notify when price rises above threshold.",
            'price_below': "Notify when price falls below threshold.",
            'rsi_above': "Notify when RSI(14) exceeds threshold (>70 = overbought).",
            'rsi_below': "Notify when RSI(14) drops below threshold (<30 = oversold).",
        }.get(a_condition, ''))

        submitted = st.form_submit_button("Create Alert", use_container_width=True)

    if submitted and a_ticker:
        alert_id = add_alert(a_ticker, a_condition, a_threshold)
        st.success(f"Alert created (ID: {alert_id}) — checking every 60 seconds.")
        st.rerun()

# ── Active Alerts ─────────────────────────────────────────────────────────────
with tab_active:
    alerts = get_alerts()

    if not alerts:
        st.info("No alerts configured. Use the Add Alert tab to create your first alert.")
    else:
        active = [a for a in alerts if not a.get('fired')]
        fired = [a for a in alerts if a.get('fired')]

        if active:
            st.markdown(f"### Monitoring ({len(active)} active)")
            for alert in active:
                label = CONDITION_LABELS.get(alert['condition'], alert['condition'])
                col_info, col_del = st.columns([5, 1])
                with col_info:
                    st.markdown(
                        f"**{alert['ticker']}** — {label} **{alert['threshold']}** "
                        f"<span style='color:#9ca3af;font-size:12px;margin-left:8px;'>ID: {alert['id']} · set {alert['created'][:10]}</span>",
                        unsafe_allow_html=True,
                    )
                with col_del:
                    if st.button("Delete", key=f"del_{alert['id']}", use_container_width=True):
                        delete_alert(alert['id'])
                        st.rerun()

        if fired:
            st.markdown("---")
            st.markdown(f"### Fired Alerts ({len(fired)})")
            for alert in fired:
                label = CONDITION_LABELS.get(alert['condition'], alert['condition'])
                col_info, col_reset, col_del = st.columns([4, 1, 1])
                with col_info:
                    st.markdown(
                        f"✅ **{alert['ticker']}** — {label} **{alert['threshold']}** "
                        f"fired at {alert.get('fired_at', 'unknown')[:16]}",
                        unsafe_allow_html=True,
                    )
                with col_reset:
                    if st.button("Reset", key=f"reset_{alert['id']}", use_container_width=True):
                        reset_alert(alert['id'])
                        st.rerun()
                with col_del:
                    if st.button("Delete", key=f"del_f_{alert['id']}", use_container_width=True):
                        delete_alert(alert['id'])
                        st.rerun()

render_footer()
