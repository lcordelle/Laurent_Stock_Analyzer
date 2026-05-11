"""
AI Analyst Report — multi-provider LLM backend with automatic provider detection.

Provider priority (first configured wins):
  1. Groq  — free tier at console.groq.com, Llama 3.3 70B, ~1s response
  2. Anthropic — claude-sonnet-4-6, paid but highest quality
  3. Ollama — local model, zero cost, offline. Install: brew install ollama && ollama pull llama3.2

Set AI_ANALYST_PROVIDER=groq|anthropic|ollama to force a specific backend.
"""

import os
import re
from datetime import datetime

import streamlit as st


# ---------------------------------------------------------------------------
# Provider detection
# ---------------------------------------------------------------------------

def _detect_provider():
    forced = os.getenv("AI_ANALYST_PROVIDER", "").lower()
    if forced in ("groq", "anthropic", "ollama"):
        return forced

    if os.getenv("GROQ_API_KEY"):
        return "groq"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"

    # Check if Ollama is running locally
    try:
        import urllib.request
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=1)
        return "ollama"
    except Exception:
        pass

    return None


def _provider_model(provider):
    defaults = {
        "groq": "llama-3.3-70b-versatile",
        "anthropic": "claude-sonnet-4-6",
        "ollama": "llama3.2",
    }
    env_model = os.getenv("AI_ANALYST_MODEL")
    return env_model or defaults.get(provider, "llama-3.3-70b-versatile")


# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------

def _fmt(v, fmt="{:.2f}", fallback="N/A"):
    try:
        return fmt.format(float(v)) if v is not None else fallback
    except Exception:
        return fallback


def _pct(v, fallback="N/A"):
    return _fmt(v, "{:.1%}", fallback)


def _grade_row(factor_grades):
    if not factor_grades or "grades" not in factor_grades:
        return "N/A"
    g = factor_grades["grades"]
    labels = [("value", "Value"), ("growth", "Growth"), ("profitability", "Profitability"),
              ("momentum", "Momentum"), ("eps_revisions", "EPS Rev.")]
    return "  |  ".join(f"{lbl}: {g.get(k, {}).get('grade', 'N/A')}" for k, lbl in labels)


def _build_prompt(ticker, company_name, sector, metrics, score, factor_grades,
                  earnings_data, dividend_scorecard, short_interest):
    grades_line = _grade_row(factor_grades)

    eps_summary = beat_rate = "N/A"
    if earnings_data and earnings_data.get("data_available"):
        last4 = earnings_data.get("eps_history", [])[:4]
        if last4:
            eps_summary = " | ".join(
                f"{e['quarter']}: {'+' if e.get('beat') else ''}{_fmt(e.get('surprise_pct'), '{:.1f}')}%"
                for e in last4 if e.get("surprise_pct") is not None
            ) or "N/A"
        br = earnings_data.get("beat_rate_4q")
        if br is not None:
            beat_rate = f"{br:.0f}%"

    div_line = "No dividend"
    if dividend_scorecard and dividend_scorecard.get("pays_dividend"):
        dg = dividend_scorecard.get("grades", {})
        div_line = (f"Yield {_pct(dividend_scorecard.get('current_yield'))} | "
                    f"Safety: {dg.get('safety', {}).get('grade', 'N/A')} | "
                    f"Growth: {dg.get('growth', {}).get('grade', 'N/A')} | "
                    f"Consistency: {dg.get('consistency', {}).get('grade', 'N/A')}")

    si_line = "N/A"
    if short_interest and isinstance(short_interest, dict):
        si_pct = short_interest.get("short_percent_of_float") or short_interest.get("short_float")
        if si_pct:
            si_line = f"{si_pct:.1%} of float"

    mktcap = metrics.get("market_cap")
    if mktcap:
        mktcap_str = (f"${mktcap/1e12:.2f}T" if mktcap >= 1e12 else
                      f"${mktcap/1e9:.2f}B" if mktcap >= 1e9 else f"${mktcap/1e6:.0f}M")
    else:
        mktcap_str = "N/A"

    score_total = score.get("total", "N/A") if isinstance(score, dict) else "N/A"
    target = metrics.get("target_mean_price") or metrics.get("analyst_target") or metrics.get("target_price")
    cur = metrics.get("current_price") or 0
    upside = _fmt((target - cur) / cur * 100, "{:+.1f}%") if target and cur else "N/A"

    return f"""You are a senior equity research analyst at VirtualFusion AI.
Produce a concise institutional-grade stock report for {ticker} ({company_name}, {sector or "Unknown Sector"}).

== QUANTITATIVE CONTEXT ==
Composite VF Score: {score_total}/100
Factor Grades (sector-relative): {grades_line}
Current Price: {_fmt(cur, '${:.2f}')} | Market Cap: {mktcap_str}
P/E: {_fmt(metrics.get('pe_ratio'), '{:.1f}')} | Fwd P/E: {_fmt(metrics.get('forward_pe'), '{:.1f}')} | P/B: {_fmt(metrics.get('price_to_book'), '{:.1f}')} | EV/EBITDA: {_fmt(metrics.get('ev_to_ebitda'), '{:.1f}')}
Revenue Growth: {_pct(metrics.get('revenue_growth'))} | EPS Growth: {_pct(metrics.get('earnings_growth'))} | FCF Margin: {_pct(metrics.get('fcf_margin'))}
Gross Margin: {_pct(metrics.get('gross_margin'))} | Net Margin: {_pct(metrics.get('profit_margin') or metrics.get('net_margin'))} | ROE: {_pct(metrics.get('roe'))} | Beta: {_fmt(metrics.get('beta'), '{:.2f}')}
Analyst Consensus: {metrics.get('analyst_consensus') or metrics.get('recommendation') or 'N/A'} ({metrics.get('num_analyst_opinions') or 'N/A'} analysts) | Target: {_fmt(target, '${:.2f}')} ({upside} upside)
EPS Surprises (last 4Q): {eps_summary} | Beat Rate: {beat_rate}
Dividend: {div_line}
Short Interest: {si_line}

== REPORT STRUCTURE ==
Your report MUST contain exactly these five sections with these exact headers:
1. Executive Summary
2. Bulls Say
3. Bears Say
4. Key Risks
5. Investment Thesis

Rules:
- Executive Summary: 3-4 sentences, data-driven verdict referencing specific numbers
- Bulls Say: exactly 3 bullet points starting with "- "
- Bears Say: exactly 3 bullet points starting with "- "
- Key Risks: 2-3 sentences on macro, competitive, and execution risks
- Investment Thesis: 2-3 sentences overall conclusion with price context
- Be direct — cite actual numbers. No disclaimers or "as an AI" language."""


# ---------------------------------------------------------------------------
# Provider call implementations
# ---------------------------------------------------------------------------

def _call_groq(system_prompt, model):
    from openai import OpenAI
    client = OpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url="https://api.groq.com/openai/v1",
    )
    response = client.chat.completions.create(
        model=model,
        max_tokens=1200,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate the five-section analyst report as instructed."},
        ],
    )
    return response.choices[0].message.content or ""


def _call_anthropic(system_prompt, model):
    import anthropic as ant
    client = ant.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model=model,
        max_tokens=1200,
        system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": "Generate the five-section analyst report as instructed."}],
    )
    return response.content[0].text if response.content else ""


def _call_ollama(system_prompt, model):
    from openai import OpenAI
    client = OpenAI(
        api_key="ollama",
        base_url="http://localhost:11434/v1",
    )
    response = client.chat.completions.create(
        model=model,
        max_tokens=1200,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate the five-section analyst report as instructed."},
        ],
    )
    return response.choices[0].message.content or ""


def _call_provider(provider, system_prompt):
    model = _provider_model(provider)
    if provider == "groq":
        return _call_groq(system_prompt, model), model
    if provider == "anthropic":
        return _call_anthropic(system_prompt, model), model
    if provider == "ollama":
        return _call_ollama(system_prompt, model), model
    raise ValueError(f"Unknown provider: {provider}")


# ---------------------------------------------------------------------------
# Section parser
# ---------------------------------------------------------------------------

def _parse_report_sections(raw_text):
    sections = {
        "executive_summary": None,
        "bulls_say": [],
        "bears_say": [],
        "key_risks": None,
        "investment_thesis": None,
        "raw": raw_text,
    }

    patterns = [
        ("executive_summary", r"(?:1\.\s*)?Executive Summary\s*[:\n]"),
        ("bulls_say",         r"(?:2\.\s*)?Bulls Say\s*[:\n]"),
        ("bears_say",         r"(?:3\.\s*)?Bears Say\s*[:\n]"),
        ("key_risks",         r"(?:4\.\s*)?Key Risks\s*[:\n]"),
        ("investment_thesis", r"(?:5\.\s*)?Investment Thesis\s*[:\n]"),
    ]

    positions = []
    for key, pat in patterns:
        m = re.search(pat, raw_text, re.IGNORECASE)
        if m:
            positions.append((m.start(), m.end(), key))
    positions.sort(key=lambda x: x[0])

    for i, (start, end, key) in enumerate(positions):
        next_start = positions[i + 1][0] if i + 1 < len(positions) else len(raw_text)
        content = raw_text[end:next_start].strip()
        if key in ("bulls_say", "bears_say"):
            bullets = re.findall(r"[-•*]\s+(.+)", content)
            if not bullets:
                bullets = re.findall(r"\d+\.\s+(.+)", content)
            if not bullets:
                bullets = [l.strip() for l in content.split("\n") if l.strip()]
            sections[key] = bullets[:3]
        else:
            sections[key] = content

    return sections


# ---------------------------------------------------------------------------
# Not-configured stub
# ---------------------------------------------------------------------------

def _no_provider_stub(ticker):
    return {
        "ticker": ticker,
        "sections": {
            "executive_summary": None,
            "bulls_say": [],
            "bears_say": [],
            "key_risks": None,
            "investment_thesis": None,
            "raw": "",
        },
        "model": None,
        "provider": None,
        "generated_at": datetime.now().isoformat(),
        "error": "no_provider",
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_analyst_report_full(ticker, company_name, sector, metrics, score,
                                  factor_grades, earnings_data, dividend_scorecard,
                                  short_interest):
    """
    Generate an AI analyst report using the best available free provider.
    Auto-detects: Groq (free) → Anthropic → Ollama (local).
    """
    provider = _detect_provider()
    if not provider:
        return _no_provider_stub(ticker)

    system_prompt = _build_prompt(
        ticker=ticker, company_name=company_name, sector=sector,
        metrics=metrics or {}, score=score or {},
        factor_grades=factor_grades, earnings_data=earnings_data,
        dividend_scorecard=dividend_scorecard, short_interest=short_interest,
    )

    try:
        raw_text, model = _call_provider(provider, system_prompt)
        sections = _parse_report_sections(raw_text)
        return {
            "ticker": ticker,
            "sections": sections,
            "model": model,
            "provider": provider,
            "generated_at": datetime.now().isoformat(),
            "error": None,
        }
    except Exception as e:
        stub = _no_provider_stub(ticker)
        stub["error"] = str(e)
        stub["provider"] = provider
        return stub
