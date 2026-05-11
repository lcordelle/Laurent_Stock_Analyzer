"""
Outcome sections — enterprise dashboard layout (shared by Single, Batch, Screener).

Tab 1 · Dashboard: score, analyst, KPIs, fundamentals, peers, headlines
Tab 2 · Forecast & signals: price/volume charts, forecast strip, trading signals
"""

import streamlit as st
import pandas as pd

from components.styling import render_analyst_ranking_panel
from components.enterprise_dashboard import (
    apply_enterprise_dashboard_css,
    render_stock_identity_bar,
    render_executive_kpi_strip,
    render_executive_metrics_verdict,
    render_score_hero,
    render_key_metrics_table,
    render_analyst_consensus_charts,
    render_news_compact,
    render_peers_compact,
    render_factor_grades_panel,
    render_dividend_scorecard_panel,
)


def _safe_float_format(value, format_str="{:.2f}", default="N/A"):
    if value is None:
        return default
    try:
        if isinstance(value, str):
            value = float(value)
        elif not isinstance(value, (int, float)):
            return default
        return format_str.format(value)
    except (ValueError, TypeError):
        return default


def render_outcome_sections(
    ticker,
    data,
    metrics,
    score,
    forecast,
    intrinsic_value,
    news_articles,
    ratings_result,
    trading_signals,
    show_identity_bar=True,
    factor_grades=None,
    dividend_scorecard=None,
    earnings_data=None,
    analyst_report=None,
):
    """
    Four-tab enterprise dashboard. Same structure for single / batch / screener.
    New tabs (Earnings, AI Analyst) only render when data is provided.
    """
    apply_enterprise_dashboard_css()

    if show_identity_bar:
        render_stock_identity_bar(ticker, data)

    tab_dash, tab_fc, tab_earn, tab_ai = st.tabs([
        "Dashboard", "Forecast & signals", "Earnings", "AI Analyst"
    ])

    with tab_dash:
        render_executive_kpi_strip(metrics, forecast, data)
        render_executive_metrics_verdict(
            metrics or {},
            forecast or {},
            score or {},
            data or {},
            trading_signals,
        )
        render_score_hero(ticker, score, metrics, forecast)

        # Factor grades panel (new)
        if factor_grades:
            render_factor_grades_panel(factor_grades)

        st.markdown("---")

        # Dividend scorecard panel (new) — shown before analyst section
        if dividend_scorecard:
            render_dividend_scorecard_panel(dividend_scorecard)
            st.markdown("---")

        st.markdown('<p class="vf-section-label">Analyst view</p>', unsafe_allow_html=True)
        current_price = metrics.get("Current Price", 0) if metrics else 0
        render_analyst_ranking_panel(
            ratings_result,
            current_price,
            ticker,
            data,
            intrinsic_value,
            compact=True,
        )
        render_analyst_consensus_charts(
            ticker,
            data,
            ratings_result,
            intrinsic_value,
            metrics or {},
            float(current_price or 0) or 0.0,
        )
        render_key_metrics_table(metrics or {})
        render_peers_compact(ticker, data, metrics, score)
        render_news_compact(ticker, news_articles or [], limit=10)

    with tab_fc:
        render_forecast_price_strip(forecast, metrics)
        render_charts_subsection_fullscreen(data, metrics, intrinsic_value, ticker, trading_signals)
        st.markdown("---")
        render_signals_subsection_fullscreen(data, metrics, score, intrinsic_value, trading_signals)

    with tab_earn:
        render_earnings_tab(earnings_data, data)

    with tab_ai:
        render_ai_analyst_tab(analyst_report, ticker)


def render_forecast_price_strip(forecast, metrics):
    """One-line institutional forecast context above charts."""
    if not forecast:
        return
    fp = forecast.get("forecast_price")
    ch = forecast.get("forecast_change_pct")
    pr = forecast.get("probability")
    cp = metrics.get("Current Price") if metrics else None
    parts = []
    if cp is not None:
        parts.append(f"**Spot** ${float(cp):.2f}")
    if fp is not None:
        parts.append(f"**Model** ${float(fp):.2f}")
    if ch is not None:
        parts.append(f"**Δ** {float(ch):+.1f}%")
    if pr is not None:
        parts.append(f"**Prob.** {float(pr):.0f}%")
    if parts:
        st.markdown(" · ".join(parts))


def render_charts_subsection_fullscreen(data, metrics, intrinsic_value, ticker="", trading_signals=None):
    """Price & volume — trader essentials, minimal chrome."""
    st.markdown('<p class="vf-section-label">Price action</p>', unsafe_allow_html=True)
    from utils.visualizations import create_price_chart, create_volume_chart

    if data and data.get("history") is not None and len(data.get("history", [])) > 0:
        price_chart = create_price_chart(data, intrinsic_value=intrinsic_value, metrics=metrics)
        if price_chart:
            st.plotly_chart(
                price_chart,
                use_container_width=True,
                height=520,
                config={"displayModeBar": True, "displaylogo": False},
            )
        st.markdown('<p class="vf-section-label">Volume</p>', unsafe_allow_html=True)
        volume_chart = create_volume_chart(data.get("history"), ticker)
        if volume_chart:
            st.plotly_chart(
                volume_chart,
                use_container_width=True,
                height=320,
                config={"displayModeBar": True, "displaylogo": False},
            )
    else:
        st.warning("Chart data not available.")


def render_signals_subsection_fullscreen(data, metrics, score, intrinsic_value, trading_signals):
    """Trading signals + strategy chart."""
    st.markdown('<p class="vf-section-label">Trading signals</p>', unsafe_allow_html=True)
    from utils.visualizations import create_trading_signals_chart, normalize_primary_stance
    from utils.stock_analyzer import StockAnalyzer

    analyzer = st.session_state.get("analyzer", StockAnalyzer())
    signals_result = create_trading_signals_chart(
        data,
        intrinsic_value=intrinsic_value,
        metrics=metrics,
        score=score,
        analyzer=analyzer,
    )

    if not signals_result:
        st.warning("Trading signals not available.")
        return

    signals_fig, trading_signals = signals_result
    st.plotly_chart(
        signals_fig,
        use_container_width=True,
        height=700,
        config={"displayModeBar": True, "displaylogo": False},
    )

    current_price = metrics.get("Current Price", 0) if metrics else 0

    primary = normalize_primary_stance(trading_signals.get("primary_stance"))
    is_buy = primary == "BUY"
    is_sell = primary == "SELL"
    entry_price = current_price
    entry_reason = "Current"
    if is_buy and trading_signals.get("buy_signals"):
        b = min(trading_signals["buy_signals"], key=lambda x: x["price"])
        entry_price, entry_reason = b["price"], b.get("type", "Buy")
    elif is_sell and trading_signals.get("sell_signals"):
        b = max(trading_signals["sell_signals"], key=lambda x: x["price"])
        entry_price, entry_reason = b["price"], b.get("type", "Sell")
    sl_price = trading_signals.get("stop_loss", {}).get("price") if trading_signals.get("stop_loss") else None
    tp_list = trading_signals.get("take_profit", [])
    if not sl_price and entry_price:
        if is_sell:
            sl_price = entry_price * 1.05
        elif is_buy:
            sl_price = entry_price * 0.95
        else:
            sl_price = entry_price * 0.97
    if not tp_list and entry_price:
        if is_sell:
            tp_list = [
                {"price": entry_price * 0.90, "label": "TP1"},
                {"price": entry_price * 0.80, "label": "TP2"},
                {"price": intrinsic_value if intrinsic_value and intrinsic_value < entry_price else entry_price * 0.70, "label": "TP3"},
            ]
        elif is_buy:
            tp_list = [
                {"price": entry_price * 1.10, "label": "TP1"},
                {"price": entry_price * 1.20, "label": "TP2"},
                {"price": intrinsic_value if intrinsic_value and intrinsic_value > entry_price else entry_price * 1.30, "label": "TP3"},
            ]
        else:
            tp_list = [
                {"price": entry_price * 1.03, "label": "Ref↑"},
                {"price": entry_price * 0.97, "label": "Ref↓"},
            ]
    tp1 = tp_list[0]["price"] if len(tp_list) > 0 else None
    tp2 = tp_list[1]["price"] if len(tp_list) > 1 else None
    tp3 = tp_list[2]["price"] if len(tp_list) > 2 else None
    risk_pct = abs((entry_price - sl_price) / entry_price * 100) if entry_price and sl_price else None
    if tp_list:
        if is_buy:
            best_tp = max(tp_list, key=lambda x: x["price"])["price"]
        elif is_sell:
            best_tp = min(tp_list, key=lambda x: x["price"])["price"]
        else:
            best_tp = tp_list[0]["price"]
    else:
        best_tp = None
    reward_pct = abs((best_tp - entry_price) / entry_price * 100) if entry_price and best_tp else None
    rec = primary
    rec_color = "#10b981" if rec == "BUY" else "#ef4444" if rec == "SELL" else "#f59e0b"
    rec_bg = "rgba(16, 185, 129, 0.12)" if rec == "BUY" else "rgba(239, 68, 68, 0.12)" if rec == "SELL" else "rgba(245, 158, 11, 0.12)"
    conf = trading_signals.get("confidence_score", 0)
    conf_level = trading_signals.get("confidence_level", "Low")
    st.markdown(
        f"""<div style="background: {rec_bg}; border: 1px solid {rec_color}; border-radius: 10px; padding: 0.85rem 1.1rem; margin-bottom: 0.75rem;">
            <span style="font-size:0.7rem;text-transform:uppercase;color:#64748b;">Stance</span>
            <p style="margin:0.15rem 0 0 0;font-size:1.35rem;font-weight:800;color:{rec_color};">{rec}</p>
            <p style="margin:0.2rem 0 0 0;font-size:0.8rem;color:#475569;">{entry_reason} · Conf. {conf:.0f}/100 ({conf_level})</p>
        </div>
        <div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:0.5rem;font-size:0.8rem;margin-bottom:1rem;">
            <div><span style="color:#64748b;">Entry</span><br/><strong>${entry_price:.2f}</strong></div>
            <div><span style="color:#64748b;">Stop</span><br/><strong style="color:#ef4444;">{f"${sl_price:.2f}" if sl_price else "—"}</strong></div>
            <div><span style="color:#64748b;">TP1 / TP2</span><br/><strong style="color:#10b981;">{f"${tp1:.2f}" if tp1 else "—"} / {f"${tp2:.2f}" if tp2 else "—"}</strong></div>
            <div><span style="color:#64748b;">Risk / Rwd</span><br/><strong>{f"{risk_pct:.1f}%" if risk_pct is not None else "—"} / {f"{reward_pct:.1f}%" if reward_pct is not None else "—"}</strong></div>
        </div>""",
        unsafe_allow_html=True,
    )

    if trading_signals.get("multi_timeframe"):
        with st.expander("Multi-timeframe", expanded=False):
            mtf = trading_signals["multi_timeframe"]
            for tf_name, tf_data in mtf.items():
                tr = tf_data.get("trend", "Neutral")
                st.caption(f"**{tf_name}** · {tr} · RSI {tf_data.get('rsi', 0):.0f}")

    from utils.trading_strategy_chart import create_trading_strategy_chart

    strategy_chart = create_trading_strategy_chart(
        data,
        trading_signals=trading_signals,
        intrinsic_value=intrinsic_value,
        metrics=metrics,
        score=score,
    )
    if strategy_chart:
        st.plotly_chart(
            strategy_chart,
            use_container_width=True,
            height=620,
            config={"displayModeBar": True, "displaylogo": False},
        )


# =============================================================================
# EARNINGS TAB
# =============================================================================

def render_earnings_tab(earnings_data, stock_data=None):
    """Render the Earnings tab with EPS/revenue surprise history and forward estimates."""
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    if not earnings_data or not earnings_data.get("data_available"):
        st.info("Earnings estimate data is not available from Yahoo Finance for this ticker.")
        return

    # Next earnings date
    ned = earnings_data.get("next_earnings_date")
    if ned:
        st.caption(f"Next earnings date: **{ned}**")

    # Summary pills
    beat_rate = earnings_data.get("beat_rate_4q")
    avg_surp = earnings_data.get("avg_surprise_pct_4q")
    if beat_rate is not None or avg_surp is not None:
        cols = st.columns(4)
        if beat_rate is not None:
            cols[0].metric("Beat Rate (4Q)", f"{beat_rate:.0f}%")
        if avg_surp is not None:
            cols[1].metric("Avg EPS Surprise (4Q)", f"{avg_surp:+.1f}%")

    # EPS Surprise History chart
    eps_hist = earnings_data.get("eps_history", [])
    if eps_hist:
        quarters = [e["quarter"] for e in eps_hist]
        estimates = [e.get("estimate") for e in eps_hist]
        actuals = [e.get("actual") for e in eps_hist]
        surprise_pcts = [e.get("surprise_pct") for e in eps_hist]
        bar_colors = [
            "#10b981" if e.get("beat") else "#ef4444" if e.get("beat") is False else "#94a3b8"
            for e in eps_hist
        ]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Estimate", x=quarters, y=estimates,
            marker_color="#cbd5e1", opacity=0.7,
        ))
        fig.add_trace(go.Bar(
            name="Actual", x=quarters, y=actuals,
            marker_color=bar_colors, opacity=0.9,
            text=[f"{s:+.1f}%" if s is not None else "" for s in surprise_pcts],
            textposition="outside",
        ))
        fig.update_layout(
            title="EPS: Actual vs Estimate",
            barmode="overlay",
            template="plotly_white",
            height=300,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=40, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Forward EPS estimates table
    forward_eps = earnings_data.get("forward_eps", {})
    if forward_eps:
        st.markdown('<p class="vf-section-label">Forward EPS Estimates</p>', unsafe_allow_html=True)
        rows = []
        for period, d in forward_eps.items():
            avg = d.get("avg")
            low = d.get("low")
            high = d.get("high")
            n = d.get("n_analysts")
            growth = d.get("growth")
            rows.append({
                "Period": period,
                "Avg EPS": f"${avg:.2f}" if avg else "N/A",
                "Low": f"${low:.2f}" if low else "N/A",
                "High": f"${high:.2f}" if high else "N/A",
                "Analysts": int(n) if n else "N/A",
                "Growth": f"{growth:.1%}" if growth else "N/A",
            })
        if rows:
            import pandas as pd
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Forward Revenue estimates table
    forward_rev = earnings_data.get("forward_revenue", {})
    if forward_rev:
        st.markdown('<p class="vf-section-label">Forward Revenue Estimates</p>', unsafe_allow_html=True)
        rows = []
        for period, d in forward_rev.items():
            avg = d.get("avg")
            growth = d.get("growth")
            n = d.get("n_analysts")
            rows.append({
                "Period": period,
                "Avg Revenue": f"${avg/1e9:.2f}B" if avg and avg > 1e6 else f"${avg:.0f}" if avg else "N/A",
                "Analysts": int(n) if n else "N/A",
                "Growth": f"{growth:.1%}" if growth else "N/A",
            })
        if rows:
            import pandas as pd
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # EPS revision trend mini-chart
    eps_trend = earnings_data.get("eps_trend", {})
    if eps_trend:
        st.markdown('<p class="vf-section-label">EPS Estimate Revision Trend</p>', unsafe_allow_html=True)
        fig2 = go.Figure()
        x_labels = ["90d ago", "60d ago", "30d ago", "7d ago", "Current"]
        keys_map = ["90d_ago", "60d_ago", "30d_ago", "7d_ago", "current"]
        colors_list = ["#1d4ed8", "#10b981", "#f59e0b", "#8b5cf6"]
        for i, (period, d) in enumerate(list(eps_trend.items())[:4]):
            y_vals = [d.get(k) for k in keys_map]
            if any(v is not None for v in y_vals):
                fig2.add_trace(go.Scatter(
                    x=x_labels, y=y_vals,
                    name=period, mode="lines+markers",
                    line=dict(color=colors_list[i % len(colors_list)], width=2),
                    marker=dict(size=5),
                    connectgaps=True,
                ))
        fig2.update_layout(
            title="Analyst EPS Estimate Revisions",
            template="plotly_white", height=260,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=40, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    # EPS revisions summary
    eps_revisions = earnings_data.get("eps_revisions", {})
    if eps_revisions:
        st.markdown('<p class="vf-section-label">Estimate Revision Counts</p>', unsafe_allow_html=True)
        rows = []
        for period, d in eps_revisions.items():
            rows.append({
                "Period": period,
                "Up (7d)": d.get("up_7d", 0),
                "Down (7d)": d.get("down_7d", 0),
                "Up (30d)": d.get("up_30d", 0),
                "Down (30d)": d.get("down_30d", 0),
            })
        if rows:
            import pandas as pd
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Financial history charts in expander
    try:
        financials = stock_data.get("financials") if stock_data else None
        cashflow = stock_data.get("cashflow") if stock_data else None
        if financials is not None or cashflow is not None:
            with st.expander("Financial History (Annual)", expanded=False):
                from utils.visualizations import create_financial_history_chart
                for chart_type, label in [
                    ("revenue", "Revenue"), ("margins", "Margins"),
                    ("earnings", "Earnings"), ("fcf", "Free Cash Flow"),
                ]:
                    fig = create_financial_history_chart(financials, cashflow, chart_type)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    except Exception:
        pass


# =============================================================================
# AI ANALYST TAB
# =============================================================================

def render_ai_analyst_tab(analyst_report, ticker):
    """Render the AI Analyst tab with AI-generated Bulls/Bears/Thesis report."""
    if not analyst_report:
        _render_ai_setup_guide()
        return

    error = analyst_report.get("error")
    sections = analyst_report.get("sections", {})

    if error == "no_provider":
        _render_ai_setup_guide()
        return

    if error and not sections.get("executive_summary"):
        st.error(f"Report generation failed: {error}")
        _render_ai_setup_guide()
        return

    # Header
    generated_at = analyst_report.get("generated_at", "")
    model = analyst_report.get("model", "")
    provider = analyst_report.get("provider", "")
    ts = generated_at[:16].replace("T", " ") if generated_at else ""
    st.markdown(f"### AI Analyst Report — {ticker}")
    if ts and model:
        provider_label = {"groq": "Groq (free)", "anthropic": "Anthropic", "ollama": "Ollama (local)"}.get(provider, provider)
        st.caption(f"Generated {ts} · {model} via {provider_label}")

    st.markdown("---")

    exec_sum = sections.get("executive_summary")
    if exec_sum:
        st.markdown('<p class="vf-section-label">Executive Summary</p>', unsafe_allow_html=True)
        st.markdown(f'<div class="vf-exec-verdict">{exec_sum}</div>', unsafe_allow_html=True)

    st.markdown("")

    bulls = sections.get("bulls_say", [])
    bears = sections.get("bears_say", [])
    if bulls or bears:
        col_bull, col_bear = st.columns(2)
        with col_bull:
            st.markdown("**Bulls Say**")
            for b in bulls:
                st.markdown(f"&#10003; {b}")
        with col_bear:
            st.markdown("**Bears Say**")
            for b in bears:
                st.markdown(f"&#10007; {b}")

    st.markdown("")

    key_risks = sections.get("key_risks")
    if key_risks:
        st.markdown('<p class="vf-section-label">Key Risks</p>', unsafe_allow_html=True)
        st.markdown(
            f'<div style="padding:0.75rem 1rem;background:#fffbeb;border-left:4px solid #f59e0b;'
            f'border-radius:6px;font-size:0.9rem;color:#0f172a;line-height:1.45;">{key_risks}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("")

    thesis = sections.get("investment_thesis")
    if thesis:
        st.markdown('<p class="vf-section-label">Investment Thesis</p>', unsafe_allow_html=True)
        st.markdown(f'<div class="vf-exec-verdict">{thesis}</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.caption(f"Generated by {model} · Data from Yahoo Finance · Not investment advice")


def _render_ai_setup_guide():
    """Show setup options when no AI provider is configured."""
    st.markdown("### AI Analyst Report — Setup Required")
    st.markdown(
        "Configure one of the options below to enable AI-generated analyst reports. "
        "All options are **free**."
    )

    st.markdown("#### Option 1 — Groq (Recommended: free cloud, ~1 second)")
    st.markdown(
        "Groq's free tier runs **Llama 3.3 70B** — no credit card required.\n\n"
        "1. Sign up free at [console.groq.com](https://console.groq.com)\n"
        "2. Create an API key\n"
        "3. Add to your `.env` file:\n"
        "```\nGROQ_API_KEY=gsk_...\n```\n"
        "4. Restart the app"
    )

    st.markdown("---")

    st.markdown("#### Option 2 — Ollama (Fully local, zero cost, no account)")
    st.markdown(
        "Runs a model on your Mac — completely private, works offline.\n\n"
        "```bash\n# Install Ollama\nbrew install ollama\n\n"
        "# Pull a model (3B = fast, 8B = better quality)\nollama pull llama3.2\n\n"
        "# Start the server\nollama serve\n```\n\n"
        "No `.env` changes needed — the app detects Ollama automatically."
    )

    st.markdown("---")

    st.markdown("#### Option 3 — Anthropic Claude (Paid, highest quality)")
    st.markdown(
        "```\nANTHROPIC_API_KEY=sk-ant-...\n```\n"
        "Get a key at [console.anthropic.com](https://console.anthropic.com)."
    )
