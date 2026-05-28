"""
Backtesting — validate trading strategies on historical data
"""

import streamlit as st
import plotly.graph_objects as go
from utils.auth import require_auth
from utils.backtesting import run_backtest, STRATEGIES
from components.styling import apply_platform_theme, render_header, render_footer
from components.navigation import render_top_navigation
require_auth()

st.set_page_config(
    page_title="Backtesting",
    page_icon="⏪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_platform_theme()
render_top_navigation()
render_header("Backtesting", "Simulate strategies on historical data · compare vs SPY benchmark")

# ── Controls ──────────────────────────────────────────────────────────────────
with st.form("backtest_form"):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        bt_ticker = st.text_input("Ticker", value="AAPL", placeholder="AAPL").upper()
    with c2:
        bt_strategy = st.selectbox("Strategy", list(STRATEGIES.keys()),
                                   format_func=lambda k: STRATEGIES[k])
    with c3:
        bt_period = st.selectbox("Period", ["1y", "2y", "3y", "5y"], index=1)
    with c4:
        bt_capital = st.number_input("Initial Capital ($)", value=10000.0, step=1000.0)
    run_bt = st.form_submit_button("Run Backtest", use_container_width=True)

# Strategy descriptions
st.caption({
    'ma_crossover': "Buy when SMA(20) crosses above SMA(50). Sell when it crosses below.",
    'rsi': "Buy when RSI(14) drops below 30 (oversold). Sell when RSI rises above 70 (overbought).",
    'golden_cross': "Buy when SMA(50) crosses above SMA(200). Sell when it crosses below.",
}.get(bt_strategy if 'bt_strategy' in dir() else 'ma_crossover', ''))

if run_bt and bt_ticker:
    with st.spinner(f"Running backtest on {bt_ticker} ({bt_period}, {STRATEGIES[bt_strategy]})..."):
        result = run_backtest(bt_ticker, bt_strategy, bt_period, bt_capital)

    if result.get('error'):
        st.error(f"Backtest failed: {result['error']}")
    else:
        m = result['metrics']

        # KPI cards
        c1, c2, c3, c4, c5 = st.columns(5)
        delta_color = "normal" if m['total_return'] >= 0 else "inverse"
        with c1:
            st.metric("Strategy Return", f"{m['total_return']:+.1f}%",
                      delta=f"{m['alpha']:+.1f}% vs SPY")
        with c2:
            st.metric("SPY Return", f"{m['spy_return']:+.1f}%")
        with c3:
            st.metric("Sharpe Ratio", f"{m['sharpe']:.2f}")
        with c4:
            st.metric("Max Drawdown", f"{m['max_drawdown']:.1f}%")
        with c5:
            st.metric("Win Rate", f"{m['win_rate']:.0f}%",
                      help=f"From {m['total_trades']} completed trades")

        st.markdown(f"**Final value:** ${m['final_value']:,.2f} "
                    f"(started with ${m['initial_capital']:,.0f})")

        # Equity curve chart
        if result['equity_curve'] and result['spy_curve']:
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=[p['date'] for p in result['equity_curve']],
                y=[p['value'] for p in result['equity_curve']],
                mode='lines',
                name=f"{bt_ticker} Strategy",
                line=dict(color='#3b82f6', width=2),
            ))
            fig.add_trace(go.Scatter(
                x=[p['date'] for p in result['spy_curve']],
                y=[p['value'] for p in result['spy_curve']],
                mode='lines',
                name='SPY Benchmark',
                line=dict(color='#9ca3af', width=1.5, dash='dash'),
            ))

            fig.add_hline(y=bt_capital, line_dash='dot',
                          line_color='#6b7280', opacity=0.5,
                          annotation_text='Initial Capital')

            fig.update_layout(
                title=f"{bt_ticker} — {STRATEGIES[bt_strategy]} ({bt_period})",
                height=420,
                template='plotly_white',
                xaxis_title='Date',
                yaxis_title='Portfolio Value ($)',
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                margin=dict(l=0, r=0, t=60, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)

        st.caption(f"Strategy: {result['strategy_label']} | "
                   f"Period: {result['period']} | "
                   f"Trades executed: {m['total_trades']}")

render_footer()
