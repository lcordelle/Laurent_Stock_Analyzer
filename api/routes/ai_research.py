from __future__ import annotations
import os
import re
import logging
import asyncio
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from api.auth import verify_token
from api.models.responses import AiAnalystSections, AiAnalystReportResponse

router = APIRouter(tags=["ai"])
logger = logging.getLogger(__name__)


class AiResearchRequest(BaseModel):
    ticker: str
    question: str
    context: dict


class AiResearchResponse(BaseModel):
    ticker: str
    answer: str


class AiAnalystRequest(BaseModel):
    ticker: str
    company_name: str = ""
    sector: str = ""
    metrics: dict = {}
    score: dict = {}


def _detect_provider() -> str | None:
    forced = os.getenv("AI_ANALYST_PROVIDER", "").lower()
    if forced in ("groq", "anthropic", "ollama"):
        return forced
    if os.getenv("GROQ_API_KEY"):
        return "groq"
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    try:
        import urllib.request
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=1)
        return "ollama"
    except Exception:
        pass
    return None


def _fmt(v, fmt="{:.2f}", fallback="N/A"):
    try:
        return fmt.format(float(v)) if v is not None else fallback
    except Exception:
        return fallback


def _build_research_prompt(ticker: str, context: dict) -> str:
    metrics = context.get("metrics") or {}
    score = context.get("score") or {}
    signals = context.get("trading_signals") or {}
    forecast = context.get("forecast") or {}
    si = context.get("short_interest") or {}
    return f"""You are a professional equity analyst at VirtualFusion AI.

STOCK: {ticker} — {context.get("company_name", "")} ({context.get("sector", "")})
VF SCORE: {score.get("total", "N/A")}/100
SIGNAL: {signals.get("signal", "N/A")} | Confidence: {signals.get("confidence", "N/A")}%

KEY METRICS:
- Price: ${metrics.get("current_price", "N/A")} | Market Cap: ${metrics.get("market_cap", "N/A")}
- P/E: {metrics.get("pe_ratio", "N/A")} | Fwd P/E: {metrics.get("forward_pe", "N/A")} | PEG: {metrics.get("peg_ratio", "N/A")}
- ROE: {metrics.get("roe", "N/A")} | Gross Margin: {metrics.get("gross_margin", "N/A")} | Rev Growth: {metrics.get("revenue_growth", "N/A")}
- Beta: {metrics.get("beta", "N/A")} | D/E: {metrics.get("debt_to_equity", "N/A")}

TECHNICALS: RSI {signals.get("rsi_value", "N/A")} ({signals.get("rsi_signal", "N/A")}) | MACD: {signals.get("macd_signal", "N/A")} | Trend: {signals.get("trend_strength", "N/A")}
Entry: ${signals.get("optimal_entry", "N/A")} | Stop: ${signals.get("stop_loss", "N/A")} | TP1: ${signals.get("tp1", "N/A")} | R:R {signals.get("risk_reward", "N/A")}

OWNERSHIP: Short Float: {si.get("short_pct_float", "N/A")} | Insiders: {si.get("insider_own_pct", "N/A")} | Institutions: {si.get("institution_own_pct", "N/A")}
FORECAST: ${forecast.get("forecast_price", "N/A")} ({forecast.get("forecast_change_pct", "N/A")}%)

Be concise (3-5 sentences), direct, and data-driven. No generic disclaimers."""


def _build_analyst_prompt(ticker: str, company_name: str, sector: str, metrics: dict, score: dict) -> str:
    cur = metrics.get("current_price") or 0
    mktcap = metrics.get("market_cap")
    if mktcap:
        mktcap_str = f"${mktcap/1e12:.2f}T" if mktcap >= 1e12 else f"${mktcap/1e9:.2f}B" if mktcap >= 1e9 else f"${mktcap/1e6:.0f}M"
    else:
        mktcap_str = "N/A"

    return f"""You are a senior equity research analyst at VirtualFusion AI.
Produce a concise institutional-grade stock report for {ticker} ({company_name or ticker}, {sector or "Unknown Sector"}).

== QUANTITATIVE CONTEXT ==
VF Score: {score.get("total", "N/A")}/100
Current Price: {_fmt(cur, "${:.2f}")} | Market Cap: {mktcap_str}
P/E: {_fmt(metrics.get("pe_ratio"), "{:.1f}")} | Fwd P/E: {_fmt(metrics.get("forward_pe"), "{:.1f}")} | P/B: {_fmt(metrics.get("price_to_book"), "{:.1f}")}
Revenue Growth: {_fmt(metrics.get("revenue_growth"), "{:.1%}")} | Gross Margin: {_fmt(metrics.get("gross_margin"), "{:.1%}")} | ROE: {_fmt(metrics.get("roe"), "{:.1%}")}
Beta: {_fmt(metrics.get("beta"), "{:.2f}")} | Analyst Target: {_fmt(metrics.get("target_price"), "${:.2f}")}

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
- Be direct — cite actual numbers. No disclaimers."""


def _call_groq(system_prompt: str, model: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("GROQ_API_KEY"), base_url="https://api.groq.com/openai/v1")
    resp = client.chat.completions.create(
        model=model, max_tokens=1000,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate the response as instructed."},
        ],
    )
    return resp.choices[0].message.content or ""


def _call_anthropic(system_prompt: str, model: str) -> str:
    import anthropic as ant
    client = ant.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    resp = client.messages.create(
        model=model, max_tokens=1000,
        system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": "Generate the response as instructed."}],
    )
    return resp.content[0].text if resp.content else ""


def _call_ollama(system_prompt: str, model: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key="ollama", base_url="http://localhost:11434/v1")
    resp = client.chat.completions.create(
        model=model, max_tokens=1000,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate the response as instructed."},
        ],
    )
    return resp.choices[0].message.content or ""


def _call_llm(system_prompt: str) -> tuple[str, str, str]:
    provider = _detect_provider()
    if not provider:
        raise ValueError("No AI provider configured. Add GROQ_API_KEY to .env (free at console.groq.com)")
    models = {"groq": "llama-3.3-70b-versatile", "anthropic": "claude-sonnet-4-6", "ollama": "llama3.2"}
    model = os.getenv("AI_ANALYST_MODEL") or models.get(provider, "llama-3.3-70b-versatile")
    env_model = os.getenv("AI_ANALYST_MODEL")
    if env_model:
        model = env_model
    if provider == "groq":
        return _call_groq(system_prompt, model), provider, model
    if provider == "anthropic":
        return _call_anthropic(system_prompt, model), provider, model
    return _call_ollama(system_prompt, model), provider, model


def _parse_sections(raw: str) -> AiAnalystSections:
    patterns = [
        ("executive_summary", r"(?:1\.\s*)?Executive Summary\s*[:\n]"),
        ("bulls_say",         r"(?:2\.\s*)?Bulls Say\s*[:\n]"),
        ("bears_say",         r"(?:3\.\s*)?Bears Say\s*[:\n]"),
        ("key_risks",         r"(?:4\.\s*)?Key Risks\s*[:\n]"),
        ("investment_thesis", r"(?:5\.\s*)?Investment Thesis\s*[:\n]"),
    ]
    positions = []
    for key, pat in patterns:
        m = re.search(pat, raw, re.IGNORECASE)
        if m:
            positions.append((m.start(), m.end(), key))
    positions.sort(key=lambda x: x[0])

    result: dict = {}
    for i, (start, end, key) in enumerate(positions):
        next_start = positions[i + 1][0] if i + 1 < len(positions) else len(raw)
        content = raw[end:next_start].strip()
        if key in ("bulls_say", "bears_say"):
            bullets = re.findall(r"[-•*]\s+(.+)", content)
            if not bullets:
                bullets = re.findall(r"\d+\.\s+(.+)", content)
            if not bullets:
                bullets = [l.strip() for l in content.split("\n") if l.strip()]
            result[key] = bullets[:3]
        else:
            result[key] = content

    return AiAnalystSections(
        executive_summary=result.get("executive_summary"),
        bulls_say=result.get("bulls_say", []),
        bears_say=result.get("bears_say", []),
        key_risks=result.get("key_risks"),
        investment_thesis=result.get("investment_thesis"),
    )


def _run_research(ticker: str, question: str, context: dict) -> str:
    system_prompt = _build_research_prompt(ticker, context)
    # For Q&A, append the question to the system prompt context
    full_prompt = system_prompt + f"\n\nUser question: {question}\n\nAnswer directly and concisely."
    try:
        text, _, _ = _call_llm(full_prompt)
        return text
    except Exception as e:
        raise RuntimeError(str(e))


def _run_analyst_report(ticker: str, company_name: str, sector: str, metrics: dict, score: dict) -> AiAnalystReportResponse:
    try:
        system_prompt = _build_analyst_prompt(ticker, company_name, sector, metrics, score)
        raw, provider, model = _call_llm(system_prompt)
        sections = _parse_sections(raw)
        return AiAnalystReportResponse(ticker=ticker, provider=provider, model_name=model, sections=sections)
    except Exception as e:
        logger.error("Analyst report failed for %s: %s", ticker, e)
        return AiAnalystReportResponse(ticker=ticker, error=str(e))


@router.post("/ai/research", response_model=AiResearchResponse)
async def ai_research(body: AiResearchRequest, _: str = Depends(verify_token)):
    loop = asyncio.get_event_loop()
    try:
        answer = await loop.run_in_executor(None, _run_research, body.ticker, body.question, body.context)
        return AiResearchResponse(ticker=body.ticker, answer=answer)
    except Exception as e:
        provider_msg = "Add GROQ_API_KEY to .env (free at console.groq.com)" if "No AI provider" in str(e) else str(e)
        return AiResearchResponse(ticker=body.ticker, answer=f"AI unavailable: {provider_msg}")


@router.post("/ai/analyst-report", response_model=AiAnalystReportResponse)
async def analyst_report(body: AiAnalystRequest, _: str = Depends(verify_token)):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, _run_analyst_report,
        body.ticker, body.company_name, body.sector, body.metrics, body.score,
    )
