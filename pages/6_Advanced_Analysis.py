"""
Advanced Analysis — Insider, Short Interest, Institutional Holdings, Options Flow
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.auth import require_auth
from utils.advanced_financials import AdvancedFinancials
from utils.options_flow import get_options_flow, sentiment_label
from components.styling import apply_platform_theme, render_header, render_footer
from components.navigation import render_top_navigation
require_auth()

st.set_page_config(
    page_title="Advanced Analysis",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_platform_theme()
render_top_navigation()
render_header("Advanced Analysis", "Insider transactions · Short interest · Institutional holdings · Options flow")

if 'advanced_financials' not in st.session_state:
    st.session_state.advanced_financials = AdvancedFinancials()

advanced = st.session_state.advanced_financials

tab_insider, tab_short, tab_inst, tab_options = st.tabs([
    "👥 Insider Transactions",
    "📉 Short Interest",
    "🏦 Institutional Holdings",
    "🎯 Options Flow",
])

# ── Insider Transactions ──────────────────────────────────────────────────────
with tab_insider:
    st.markdown("### 👥 Insider Transactions")
    st.caption("SEC Form 4 filings — cluster buys by insiders often precede price appreciation.")

    col_input, col_btn = st.columns([3, 1])
    with col_input:
        insider_ticker = st.text_input("Ticker", value="AAPL", key="insider_ticker",
                                       label_visibility="collapsed", placeholder="e.g. AAPL").upper()
    with col_btn:
        run_insider = st.button("Fetch", key="btn_insider", use_container_width=True)

    if run_insider and insider_ticker:
        with st.spinner(f"Fetching insider data for {insider_ticker}..."):
            df = advanced.get_insider_transactions(insider_ticker)

        if df is not None and len(df) > 0:
            # Cluster buy detection: buys in last 30 days
            if 'Transaction' in df.columns and 'Start Date' in df.columns:
                buys = df[df['Transaction'].str.contains('Buy|Purchase', case=False, na=False)]
                if len(buys) >= 3:
                    st.success(f"Cluster buying signal: {len(buys)} purchase transactions detected")

            st.dataframe(df.head(20), use_container_width=True, hide_index=True)
        else:
            st.info("No recent insider transaction data available for this ticker.")

# ── Short Interest ────────────────────────────────────────────────────────────
with tab_short:
    st.markdown("### 📉 Short Interest & Days-to-Cover")
    st.caption("High short % + rising price = potential squeeze. Days-to-cover > 5 amplifies the effect.")

    col_input2, col_btn2 = st.columns([3, 1])
    with col_input2:
        short_ticker = st.text_input("Ticker", value="AAPL", key="short_ticker",
                                     label_visibility="collapsed", placeholder="e.g. NVDA").upper()
    with col_btn2:
        run_short = st.button("Fetch", key="btn_short", use_container_width=True)

    if run_short and short_ticker:
        with st.spinner(f"Fetching short interest for {short_ticker}..."):
            short_data = advanced.get_short_interest(short_ticker)

        if short_data and short_data.get('shares_short', 0) > 0:
            short_pct = short_data.get('short_percent_of_float', 0)
            days_cover = short_data.get('short_ratio', 0)
            pct_change = short_data.get('short_percent_change', 0)

            squeeze_risk = "High" if short_pct > 20 and days_cover > 5 else \
                           "Moderate" if short_pct > 10 else "Low"
            squeeze_color = "#ef4444" if squeeze_risk == "High" else \
                            "#f59e0b" if squeeze_risk == "Moderate" else "#22c55e"

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Short % of Float", f"{short_pct:.1f}%")
            with c2:
                st.metric("Days to Cover", f"{days_cover:.1f}")
            with c3:
                st.metric("Short Change MoM", f"{pct_change:+.1f}%",
                          delta=f"{pct_change:+.1f}%")
            with c4:
                st.metric("Shares Short", f"{short_data.get('shares_short', 0):,.0f}")

            st.markdown(
                f'<div style="padding:8px 14px;background:{squeeze_color}22;border-left:4px solid {squeeze_color};'
                f'border-radius:4px;margin-top:8px;">'
                f'<b style="color:{squeeze_color};">Squeeze Risk: {squeeze_risk}</b>'
                f'</div>',
                unsafe_allow_html=True
            )
        else:
            st.info("Short interest data not available for this ticker.")

# ── Institutional Holdings ────────────────────────────────────────────────────
with tab_inst:
    st.markdown("### 🏦 Institutional & Mutual Fund Holdings")
    st.caption("Top holders from most recent 13F filings. Large increases = conviction buying.")

    col_input3, col_btn3 = st.columns([3, 1])
    with col_input3:
        inst_ticker = st.text_input("Ticker", value="AAPL", key="inst_ticker",
                                    label_visibility="collapsed", placeholder="e.g. MSFT").upper()
    with col_btn3:
        run_inst = st.button("Fetch", key="btn_inst", use_container_width=True)

    if run_inst and inst_ticker:
        with st.spinner(f"Fetching institutional data for {inst_ticker}..."):
            inst_df = advanced.get_institutional_holdings(inst_ticker)

        if inst_df is not None and len(inst_df) > 0:
            st.markdown("#### Top Institutional Holders")
            st.dataframe(inst_df.head(15), use_container_width=True, hide_index=True)

            # Chart: top 10 by % held
            if '% Out' in inst_df.columns and 'Holder' in inst_df.columns:
                top10 = inst_df.head(10).copy()
                fig = go.Figure(go.Bar(
                    x=top10['% Out'],
                    y=top10['Holder'],
                    orientation='h',
                    marker_color='#3b82f6',
                ))
                fig.update_layout(
                    title='Top 10 Institutional Holders (% Shares Owned)',
                    height=350,
                    margin=dict(l=0, r=0, t=40, b=0),
                    xaxis_title='% Outstanding',
                    yaxis=dict(autorange='reversed'),
                    template='plotly_white',
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Institutional holdings data not available.")

# ── Options Flow ──────────────────────────────────────────────────────────────
with tab_options:
    st.markdown("### 🎯 Unusual Options Activity")
    st.caption("Volume > open interest = fresh directional bet. High volume/OI ratio = high conviction.")

    col_input4, col_btn4 = st.columns([3, 1])
    with col_input4:
        opts_ticker = st.text_input("Ticker", value="NVDA", key="opts_ticker",
                                    label_visibility="collapsed", placeholder="e.g. NVDA").upper()
    with col_btn4:
        run_opts = st.button("Fetch", key="btn_opts", use_container_width=True)

    if run_opts and opts_ticker:
        with st.spinner(f"Fetching options flow for {opts_ticker}..."):
            flow = get_options_flow(opts_ticker)

        if flow.get('error') and not flow.get('unusual'):
            st.error(f"Options data unavailable: {flow['error']}")
        else:
            summary = flow['summary']
            pc = summary.get('pc_ratio', 0)
            pc_vol = summary.get('pc_volume_ratio', 0)
            sentiment, sent_color = sentiment_label(pc)

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Call OI", f"{summary['total_call_oi']:,}")
            with c2:
                st.metric("Put OI", f"{summary['total_put_oi']:,}")
            with c3:
                st.metric("P/C OI Ratio", f"{pc:.2f}")
            with c4:
                st.metric("P/C Volume Ratio", f"{pc_vol:.2f}")

            st.markdown(
                f'<div style="padding:8px 14px;background:{sent_color}22;border-left:4px solid {sent_color};'
                f'border-radius:4px;margin-bottom:12px;">'
                f'<b style="color:{sent_color};">Options Sentiment: {sentiment}</b>'
                f'</div>',
                unsafe_allow_html=True
            )

            if flow['unusual']:
                st.markdown("#### Unusual Activity (Volume > OI, Volume > 100)")
                rows = []
                for u in flow['unusual']:
                    rows.append({
                        'Expiry': u['expiry'],
                        'Type': u['type'].upper(),
                        'Strike': f"${u['strike']:.1f}",
                        'Volume': f"{u['volume']:,}",
                        'OI': f"{u['oi']:,}",
                        'Vol/OI': f"{u['vol_oi_ratio']:.1f}x",
                        'IV %': f"{u['iv']:.0f}%" if u['iv'] else "—",
                        'Last': f"${u['last']:.2f}",
                    })
                df_unusual = pd.DataFrame(rows)
                st.dataframe(df_unusual, use_container_width=True, hide_index=True)
            else:
                st.info("No unusual options activity detected for current expiries.")

            if flow['expirations']:
                st.caption(f"Analyzed expirations: {', '.join(flow['expirations'][:4])}")

render_footer()
