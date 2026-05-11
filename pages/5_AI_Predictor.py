"""
AI Price Predictor Page
9-indicator weighted signal model for directional stock prediction
"""

import streamlit as st
from utils.auth import require_auth

require_auth()

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils.stock_analyzer import StockAnalyzer
from utils.ai_predictor import AIPredictor
from components.styling import apply_platform_theme, render_header, render_footer
from components.navigation import render_top_navigation

st.set_page_config(
    page_title="AI Price Predictor",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

apply_platform_theme()
render_top_navigation()

if 'analyzer' not in st.session_state:
    st.session_state.analyzer = StockAnalyzer()
if 'ai_predictor' not in st.session_state:
    st.session_state.ai_predictor = AIPredictor()

analyzer  = st.session_state.analyzer
predictor = st.session_state.ai_predictor

render_header("AI Price Predictor", "Weighted signal model across 9 technical indicators · 5-day horizon")

with st.form("predictor_form", clear_on_submit=False):
    ticker = st.text_input(
        "Stock Ticker or Company Name", value="",
        key="predictor_ticker",
        placeholder="e.g., AAPL, NVDA, Tesla"
    ).strip()
    submitted = st.form_submit_button("🤖 Run AI Prediction", use_container_width=True)

if submitted and ticker:
    with st.spinner(f"Running AI prediction for {ticker.upper()}..."):
        data = analyzer.get_stock_data(ticker, period="1y")

        if not data or data.get('history') is None or len(data.get('history', [])) < 50:
            st.error(f"Could not fetch sufficient data for **{ticker.upper()}**. Try a different ticker.")
            st.stop()

        hist = analyzer.calculate_technical_indicators(data['history'].copy())
        data['history'] = hist

        score    = analyzer.calculate_score(data)
        metrics  = analyzer.get_key_metrics(data)
        forecast = analyzer.calculate_forecast(data, metrics, score)
        pred     = predictor.predict(hist, metrics, score, forecast)

    # ── Direction metadata ────────────────────────────────────────────────
    direction  = pred['direction']
    confidence = pred['confidence']
    bull_score = pred['bull_score']
    pt         = pred['price_targets']
    current    = pt['current']

    COLORS = {
        'BULL':    '#10b981',
        'BEAR':    '#ef4444',
        'NEUTRAL': '#f59e0b',
    }
    LABELS = {
        'BULL': 'BULLISH',
        'BEAR': 'BEARISH',
        'NEUTRAL': 'NEUTRAL',
    }
    color = COLORS[direction]

    st.markdown("---")

    # ── Section 1: Prediction Hero ────────────────────────────────────────
    hero_left, hero_right = st.columns([4, 6])

    with hero_left:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=bull_score,
            title={'text': "Bull Score", 'font': {'size': 15, 'color': '#475569'}},
            number={'font': {'size': 40, 'color': color}},
            delta={
                'reference': 50,
                'increasing': {'color': '#10b981'},
                'decreasing': {'color': '#ef4444'},
            },
            gauge={
                'axis': {
                    'range': [0, 100],
                    'tickwidth': 1,
                    'tickcolor': '#cbd5e1',
                    'tickvals': [0, 25, 50, 75, 100],
                    'ticktext': ['0', 'Bear', '50', 'Bull', '100'],
                    'tickfont': {'color': '#475569', 'size': 11},
                },
                'bar': {'color': color, 'thickness': 0.25},
                'bgcolor': '#f8fafc',
                'borderwidth': 0,
                'steps': [
                    {'range': [0,  25], 'color': 'rgba(239,68,68,0.15)'},
                    {'range': [25, 50], 'color': 'rgba(239,68,68,0.06)'},
                    {'range': [50, 75], 'color': 'rgba(16,185,129,0.06)'},
                    {'range': [75, 100],'color': 'rgba(16,185,129,0.15)'},
                ],
                'threshold': {
                    'line': {'color': '#1e293b', 'width': 2},
                    'thickness': 0.75,
                    'value': bull_score,
                },
            }
        ))
        fig_gauge.update_layout(
            height=290,
            margin=dict(l=20, r=20, t=50, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'family': 'Inter, sans-serif'},
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

        st.markdown(f"""
        <div style="text-align:center; margin-top:-8px;">
            <p style="color:#475569; font-size:0.75rem; font-weight:600; margin:0;
                      text-transform:uppercase; letter-spacing:0.06em;">Confidence</p>
            <div style="background:#e2e8f0; border-radius:100px; height:8px; margin:6px 0;">
                <div style="background:{color}; width:{confidence:.0f}%; height:8px; border-radius:100px;"></div>
            </div>
            <p style="color:{color}; font-size:1.4rem; font-weight:700; margin:0;">{confidence:.0f}%</p>
        </div>
        """, unsafe_allow_html=True)

    with hero_right:
        company_name = data.get('info', {}).get('longName', ticker.upper())
        st.markdown(f"""
        <p style="color:#475569; font-size:0.85rem; margin:0 0 0.5rem;">{company_name}</p>
        <div style="display:inline-block; background:{color}; color:white;
                    padding:0.4rem 2rem; border-radius:100px; font-size:1.6rem;
                    font-weight:800; letter-spacing:0.1em; margin-bottom:1rem;">
            {LABELS[direction]}
        </div>
        <p style="color:#475569; font-size:0.85rem; margin:0 0 1.5rem;">
            AI Prediction &nbsp;·&nbsp; 5-Day Horizon &nbsp;·&nbsp;
            Volatility: {pred['volatility_pct']:.1f}% annualised
        </p>
        """, unsafe_allow_html=True)

        t1, t2, t3 = st.columns(3)
        for col, label, price, icon in [
            (t1, "Conservative", pt['conservative'], "▸"),
            (t2, "Base Target",  pt['base'],         "▸▸"),
            (t3, "Aggressive",   pt['aggressive'],   "▸▸▸"),
        ]:
            pct = (price - current) / current * 100 if current else 0
            sign_str = f"+{pct:.1f}%" if pct >= 0 else f"{pct:.1f}%"
            pct_color = '#10b981' if pct >= 0 else '#ef4444'
            col.markdown(f"""
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px;
                        padding:0.9rem; text-align:center;">
                <p style="color:#475569; font-size:0.7rem; font-weight:600; margin:0 0 0.25rem;
                           text-transform:uppercase; letter-spacing:0.05em;">{icon} {label}</p>
                <p style="color:#0f172a; font-size:1.15rem; font-weight:700; margin:0;">${price:.2f}</p>
                <p style="color:{pct_color}; font-size:0.85rem; font-weight:600; margin:0;">{sign_str}</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<p style='color:#475569; font-size:0.8rem; font-weight:600; margin:1.25rem 0 0.5rem; text-transform:uppercase; letter-spacing:0.05em;'>Trade Setup</p>", unsafe_allow_html=True)

        sl_pct   = (pred['stop_loss'] - pred['entry']) / pred['entry'] * 100 if pred['entry'] else 0
        tp1_pct  = (pred['tp1'] - pred['entry']) / pred['entry'] * 100 if pred['entry'] else 0
        tp2_pct  = (pred['tp2'] - pred['entry']) / pred['entry'] * 100 if pred['entry'] else 0

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Entry",       f"${pred['entry']:.2f}")
        m2.metric("Stop Loss",   f"${pred['stop_loss']:.2f}", delta=f"{sl_pct:.1f}%",  delta_color="inverse")
        m3.metric("TP1",         f"${pred['tp1']:.2f}",       delta=f"{tp1_pct:+.1f}%")
        m4.metric("TP2",         f"${pred['tp2']:.2f}",       delta=f"{tp2_pct:+.1f}%")
        m5.metric("Risk/Reward", f"{pred['risk_reward']:.1f}x")

    # ── Section 2: Signal Breakdown ───────────────────────────────────────
    st.markdown("---")
    st.markdown("### Signal Breakdown")

    signals     = pred['signals']
    names       = list(signals.keys())
    contribs    = [signals[k]['raw_score'] * signals[k]['weight'] for k in names]
    bar_colors  = [
        '#10b981' if signals[k]['signal'] == 'bullish' else
        '#ef4444' if signals[k]['signal'] == 'bearish' else '#f59e0b'
        for k in names
    ]

    fig_bar = go.Figure(go.Bar(
        y=names,
        x=contribs,
        orientation='h',
        marker_color=bar_colors,
        marker_line_width=0,
        text=[f"{v:+.3f}" for v in contribs],
        textposition='outside',
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Weighted contribution: %{x:.4f}<br>"
            "Raw score: %{customdata[0]:.2f}<br>"
            "Signal: %{customdata[1]}<extra></extra>"
        ),
        customdata=[[signals[k]['raw_score'], signals[k]['signal']] for k in names],
    ))
    fig_bar.add_vline(x=0, line_color='#475569', line_width=1.5, opacity=0.5)
    fig_bar.update_layout(
        height=360,
        margin=dict(l=10, r=70, t=10, b=20),
        xaxis=dict(
            range=[-0.22, 0.22],
            zeroline=False,
            gridcolor='#f1f5f9',
            title='Weighted Contribution to Bull Score',
            tickfont={'color': '#475569', 'size': 11},
            title_font={'color': '#475569', 'size': 12},
        ),
        yaxis=dict(
            tickfont={'color': '#0f172a', 'size': 13},
            gridcolor='rgba(0,0,0,0)',
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': 'Inter, sans-serif'},
        showlegend=False,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    table_rows = []
    for k in names:
        s = signals[k]
        table_rows.append({
            'Indicator':  k,
            'Value':      f"{s['value']:.2f}",
            'Raw Score':  f"{s['raw_score']:+.2f}",
            'Weight':     f"{s['weight']*100:.0f}%",
            'Weighted':   f"{s['raw_score'] * s['weight']:+.4f}",
            'Signal':     s['signal'].upper(),
        })
    df = pd.DataFrame(table_rows)

    def _color_signal(val):
        if val == 'BULLISH': return 'color: #10b981; font-weight: 600'
        if val == 'BEARISH': return 'color: #ef4444; font-weight: 600'
        return 'color: #f59e0b; font-weight: 600'

    st.dataframe(
        df.style.applymap(_color_signal, subset=['Signal']),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        f"Annualised volatility: {pred['volatility_pct']:.1f}%  ·  "
        f"Composite weighted score: {pred['weighted_sum']:+.4f}  ·  "
        f"Direction threshold: ±0.15"
    )

render_footer()
