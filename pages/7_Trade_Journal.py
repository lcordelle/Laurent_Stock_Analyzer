"""
Trade Journal — log trades, track P&L vs SPY benchmark
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date
from utils.auth import require_auth
from utils.trade_journal import (
    add_trade, close_trade, delete_trade,
    get_open_trades, get_closed_trades, get_pnl_summary, get_spy_return,
)
from components.styling import apply_platform_theme, render_header, render_footer
from components.navigation import render_top_navigation
require_auth()

st.set_page_config(
    page_title="Trade Journal",
    page_icon="📓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_platform_theme()
render_top_navigation()
render_header("Trade Journal", "Log entries · track P&L · compare vs SPY")

tab_open, tab_closed, tab_add = st.tabs(["📂 Open Positions", "✅ Closed Trades", "➕ Add Trade"])

# ── Add Trade ─────────────────────────────────────────────────────────────────
with tab_add:
    st.markdown("### Log a New Trade")
    with st.form("add_trade_form"):
        c1, c2 = st.columns(2)
        with c1:
            ticker = st.text_input("Ticker", placeholder="AAPL").upper()
            direction = st.selectbox("Direction", ["LONG", "SHORT"])
            shares = st.number_input("Shares", min_value=0.01, value=1.0, step=0.01)
        with c2:
            entry_date = st.date_input("Entry Date", value=date.today())
            entry_price = st.number_input("Entry Price ($)", min_value=0.01, value=100.0, step=0.01)
            tags = st.text_input("Tags (optional)", placeholder="swing, earnings")
        notes = st.text_area("Notes", placeholder="Reason for entry, catalyst, setup...")
        submitted = st.form_submit_button("Log Trade", use_container_width=True)

    if submitted and ticker and entry_price > 0:
        add_trade(
            ticker=ticker,
            direction=direction,
            entry_date=str(entry_date),
            entry_price=entry_price,
            shares=shares,
            notes=notes,
            tags=tags,
        )
        st.success(f"Trade logged: {direction} {shares:.2f} × {ticker} @ ${entry_price:.2f}")
        st.rerun()

# ── Open Positions ────────────────────────────────────────────────────────────
with tab_open:
    st.markdown("### Open Positions")
    open_trades = get_open_trades()

    if not open_trades:
        st.info("No open positions. Use the Add Trade tab to log your first trade.")
    else:
        for trade in open_trades:
            with st.expander(
                f"{trade['direction']} {trade['ticker']} — {trade['shares']} shares @ ${trade['entry_price']:.2f} "
                f"(entered {trade['entry_date']})",
                expanded=False,
            ):
                if trade.get('notes'):
                    st.caption(trade['notes'])
                if trade.get('tags'):
                    st.caption(f"Tags: {trade['tags']}")

                col_exit, col_price, col_btn, col_del = st.columns([2, 2, 1, 1])
                with col_exit:
                    exit_date = st.date_input("Exit Date", value=date.today(),
                                              key=f"exit_date_{trade['id']}")
                with col_price:
                    exit_price = st.number_input("Exit Price ($)", min_value=0.01,
                                                 value=float(trade['entry_price']),
                                                 step=0.01, key=f"exit_price_{trade['id']}")
                with col_btn:
                    if st.button("Close", key=f"close_{trade['id']}", use_container_width=True):
                        close_trade(trade['id'], str(exit_date), exit_price)
                        st.rerun()
                with col_del:
                    if st.button("Delete", key=f"del_{trade['id']}", use_container_width=True):
                        delete_trade(trade['id'])
                        st.rerun()

# ── Closed Trades ─────────────────────────────────────────────────────────────
with tab_closed:
    closed = get_closed_trades()
    summary = get_pnl_summary()

    if summary['total_trades'] > 0:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total P&L", f"${summary['total_pnl']:+,.2f}")
        with c2:
            st.metric("Win Rate", f"{summary['win_rate']:.0f}%")
        with c3:
            st.metric("Avg Return", f"{summary['avg_pnl_pct']:+.1f}%")
        with c4:
            st.metric("Trades", str(summary['total_trades']))

        st.markdown("---")

    if not closed:
        st.info("No closed trades yet.")
    else:
        rows = []
        for t in closed:
            spy_ret = get_spy_return(t['entry_date'], t['exit_date']) if t.get('exit_date') else 0
            alpha = round(t['pnl_pct'] - spy_ret, 2)
            rows.append({
                'Ticker': t['ticker'],
                'Dir': t['direction'],
                'Entry Date': t['entry_date'],
                'Entry $': f"${t['entry_price']:.2f}",
                'Exit $': f"${t['exit_price']:.2f}",
                'Shares': t['shares'],
                'P&L %': t['pnl_pct'],
                'P&L $': t['pnl_dollars'],
                'SPY %': spy_ret,
                'Alpha %': alpha,
            })

        df = pd.DataFrame(rows)

        def color_pnl(val):
            if isinstance(val, (int, float)):
                return f"color: {'#22c55e' if val > 0 else '#ef4444'}"
            return ''

        styled = df.style.applymap(color_pnl, subset=['P&L %', 'P&L $', 'Alpha %'])
        st.dataframe(styled, use_container_width=True, hide_index=True)

        # Cumulative P&L equity curve
        if len(closed) >= 2:
            cum_pnl = [0]
            for t in reversed(closed):
                cum_pnl.append(cum_pnl[-1] + t['pnl_dollars'])

            dates_labels = ['Start'] + [t['exit_date'] for t in reversed(closed)]
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates_labels,
                y=cum_pnl,
                mode='lines+markers',
                name='Cumulative P&L',
                line=dict(color='#3b82f6', width=2),
                fill='tozeroy',
                fillcolor='rgba(59,130,246,0.1)',
            ))
            fig.update_layout(
                title='Cumulative P&L ($)',
                height=300,
                margin=dict(l=0, r=0, t=40, b=0),
                template='plotly_white',
                yaxis_title='P&L ($)',
            )
            st.plotly_chart(fig, use_container_width=True)

render_footer()
