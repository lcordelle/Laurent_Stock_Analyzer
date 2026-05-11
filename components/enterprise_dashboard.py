"""
Enterprise dashboard layout: executive KPIs, grouped Dashboard vs Forecast & Signals.
Used by Single Analysis, Batch Comparison, and Stock Screener (same structure).
"""

import html
import streamlit as st
import pandas as pd

import config as cfg


def apply_enterprise_dashboard_css():
    """Inject styles for KPI strip, dashboard sections, and tab hierarchy."""
    st.markdown(
        """
        <style>
        .vf-dash-wrap { margin-bottom: 1.25rem; }
        .vf-section-label {
            font-size: 0.6875rem; font-weight: 700; letter-spacing: 0.12em;
            text-transform: uppercase; color: #64748b; margin: 0 0 0.5rem 0;
        }
        .vf-kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(7.5rem, 1fr));
            gap: 0.5rem;
            margin-bottom: 1rem;
        }
        .vf-kpi-cell {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 0.5rem 0.65rem;
            text-align: center;
        }
        .vf-kpi-cell .vf-k {
            font-size: 0.65rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.06em;
            margin: 0 0 0.2rem 0;
        }
        .vf-kpi-cell .vf-v {
            font-size: 1rem; font-weight: 700; color: #0f172a; margin: 0;
        }
        .vf-kpi-cell .vf-sub { font-size: 0.7rem; color: #64748b; margin: 0.15rem 0 0 0; }
        .vf-score-hero {
            display: flex; align-items: stretch; gap: 1rem; flex-wrap: wrap;
            margin-bottom: 1rem;
        }
        .vf-score-big {
            min-width: 8rem; text-align: center; padding: 1rem 1.25rem;
            border-radius: 12px; border: 2px solid;
            background: #fff;
        }
        .vf-metric-table { width: 100%; border-collapse: collapse; font-size: 0.8125rem; }
        .vf-metric-table th { text-align: left; color: #64748b; font-weight: 600; padding: 0.35rem 0.5rem; border-bottom: 1px solid #e2e8f0; }
        .vf-metric-table td { padding: 0.35rem 0.5rem; border-bottom: 1px solid #f1f5f9; color: #0f172a; }
        .vf-metric-table td:last-child { text-align: right; font-weight: 600; }
        .vf-identity {
            margin-bottom: 1rem; padding-bottom: 0.75rem; border-bottom: 1px solid #e2e8f0;
        }
        .vf-identity h2 { margin: 0; font-size: 1.35rem; font-weight: 700; color: #0f172a; letter-spacing: -0.02em; }
        .vf-identity .meta { font-size: 0.8125rem; color: #64748b; margin-top: 0.25rem; }
        .vf-kpi-cell.vf-good { background: #ecfdf5 !important; border-color: #86efac !important; }
        .vf-kpi-cell.vf-mid { background: #fffbeb !important; border-color: #fcd34d !important; }
        .vf-kpi-cell.vf-poor { background: #fef2f2 !important; border-color: #fca5a5 !important; }
        .vf-kpi-cell.vf-neutral { background: #f8fafc !important; border-color: #e2e8f0 !important; }
        .vf-metric-table tr.vf-good td { background: #f0fdf4; border-left: 3px solid #22c55e; }
        .vf-metric-table tr.vf-mid td { background: #fffbeb; border-left: 3px solid #eab308; }
        .vf-metric-table tr.vf-poor td { background: #fef2f2; border-left: 3px solid #ef4444; }
        .vf-metric-table tr.vf-neutral td { border-left: 3px solid #e2e8f0; }
        .vf-bench-legend { font-size: 0.7rem; color: #64748b; margin: 0.35rem 0 0.75rem 0; }
        .vf-news-item { margin-bottom: 1.1rem; padding-bottom: 0.85rem; border-bottom: 1px solid #e2e8f0; }
        .vf-news-item:last-child { border-bottom: none; }
        .vf-news-sum { font-size: 0.8125rem; color: #475569; line-height: 1.5; margin: 0.35rem 0 0 0; padding-left: 0.25rem; }
        .vf-exec-wrap {
            background: linear-gradient(180deg, #f8fafc 0%, #fff 100%);
            border: 1px solid #e2e8f0; border-radius: 10px; padding: 1rem 1.15rem; margin: 0.75rem 0 1rem 0;
        }
        .vf-exec-verdict {
            margin-top: 0.85rem; padding: 0.75rem 1rem; background: #eff6ff; border-left: 4px solid #2563eb;
            border-radius: 6px; font-size: 0.9rem; color: #0f172a; line-height: 1.45;
        }
        .vf-trade-plan {
            margin-top: 0.75rem; padding: 0.75rem 1rem; background: #f0fdf4; border: 1px solid #86efac;
            border-radius: 8px; font-size: 0.85rem; color: #14532d; line-height: 1.5;
        }
        .vf-trade-plan .tag {
            display: inline-block; font-size: 0.65rem; font-weight: 700; letter-spacing: 0.08em;
            text-transform: uppercase; color: #166534; margin-bottom: 0.35rem;
        }
        /* ── Factor / Dividend Grade Pills ─────────────────────────── */
        .vf-grade-panel {
            display: flex; gap: 1rem; flex-wrap: wrap; align-items: flex-start;
            margin: 0.5rem 0 1rem 0;
        }
        .vf-grade-item { text-align: center; min-width: 3.5rem; }
        .vf-grade-pill {
            display: inline-flex; align-items: center; justify-content: center;
            width: 2.6rem; height: 2.6rem; border-radius: 50%;
            font-size: 0.72rem; font-weight: 800; color: white; cursor: default;
        }
        .vf-grade-label {
            font-size: 0.58rem; text-transform: uppercase; letter-spacing: 0.08em;
            color: #64748b; margin: 0.25rem 0 0 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _fmt_num(v, fmt="{:.2f}", default="—"):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return default
    try:
        if isinstance(v, str):
            v = float(v.replace("%", "").strip())
        return fmt.format(float(v))
    except (ValueError, TypeError):
        return default


def _quality_bucket_pe(pe: float) -> str:
    """P/E vs typical best-in-class band (value + quality)."""
    if pe is None or pd.isna(pe) or pe <= 0:
        return "neutral"
    if pe < 5:
        return "mid"
    if cfg.PE_RATIO_MIN_IDEAL <= pe <= cfg.PE_RATIO_MAX_IDEAL:
        return "good"
    if cfg.PE_RATIO_MIN_GOOD <= pe < cfg.PE_RATIO_MIN_IDEAL or cfg.PE_RATIO_MAX_IDEAL < pe <= cfg.PE_RATIO_MAX_GOOD:
        return "mid"
    if pe > cfg.PE_RATIO_MAX_FAIR or pe < 0:
        return "poor"
    return "mid"


def _quality_bucket_peg(peg: float) -> str:
    if peg is None or pd.isna(peg) or peg <= 0:
        return "neutral"
    if peg <= 1.0:
        return "good"
    if peg <= 2.0:
        return "mid"
    return "poor"


def _quality_bucket_roe(roe: float) -> str:
    if roe is None or pd.isna(roe):
        return "neutral"
    if roe >= cfg.ROE_EXCELLENT:
        return "good"
    if roe >= cfg.ROE_FAIR:
        return "mid"
    return "poor"


def _quality_bucket_gm(gm: float) -> str:
    if gm is None or pd.isna(gm):
        return "neutral"
    if gm >= cfg.GROSS_MARGIN_GOOD:
        return "good"
    if gm >= cfg.GROSS_MARGIN_FAIR:
        return "mid"
    return "poor"


def _quality_bucket_rev_growth(rg: float) -> str:
    if rg is None or pd.isna(rg):
        return "neutral"
    if rg >= cfg.REVENUE_GROWTH_GOOD:
        return "good"
    if rg >= cfg.REVENUE_GROWTH_FAIR:
        return "mid"
    return "poor"


def _quality_bucket_beta(beta: float) -> str:
    """Near market beta = balanced; high beta = risk."""
    if beta is None or pd.isna(beta) or beta <= 0:
        return "neutral"
    if 0.85 <= beta <= 1.25:
        return "good"
    if 0.5 <= beta < 0.85 or 1.25 < beta <= 1.6:
        return "mid"
    return "poor"


def _quality_bucket_rsi(rsi: float) -> str:
    if rsi is None or pd.isna(rsi):
        return "neutral"
    if 40 <= rsi <= 60:
        return "good"
    if 30 <= rsi < 40 or 60 < rsi <= 70:
        return "mid"
    return "poor"


def _quality_bucket_fwd_delta(pct: float) -> str:
    if pct is None or pd.isna(pct):
        return "neutral"
    if pct >= 5:
        return "good"
    if pct >= -5:
        return "mid"
    return "poor"


def _quality_for_kpi_strip(label: str, raw) -> str:
    """Map strip label to quality class."""
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return "neutral"
    try:
        x = float(raw)
    except (TypeError, ValueError):
        return "neutral"
    if label == "P/E":
        return _quality_bucket_pe(x)
    if label == "Fwd P/E":
        return _quality_bucket_pe(x)
    if label == "PEG":
        return _quality_bucket_peg(x)
    if label == "ROE":
        return _quality_bucket_roe(x)
    if label == "GM%":
        return _quality_bucket_gm(x)
    if label == "Rev Δ":
        return _quality_bucket_rev_growth(x)
    if label == "Beta":
        return _quality_bucket_beta(x)
    if label == "RSI":
        return _quality_bucket_rsi(x)
    if label == "Fwd Δ%":
        return _quality_bucket_fwd_delta(x)
    return "neutral"


def _quality_for_metric_key(key: str, v) -> str:
    """Fundamentals table keys -> quality vs best-in-class heuristics."""
    if v is None:
        return "neutral"
    try:
        if isinstance(v, str) and key not in ("52 Week Range", "Today Range"):
            return "neutral"
        if key in ("52 Week Range", "Today Range"):
            return "neutral"
        x = float(v)
    except (TypeError, ValueError):
        return "neutral"
    if key == "P/E Ratio":
        return _quality_bucket_pe(x)
    if key == "Forward P/E":
        return _quality_bucket_pe(x)
    if key == "PEG Ratio":
        return _quality_bucket_peg(x)
    if key == "Price to Book":
        if x <= 3:
            return "good"
        if x <= 8:
            return "mid"
        return "poor"
    if key == "Dividend Yield":
        if x >= 2.5:
            return "good"
        if x >= 0.5:
            return "mid"
        return "poor"
    if key == "Debt to Equity":
        if x <= 0.5:
            return "good"
        if x <= 1.5:
            return "mid"
        return "poor"
    if key == "Current Ratio":
        if x >= 1.5:
            return "good"
        if x >= 1.0:
            return "mid"
        return "poor"
    if key == "Target Price":
        return "neutral"
    return "neutral"


def _last_rsi_macd(history):
    if history is None or len(history) < 2:
        return None, None
    row = history.iloc[-1]
    rsi = row.get("RSI") if "RSI" in history.columns else None
    macd = row.get("MACD") if "MACD" in history.columns else None
    sig = row.get("Signal") if "Signal" in history.columns else None
    macd_s = "↑" if macd is not None and sig is not None and macd > sig else "↓" if macd is not None and sig is not None else "—"
    return rsi, macd_s


def render_stock_identity_bar(ticker: str, data: dict, max_summary_chars: int = 180):
    """Compact identity: name, ticker, sector, one-line thesis."""
    info = data.get("info") or {}
    name = info.get("longName") or info.get("shortName") or ticker
    sector = info.get("sector") or "—"
    industry = info.get("industry") or ""
    summary = (info.get("longBusinessSummary") or "").strip()
    if len(summary) > max_summary_chars:
        summary = summary[: max_summary_chars - 1].rsplit(" ", 1)[0] + "…"
    meta = f"{sector}"
    if industry and industry != sector:
        meta += f" · {industry}"
    st.markdown(
        f"""
        <div class="vf-identity">
            <h2>{name} <span style="color:#64748b;font-weight:600;">{ticker}</span></h2>
            <div class="meta">{meta}</div>
            {f'<p style="margin:0.5rem 0 0 0;font-size:0.8125rem;color:#475569;line-height:1.45;">{summary}</p>' if summary else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_executive_kpi_strip(metrics: dict, forecast: dict, data: dict):
    """Single row of trader-focused KPIs: valuation, momentum, growth, size."""
    hist = data.get("history")
    rsi, macd_hint = _last_rsi_macd(hist)

    pe = metrics.get("P/E Ratio")
    fwd = metrics.get("Forward P/E")
    peg = metrics.get("PEG Ratio")
    roe = metrics.get("ROE")
    gm = metrics.get("Gross Margin")
    rev_g = metrics.get("Revenue Growth")
    beta = metrics.get("Beta")

    cells = []

    def push(label, display, raw_for_quality):
        q = _quality_for_kpi_strip(label, raw_for_quality)
        cells.append((label, display, q))

    push("P/E", _fmt_num(pe, "{:.1f}"), pe)
    push("Fwd P/E", _fmt_num(fwd, "{:.1f}"), fwd)
    push("PEG", _fmt_num(peg, "{:.2f}"), peg)
    push("ROE", _fmt_num(roe, "{:.1f}%") if roe is not None else "—", roe)
    push("GM%", _fmt_num(gm, "{:.1f}%") if gm is not None else "—", gm)
    push("Rev Δ", _fmt_num(rev_g, "{:+.1f}%") if rev_g is not None else "—", rev_g)
    push("Beta", _fmt_num(beta, "{:.2f}"), beta)

    if rsi is not None and not pd.isna(rsi):
        push("RSI", f"{float(rsi):.0f} {macd_hint or ''}".strip(), float(rsi))

    fchg = None
    if forecast:
        fchg = forecast.get("forecast_change_pct")
    if fchg is not None:
        push("Fwd Δ%", _fmt_num(fchg, "{:+.1f}%"), fchg)

    parts = ['<div class="vf-kpi-grid">']
    for label, val, q in cells:
        parts.append(
            f'<div class="vf-kpi-cell vf-{q}"><p class="vf-k">{label}</p><p class="vf-v">{val}</p></div>'
        )
    parts.append("</div>")
    st.markdown('<p class="vf-section-label">Key metrics</p>', unsafe_allow_html=True)
    st.markdown("".join(parts), unsafe_allow_html=True)
    st.markdown(
        '<p class="vf-bench-legend">Vs typical best-in-class bands: '
        '<span style="color:#16a34a;font-weight:600">■ strong</span> · '
        '<span style="color:#ca8a04;font-weight:600">■ mixed</span> · '
        '<span style="color:#dc2626;font-weight:600">■ weak</span></p>',
        unsafe_allow_html=True,
    )


def _trader_narrative_lines(metrics: dict, forecast: dict, data: dict, score: dict):
    """Derive short good/bad/mixed bullets from KPI quality + score + model forecast."""
    hist = data.get("history")
    rsi, _ = _last_rsi_macd(hist)

    goods, bads, mixed = [], [], []

    def add_from(label, raw):
        if raw is None or (isinstance(raw, float) and pd.isna(raw)):
            return
        q = _quality_for_kpi_strip(label, raw)
        g, b, m = _one_line_for_kpi(label, raw, q)
        if g:
            goods.append(g)
        if b:
            bads.append(b)
        if m:
            mixed.append(m)

    add_from("P/E", metrics.get("P/E Ratio"))
    add_from("Fwd P/E", metrics.get("Forward P/E"))
    add_from("PEG", metrics.get("PEG Ratio"))
    add_from("ROE", metrics.get("ROE"))
    add_from("GM%", metrics.get("Gross Margin"))
    add_from("Rev Δ", metrics.get("Revenue Growth"))
    add_from("Beta", metrics.get("Beta"))
    if rsi is not None and not pd.isna(rsi):
        add_from("RSI", float(rsi))
    fchg = forecast.get("forecast_change_pct") if forecast else None
    if fchg is not None:
        add_from("Fwd Δ%", fchg)

    total = float(score.get("total_score", 0) or 0)
    if total >= 72:
        goods.append(f"Composite score {total:.0f}/100 — top quartile in our model.")
    elif total >= 58:
        goods.append(f"Composite score {total:.0f}/100 — passes baseline quality screen.")
    elif total < 48:
        bads.append(f"Composite score {total:.0f}/100 — below our typical hurdle; edge is questionable.")

    if forecast:
        fp = forecast.get("forecast_price")
        cp = metrics.get("Current Price")
        pr = forecast.get("probability")
        if fp is not None and cp and float(cp) > 0:
            gap = (float(fp) - float(cp)) / float(cp) * 100
            if gap > 12 and (pr is None or float(pr) >= 50):
                goods.append(
                    f"Model target ~{gap:+.0f}% from spot (prob. {float(pr):.0f}%)" if pr is not None else f"Model target ~{gap:+.0f}% from spot."
                )
            elif gap < -12:
                bads.append(f"Model target sits ~{gap:+.0f}% below spot — upside not implied by base case.")

    def _dedupe(seq):
        seen = set()
        out = []
        for x in seq:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    return _dedupe(goods), _dedupe(bads), _dedupe(mixed)


def _one_line_for_kpi(label: str, raw, q: str):
    """Return (good_line, bad_line, mixed_line)."""
    if q == "neutral":
        return None, None, None
    try:
        x = float(raw)
    except (TypeError, ValueError):
        return None, None, None

    if q == "good":
        lines = {
            "P/E": f"P/E ~{x:.1f}x — multiple sits in our preferred quality band.",
            "Fwd P/E": f"Forward P/E ~{x:.1f}x — not paying an absurd growth tax at first glance.",
            "PEG": f"PEG ~{x:.2f} — growth looks reasonably priced vs earnings.",
            "ROE": f"ROE ~{x:.1f}% — capital efficiency looks solid.",
            "GM%": f"Gross margin ~{x:.1f}% — pricing power / mix supportive.",
            "Rev Δ": f"Revenue growth ~{x:+.1f}% — top-line still moving.",
            "Beta": f"Beta ~{x:.2f} — volatility profile close to the market (easier to size).",
            "RSI": f"RSI ~{x:.0f} — momentum not at an extreme.",
            "Fwd Δ%": f"Model path ~{x:+.1f}% — constructive vs spot.",
        }
        return lines.get(label), None, None
    if q == "poor":
        lines = {
            "P/E": f"P/E ~{x:.1f}x — multiple looks stretched or distressed vs benchmarks.",
            "Fwd P/E": f"Forward P/E ~{x:.1f}x — valuation demands flawless execution.",
            "PEG": f"PEG ~{x:.2f} — paying too much for growth (or negative earnings noise).",
            "ROE": f"ROE ~{x:.1f}% — returns on equity weak vs quality peers.",
            "GM%": f"Gross margin ~{x:.1f}% — pricing/mix pressure visible.",
            "Rev Δ": f"Revenue growth ~{x:+.1f}% — demand story is shaky.",
            "Beta": f"Beta ~{x:.2f} — high swing name; size and stops matter.",
            "RSI": f"RSI ~{x:.0f} — stretched or oversold; mean reversion risk.",
            "Fwd Δ%": f"Model path ~{x:+.1f}% — base case not friendly to longs.",
        }
        return None, lines.get(label), None
    mid_lines = {
        "P/E": f"P/E ~{x:.1f}x — OK but not a clear bargain.",
        "Fwd P/E": f"Forward P/E ~{x:.1f}x — fair-ish, not a fat pitch.",
        "PEG": f"PEG ~{x:.2f} — neutral vs growth.",
        "ROE": f"ROE ~{x:.1f}% — fine, not best-in-class.",
        "GM%": f"Gross margin ~{x:.1f}% — mixed quality signal.",
        "Rev Δ": f"Revenue growth ~{x:+.1f}% — lukewarm.",
        "Beta": f"Beta ~{x:.2f} — slightly off-market risk.",
        "RSI": f"RSI ~{x:.0f} — neither clean trend nor obvious reversal.",
        "Fwd Δ%": f"Model path ~{x:+.1f}% — small edge only.",
    }
    return None, None, mid_lines.get(label)


def _trader_verdict_paragraph(score: dict, forecast: dict, goods: list, bads: list) -> str:
    """Single executive verdict a prop desk would scan (HTML-safe)."""
    total = float(score.get("total_score", 0) or 0)
    fchg = forecast.get("forecast_change_pct") if forecast else None
    ng, nb = len(goods), len(bads)

    if total >= 68 and ng >= nb:
        bias = "<strong>Bias: constructive.</strong> Fundamentals and model skew support a long-biased workflow if your risk rules allow."
    elif total < 48 or nb > ng + 2:
        bias = "<strong>Bias: defensive.</strong> Weak vs our hurdles — prioritize capital preservation, tight risk, or pass."
    elif total >= 52:
        bias = "<strong>Bias: mixed / tactical.</strong> Neither clean long nor obvious short — trade the tape and levels, not narrative."
    else:
        bias = "<strong>Bias: selective.</strong> Only actionable with clear setup from price and signals."

    model_bits = []
    if fchg is not None:
        if fchg > 10:
            model_bits.append(
                "Internal model sees meaningful upside from spot; align position size with volatility."
            )
        elif fchg < -10:
            model_bits.append(
                "Internal model flags downside vs spot — do not average down without a new catalyst."
            )
        else:
            model_bits.append("Model outlook is near flat vs spot — edge is in execution, not macro call.")

    risk_line = (
        "<strong>Trader takeaway:</strong> Use the Forecast &amp; signals tab for entries, stops, and R-multiples; "
        "this panel is a fundamentals snapshot only, not investment advice."
    )

    parts = [bias] + model_bits + [risk_line]
    return " ".join(parts)


def _html_trade_plan_from_signals(trading_signals: dict, metrics: dict):
    """Stance, next move, example size — aligned with primary_stance in Forecast & signals."""
    if not trading_signals:
        return ""
    stance = trading_signals.get("primary_stance", "HOLD")
    reason = html.escape(trading_signals.get("primary_stance_reason", "") or "")
    cp = float(metrics.get("Current Price") or 0)
    sl = (trading_signals.get("stop_loss") or {}).get("price")
    tps = trading_signals.get("take_profit") or []
    tp1 = tps[0].get("price") if tps else None
    risk_pct = abs(cp - sl) / cp * 100 if sl and cp else None

    ex_acct = 100000.0
    risk_budget = ex_acct * 0.01
    shares = None
    notional = None
    if sl and cp and abs(cp - sl) > 1e-6:
        shares = int(risk_budget / abs(cp - sl))
        notional = shares * cp

    if stance == "BUY":
        nxt = (
            f"<b>Next move:</b> Bias long — use <b>Forecast &amp; signals</b> for entry (~${cp:.2f} spot), "
            f"stop, and targets; do not chase."
        )
    elif stance == "SELL":
        nxt = (
            f"<b>Next move:</b> Bias defensive / take profits / hedge — align with levels in "
            f"<b>Forecast &amp; signals</b> (~${cp:.2f} spot)."
        )
    else:
        nxt = (
            "<b>Next move:</b> <b>HOLD / wait</b> — no primary edge from rules; use signals tab for "
            "tactical scalps only with tight risk."
        )

    if shares and shares > 0 and notional:
        sz = (
            f"<b>Size (example):</b> 1% account risk on ${ex_acct:,.0f} = ${risk_budget:,.0f} risk budget → "
            f"~<b>{shares}</b> shares @ ~${cp:.2f} (~${notional:,.0f} notional) if stop is ${sl:.2f} "
            f"({risk_pct:.1f}% to stop)."
        )
    else:
        sz = (
            "<b>Size:</b> Risk <b>0.5–1%</b> of account equity to your stop from "
            "<b>Forecast &amp; signals</b>; adjust for volatility."
        )

    sc = stance
    color = "#15803d" if stance == "BUY" else "#b91c1c" if stance == "SELL" else "#a16207"
    bg = "#ecfdf5" if stance == "BUY" else "#fef2f2" if stance == "SELL" else "#fffbeb"
    return f"""
        <div class="vf-trade-plan" style="border-color:{color};background:{bg};">
            <span class="tag" style="color:{color};">Trading stance (same as strategy chart)</span>
            <p style="margin:0.25rem 0 0.35rem 0;font-size:1.15rem;font-weight:800;color:{color};">{html.escape(sc)}</p>
            <p style="margin:0 0 0.5rem 0;color:#334155;">{reason}</p>
            <p style="margin:0 0 0.5rem 0;color:#334155;">{nxt}</p>
            <p style="margin:0;color:#334155;">{sz}</p>
        </div>
    """


def render_executive_metrics_verdict(
    metrics: dict,
    forecast: dict,
    score: dict,
    data: dict,
    trading_signals: dict = None,
):
    """Executive summary: strengths, weaknesses, trader verdict — directly under key metrics."""
    goods, bads, mixed = _trader_narrative_lines(metrics or {}, forecast or {}, data or {}, score or {})
    verdict = _trader_verdict_paragraph(score or {}, forecast or {}, goods, bads)
    trade_plan_html = _html_trade_plan_from_signals(trading_signals or {}, metrics or {})

    if not goods and not bads and not mixed:
        goods = ["Insufficient clean signals on headline multiples — rely on composite score and full fundamentals table."]
    g_html = "<ul style='margin:0.35rem 0 0 1rem;padding:0;color:#166534;'>" + "".join(
        f"<li style='margin:0.2rem 0'>{html.escape(g)}</li>" for g in goods[:8]
    ) + "</ul>"
    b_html = "<ul style='margin:0.35rem 0 0 1rem;padding:0;color:#991b1b;'>" + "".join(
        f"<li style='margin:0.2rem 0'>{html.escape(b)}</li>" for b in bads[:8]
    ) + "</ul>"
    m_html = "<ul style='margin:0.35rem 0 0 1rem;padding:0;color:#a16207;'>" + "".join(
        f"<li style='margin:0.2rem 0'>{html.escape(x)}</li>" for x in mixed[:6]
    ) + "</ul>"

    mixed_block = ""
    if mixed:
        mixed_block = (
            "<div style='margin-top:0.75rem;'><strong style='color:#a16207;font-size:0.85rem;'>"
            "Mixed / no clear edge</strong>"
            + m_html
            + "</div>"
        )

    st.markdown(
        f"""
        <div class="vf-exec-wrap">
            <p class="vf-section-label" style="margin-bottom:0.5rem;">Executive read</p>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;">
                <div>
                    <strong style="color:#15803d;font-size:0.85rem;">What's working</strong>
                    {g_html if goods else "<p style='color:#64748b;font-size:0.85rem;margin:0.35rem 0 0 0;'>—</p>"}
                </div>
                <div>
                    <strong style="color:#b91c1c;font-size:0.85rem;">Headwinds / watchlist</strong>
                    {b_html if bads else "<p style='color:#64748b;font-size:0.85rem;margin:0.35rem 0 0 0;'>—</p>"}
                </div>
            </div>
            {mixed_block}
            {trade_plan_html}
            <div class="vf-exec-verdict">{verdict}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_score_hero(ticker: str, score: dict, metrics: dict, forecast: dict):
    """Large score + side metrics."""
    total = score.get("total_score", 0) or 0
    if total >= 70:
        border, fill = "#10b981", "rgba(16,185,129,0.08)"
    elif total >= 50:
        border, fill = "#f59e0b", "rgba(245,158,11,0.08)"
    else:
        border, fill = "#ef4444", "rgba(239,68,68,0.08)"

    price = metrics.get("Current Price")
    fc_p = forecast.get("forecast_price") if forecast else None
    fc_pct = forecast.get("forecast_change_pct") if forecast else None
    prob = forecast.get("probability") if forecast else None

    st.markdown('<p class="vf-section-label">Overall score</p>', unsafe_allow_html=True)
    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.markdown(
            f"""
            <div class="vf-score-big" style="border-color:{border};background:{fill};">
                <p style="margin:0;font-size:0.65rem;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;">Composite</p>
                <p style="margin:0;font-size:2.75rem;font-weight:800;color:{border};line-height:1;">{total:.0f}</p>
                <p style="margin:0;color:#64748b;font-size:0.8rem;">/ 100</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_b:
        c1, c2, c3 = st.columns(3)
        with c1:
            spot = f"${float(price):.2f}" if price is not None else "—"
            st.metric("Spot", spot)
        with c2:
            tgt = _fmt_num(fc_p, "${:.2f}", "—")
            d = float(fc_pct) if fc_pct is not None else None
            st.metric("Model target", tgt, delta=f"{d:+.1f}%" if d is not None else None)
        with c3:
            pr = float(prob) if prob is not None else None
            st.metric("Confidence", f"{pr:.0f}%" if pr is not None else "—")

    from utils.visualizations import create_score_breakdown_table

    with st.expander("Score components", expanded=False):
        create_score_breakdown_table(score, forecast)


def render_key_metrics_table(metrics: dict):
    """Tight fundamental table: what a PM scans in 10s."""
    rows = []
    spec = [
        ("52W range", "52 Week Range", None),
        ("Session", "Today Range", None),
        ("P/E", "P/E Ratio", "{:.1f}"),
        ("Fwd P/E", "Forward P/E", "{:.1f}"),
        ("PEG", "PEG Ratio", "{:.2f}"),
        ("P/B", "Price to Book", "{:.2f}"),
        ("Div yield", "Dividend Yield", "{:.2f}%"),
        ("D/E", "Debt to Equity", "{:.2f}"),
        ("Current", "Current Ratio", "{:.2f}"),
        ("Analyst tgt", "Target Price", "${:.2f}"),
    ]
    for label, key, fmt in spec:
        v = metrics.get(key)
        if v is None:
            continue
        if v == 0 and key in ("Dividend Yield", "Target Price", "Forward P/E", "PEG Ratio", "P/E Ratio"):
            continue
        if fmt and isinstance(v, (int, float)) and not isinstance(v, bool):
            rows.append((label, _fmt_num(v, fmt), key, v))
        else:
            rows.append((label, str(v)[:56], key, v))

    if not rows:
        return
    st.markdown('<p class="vf-section-label">Fundamentals snapshot</p>', unsafe_allow_html=True)
    tr_parts = []
    for lbl, disp, key, raw_v in rows[:12]:
        q = _quality_for_metric_key(key, raw_v)
        tr_parts.append(f'<tr class="vf-metric-row vf-{q}"><td>{lbl}</td><td>{disp}</td></tr>')
    st.markdown(
        f'<table class="vf-metric-table"><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody>{"".join(tr_parts)}</tbody></table>',
        unsafe_allow_html=True,
    )


def render_analyst_consensus_charts(
    ticker: str,
    data: dict,
    ratings_result,
    intrinsic_value,
    metrics: dict,
    current_price: float,
):
    """
    Full analyst projection (history + fair value tunnel + paths to targets)
    and a compact Low / Consensus / High bar chart vs spot.
    """
    from utils.visualizations import (
        create_analyst_projection_chart,
        create_analyst_consensus_bar_chart,
    )

    st.markdown(
        '<p class="vf-section-label">Analyst consensus & target range</p>',
        unsafe_allow_html=True,
    )
    chart_cfg = {"displayModeBar": True, "displaylogo": False}

    proj = None
    try:
        proj = create_analyst_projection_chart(
            data, ratings_result, intrinsic_value, current_price, ticker
        )
    except Exception:
        proj = None

    if proj:
        st.plotly_chart(proj, use_container_width=True, height=620, config=chart_cfg)
    else:
        st.caption(
            "Full projection chart appears when price history is available and Yahoo reports analyst targets."
        )

    bar = None
    try:
        bar = create_analyst_consensus_bar_chart(data, ratings_result, metrics, ticker)
    except Exception:
        bar = None
    if bar:
        st.plotly_chart(bar, use_container_width=True, height=380, config=chart_cfg)


def render_news_compact(ticker: str, news_articles: list, limit: int = 10):
    """Top news headlines with summary under each item (default 10) on dashboard."""
    if not news_articles:
        return
    st.markdown('<p class="vf-section-label">Top news</p>', unsafe_allow_html=True)
    for article in news_articles[:limit]:
        title = (article.get("title") or "Untitled")[:220]
        link = article.get("link") or "#"
        pub = article.get("publisher") or ""
        raw_sum = (article.get("summary") or "").strip()
        if raw_sum and raw_sum != "No summary available":
            sum_display = html.escape(raw_sum)
            if len(sum_display) > 450:
                sum_display = sum_display[:447] + "…"
            sum_block = f'<p class="vf-news-sum">{sum_display}</p>'
        else:
            sum_block = (
                '<p class="vf-news-sum" style="color:#94a3b8;font-style:italic;">'
                "No summary in feed — open article for full text."
                "</p>"
            )

        st.markdown(
            f"""
            <div class="vf-news-item">
                <a href="{html.escape(str(link), quote=True)}"
                   target="_blank" rel="noopener noreferrer"
                   style="font-weight:600;color:#1d4ed8;text-decoration:none;font-size:0.95rem;">
                   {html.escape(title)}
                </a>
                <span style="color:#64748b;font-size:0.8rem;"> · {html.escape(pub)}</span>
                {sum_block}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_peers_compact(ticker: str, data: dict, metrics: dict, score: dict):
    """Peer rank + table (reuses PeerBenchmark)."""
    from utils.peer_benchmark import PeerBenchmark

    peer_bench = PeerBenchmark()
    sector = data.get("info", {}).get("sector", "")
    try:
        peers = peer_bench.get_sector_peers(ticker, sector)
        if not peers:
            st.caption("No sector peers for benchmark.")
            return
        benchmark_result = peer_bench.benchmark_against_peers(ticker, metrics, score, peers)
        if not benchmark_result or not benchmark_result.get("benchmark_summary"):
            st.caption("Peer benchmark unavailable.")
            return
        summary = benchmark_result["benchmark_summary"]
        st.markdown('<p class="vf-section-label">Peers</p>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Rank", f"{summary['position']}/{summary['total_peers']}")
        with c2:
            st.metric("Percentile", f"{summary['percentile']:.0f}")
        with c3:
            st.metric("Outperform", summary["better_than"])

        comp = benchmark_result.get("peer_comparison")
        if comp is not None and len(comp):
            display_columns = ["ticker", "score", "pe_ratio", "roe", "current_price"]
            avail = [c for c in display_columns if c in comp.columns]
            if avail:
                show = comp[avail].head(8).copy()
                show.columns = [c.replace("_", " ").title() for c in avail]
                st.dataframe(show, use_container_width=True, hide_index=True)
    except Exception:
        st.caption("Peer data could not be loaded.")


# =============================================================================
# FACTOR GRADE & DIVIDEND SCORECARD PANELS
# =============================================================================

def render_factor_grades_panel(factor_grades: dict):
    """Render five circular factor grade pills (Value, Growth, Profitability, Momentum, EPS Rev.)."""
    from config import GRADE_COLORS

    if not factor_grades or "grades" not in factor_grades:
        return

    LABELS = [
        ("value", "Value"),
        ("growth", "Growth"),
        ("profitability", "Profit."),
        ("momentum", "Momentum"),
        ("eps_revisions", "EPS Rev."),
    ]

    grades = factor_grades["grades"]
    sector = factor_grades.get("sector", "")
    n_peers = factor_grades.get("n_peers", 0)

    pills_html = '<div class="vf-grade-panel">'
    for key, label in LABELS:
        g = grades.get(key, {})
        grade = g.get("grade", "N/A")
        tooltip = g.get("tooltip", "")
        color = GRADE_COLORS.get(grade, GRADE_COLORS["N/A"])
        pills_html += (
            f'<div class="vf-grade-item" title="{tooltip}">'
            f'<div class="vf-grade-pill" style="background:{color}">{grade}</div>'
            f'<p class="vf-grade-label">{label}</p>'
            f'</div>'
        )
    pills_html += "</div>"

    st.markdown('<p class="vf-section-label">Factor Grades</p>', unsafe_allow_html=True)
    st.markdown(pills_html, unsafe_allow_html=True)
    if sector or n_peers:
        st.caption(f"Sector-relative grades vs {n_peers} peers · {sector}")

    # Expandable sub-metric detail
    with st.expander("Grade detail", expanded=False):
        for key, label in LABELS:
            g = grades.get(key, {})
            grade = g.get("grade", "N/A")
            pct = g.get("percentile")
            sub = g.get("sub_scores", {})
            pct_str = f" ({pct:.0f}th pct)" if pct is not None else ""
            st.markdown(f"**{label}** — {grade}{pct_str}")
            if sub:
                sub_lines = []
                for k, v in sub.items():
                    if isinstance(v, (int, float)) and v is not None:
                        sub_lines.append(f"{k}: {v:.0f}" if isinstance(v, float) else f"{k}: {v}")
                if sub_lines:
                    st.caption("  ·  ".join(sub_lines))


def render_dividend_scorecard_panel(dividend_scorecard: dict):
    """Render four circular dividend grade pills (Safety, Growth, Yield, Consistency)."""
    from config import GRADE_COLORS

    if not dividend_scorecard:
        return

    if not dividend_scorecard.get("pays_dividend"):
        st.markdown('<p class="vf-section-label">Dividend Scorecard</p>', unsafe_allow_html=True)
        pill = f'<div class="vf-grade-panel"><div class="vf-grade-item"><div class="vf-grade-pill" style="background:{GRADE_COLORS["N/A"]}">N/A</div><p class="vf-grade-label">No Div.</p></div></div>'
        st.markdown(pill, unsafe_allow_html=True)
        st.caption("Company does not pay a dividend")
        return

    LABELS = [
        ("safety", "Safety"),
        ("growth", "Growth"),
        ("yield", "Yield"),
        ("consistency", "Consistency"),
    ]

    grades = dividend_scorecard.get("grades", {})
    pills_html = '<div class="vf-grade-panel">'
    for key, label in LABELS:
        g = grades.get(key, {})
        grade = g.get("grade", "N/A")
        tooltip = g.get("tooltip", "")
        color = GRADE_COLORS.get(grade, GRADE_COLORS["N/A"])
        pills_html += (
            f'<div class="vf-grade-item" title="{tooltip}">'
            f'<div class="vf-grade-pill" style="background:{color}">{grade}</div>'
            f'<p class="vf-grade-label">{label}</p>'
            f'</div>'
        )
    pills_html += "</div>"

    st.markdown('<p class="vf-section-label">Dividend Scorecard</p>', unsafe_allow_html=True)
    st.markdown(pills_html, unsafe_allow_html=True)
    dy = dividend_scorecard.get("current_yield", 0)
    if dy:
        st.caption(f"Current yield: {dy:.2%}")
