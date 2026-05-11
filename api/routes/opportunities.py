from __future__ import annotations
import asyncio
import logging
import time
from typing import Optional
import yfinance as yf
import pandas as pd
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from api.auth import verify_token
from api.routes.stocks import _compute_trading_signals
from utils.stock_analyzer import StockAnalyzer

router = APIRouter(tags=["opportunities"])
logger = logging.getLogger(__name__)

_analyzer = StockAnalyzer()
_SEM = asyncio.Semaphore(30)

CACHE_TTL = 15 * 60  # 15 minutes
_cache: Optional[dict] = None
_cache_ts: float = 0.0

# ── ~500-stock universe across 20 domains ────────────────────────────────────
SCAN_UNIVERSE: dict[str, list[str]] = {
    "AI & Semiconductors": [
        "NVDA","AMD","AVGO","TSM","ASML","AMAT","KLAC","ARM","MRVL","LRCX",
        "SNPS","CDNS","ONTO","ACLS","FORM","QCOM","INTC","SMCI","MPWR","MCHP",
        "WOLF","COHR","IPGP","SLAB","OLED",
    ],
    "Cloud & Enterprise Tech": [
        "MSFT","CRM","NOW","SNOW","DDOG","PLTR","META","GOOGL","MDB","NET",
        "HUBS","OKTA","GTLB","BILL","ZM","ORCL","ADSK","TTD","TWLO","ESTC",
        "CFLT","AZPN","ZI","APPF","PTC",
    ],
    "Mid-Cap SaaS & Platforms": [
        "ADBE","INTU","WDAY","VEEV","PAYC","PCTY","SMAR","ASAN","BRZE","FRSH",
        "BOX","DOCN","PD","NCNO","ENFN","RAMP","XMTR","TASK",
    ],
    "Healthcare & Med-Tech": [
        "LLY","NVO","UNH","ISRG","MDT","ABT","BSX","SYK","EW","DXCM",
        "NTRA","RVMD","INSP","PODD","ITGR","TMO","DHR","IQVIA","MEDP","ICLR",
        "HOLX","NVCR","EXAS","AMED","MMSI","GEHC","PGNY","PRVA","MLAB","RMD",
    ],
    "Biotech": [
        "ABBV","VRTX","REGN","MRNA","BIIB","ALNY","BMRN","EXEL","RARE","ARWR",
        "IONS","PTGX","KYMR","ACAD","GILD","AMGN","INCY","RGEN","BEAM","NTLA",
        "EDIT","CRSP","AKRO","FOLD","SRPT","UTHR","MRUS","DNLI","IMVT","NUVL",
    ],
    "Financials & Fintech": [
        "JPM","V","MA","BLK","GS","AXP","MS","SCHW","ICE","CME",
        "PYPL","SQ","AFRM","NU","SOFI","FIS","FISV","SPGI","MCO","NDAQ",
        "CBOE","WEX","HOOD","COIN","MELI","IBKR","RJF","LPLA",
    ],
    "Banks & Regional Finance": [
        "BAC","WFC","C","USB","PNC","TFC","CFG","FITB","HBAN","KEY",
        "RF","ZION","CMA","WAL","EWBC","WTFC","BOKF","FHB","COLB","BANR",
        "FFIN","CVBF","TCBI","IBCP",
    ],
    "Insurance & Asset Management": [
        "BRK-B","MET","PRU","AFL","CB","TRV","ALL","TROW","AMG","BEN",
        "RLI","WRB","RNR","MKL","RYAN","ACGL","RE","ORI",
    ],
    "Clean Energy & Nuclear": [
        "CEG","VST","CCJ","NEE","FSLR","XOM","ENPH","SEDG","RUN","OKLO",
        "SMR","NNE","BEP","AES","BE","STEM","ARRY","SHLS","CHPT","EVGO",
        "HASI","CWEN","NOVA",
    ],
    "Energy & Oil/Gas": [
        "CVX","COP","EOG","FANG","DVN","APA","MRO","OXY","HAL","SLB",
        "BKR","NOV","MTDR","CIVI","SM","CNX","AR","EQT","RRC","CTRA",
        "PSX","VLO",
    ],
    "Consumer & E-Commerce": [
        "AMZN","COST","MCD","TSLA","AAPL","SBUX","NKE","TGT","LULU","SHOP",
        "ETSY","DUOL","APP","BROS","EBAY","ROST","TJX","ULTA","DLTR","DG",
        "YUM","CPNG",
    ],
    "Transportation & Logistics": [
        "UPS","FDX","UBER","LYFT","DASH","ABNB","BKNG","DAL","UAL","LUV",
        "CSX","NSC","UNP","CP","EXPD","CHRW","XPO","ODFL","SAIA","JBHT",
        "WERN","LSTR",
    ],
    "Defence & Cybersecurity": [
        "LMT","RTX","NOC","CRWD","PANW","ZS","GD","HII","LDOS","FTNT",
        "S","CYBR","TENB","QLYS","BAH","SAIC","LHX","DRS","TDG","VRNS",
        "HEI","SPR","KTOS","SAIL",
    ],
    "Industrial & Infrastructure": [
        "CAT","DE","ETN","PWR","EMR","ROK","CARR","ITW","GWW","FAST",
        "URI","WIRE","CTAS","PAYX","MSA","AME","HUBB","AECOM","JCI","XYL",
        "IDEX","NDSN","GNRC","TRMB","FTV","PH","FBIN",
    ],
    "REITs & Real Assets": [
        "AMT","PLD","EQIX","DLR","PSA","EXR","O","VICI","SPG","AVB",
        "IRM","GLPI","CBRE","MAA","WPC","REXR","FR","STAG","NNN","BXP",
        "CCI","COLD",
    ],
    "Dividend Champions": [
        "JNJ","PG","KO","PEP","MMC","ADP","TXN","CINF","IBM","HD",
        "LOW","WMT","T","VZ","PM","MO","NUE","GPC",
    ],
    "Small-Cap Growth": [
        "CELH","ASTS","RKLB","IONQ","AXON","TOST","CAVA","DKNG","MNDY","HIMS",
        "AMBA","CRDO","ALAB","KVYO","DOCS","TRUP","FLYW","ACVA","NARI","INMD",
        "LMND","JOBY","RXRX","ELF","ONON","BIRK","ROIV","SOUN","PLTK","OSCR",
    ],
    "International ADRs": [
        "SAP","TM","SNY","BABA","JD","SE","GRAB","WDS","RIO","BHP",
        "VALE","BNTX","RACE","ASAI","UL","SHEL","BP","RELX","UBS","DB",
        "ING","ABB","INFY","WIT","CNQ","STLA","ERIC","BTI",
    ],
    "Materials & Commodities": [
        "FCX","NEM","GOLD","ALB","MP","LAC","LIN","APD","SHW","PPG",
        "MOS","NTR","CF","EMN","LYB","DOW","DD","CE","HUN","OLN",
        "RPM","WFG","CTVA","AVY","IFF","BALL","SEE",
    ],
    "Communication & Media": [
        "NFLX","DIS","SPOT","SNAP","PINS","RBLX","TTWO","EA","MTCH","WBD",
        "FOXA","TMUS","CHTR","PARA","SIRI","IAC","NWSA","RDDT","MGNI","ATUS",
        "ROKU","FUBO","CARG","WMG","LYV",
    ],
}

MARKET_THEMES = [
    {
        "theme": "AI Infrastructure Supercycle",
        "conviction": "HIGH",
        "thesis": "Hyperscalers committing $300B+ in 2025-2026 data centre capex. GPU demand compound growth 40%+ annually. Inference scaling creating a second wave of compute demand beyond training.",
        "catalysts": [
            "Hyperscaler capex guidance at record highs — Microsoft, Google, Meta, Amazon all guiding up",
            "Next-gen GPU (Blackwell/Rubin) architecture driving 2-3 year upgrade supercycle",
            "AI inference demand growing 10x annually, requiring 5-10x more compute per model generation",
        ],
        "stocks": ["NVDA", "AVGO", "AMD", "ASML", "AMAT"],
        "timeframe": "12-24 months",
        "risk": "Valuation compression if AI revenue ramp disappoints consensus; potential China export restrictions",
        "opportunity_size": "$500B+ chip and infrastructure market by 2027",
    },
    {
        "theme": "GLP-1 Weight-Loss Drug Revolution",
        "conviction": "HIGH",
        "thesis": "Obesity drug market projected to reach $150B+ by 2030. Supply constraints easing in H2 2025. Next-gen oral formulations (orforglipron, CagriSema) expanding TAM well beyond injectables.",
        "catalysts": [
            "LLY oral GLP-1 Phase 3 readouts H2 2025 — could 10x the addressable market",
            "Cardiovascular and renal protection labels expanding prescriber confidence",
            "Manufacturing capacity additions removing supply bottleneck by Q4 2025",
        ],
        "stocks": ["LLY", "NVO", "VRTX", "REGN"],
        "timeframe": "18-36 months",
        "risk": "FDA safety signal or competing mechanism of action entering market sooner than expected",
        "opportunity_size": "$150B+ annual market by 2030",
    },
    {
        "theme": "Defence & Geopolitical Re-Armament",
        "conviction": "HIGH",
        "thesis": "NATO 2% GDP spending mandate, European defence budgets growing fastest in 30 years. US defence budget at $886B for FY2025. Multi-year procurement cycles locking in revenue visibility.",
        "catalysts": [
            "European defence emergency funding adding $100B+ in new procurement",
            "F-35, Patriot, HIMARS backlogs stretching 5-7 years",
            "Unmanned systems and electronic warfare creating new growth vectors",
        ],
        "stocks": ["LMT", "RTX", "NOC"],
        "timeframe": "24-48 months",
        "risk": "Unexpected geopolitical de-escalation reducing procurement urgency",
        "opportunity_size": "$3T+ cumulative NATO spending through 2030",
    },
    {
        "theme": "Nuclear Energy Renaissance",
        "conviction": "HIGH",
        "thesis": "AI data centres require clean, always-on baseload power. Tech giants signing 20-year nuclear PPAs. SMR technology maturing with NRC approvals accelerating.",
        "catalysts": [
            "Microsoft, Google, Amazon signing nuclear PPAs — legitimising the asset class",
            "Three Mile Island restart demonstrating utility economics at scale",
            "NRC expedited SMR review pipeline — 10+ projects in advanced licensing",
        ],
        "stocks": ["CEG", "VST", "CCJ"],
        "timeframe": "24-60 months",
        "risk": "Regulatory delays, SMR cost overruns, natural gas price collapse",
        "opportunity_size": "$600B+ new nuclear capacity globally by 2040",
    },
    {
        "theme": "Cybersecurity AI-Native Consolidation",
        "conviction": "MEDIUM",
        "thesis": "Enterprise security budgets growing 15%+ annually even in downturns. AI-native platforms displacing 10-12 legacy point solutions. Platform consolidation driving revenue expansion and margin improvement.",
        "catalysts": [
            "CrowdStrike Falcon platform expanding from endpoint to SIEM/SOAR/identity",
            "AI-powered threat detection reducing analyst workload 80% — driving upsell",
            "Regulatory mandates (NIS2, DORA, SEC disclosure rules) accelerating spend",
        ],
        "stocks": ["CRWD", "PANW", "ZS"],
        "timeframe": "12-24 months",
        "risk": "Economic slowdown causing enterprise security budget cuts; M&A premium risk",
        "opportunity_size": "$500B+ total addressable market by 2027",
    },
    {
        "theme": "Cloud Hyperscalers & Platform AI",
        "conviction": "HIGH",
        "thesis": "AWS, Azure, and Google Cloud growing 20-30% with AI workloads as incremental revenue. Software platforms layering AI copilots across entire suite — driving seat expansion and ARPU growth.",
        "catalysts": [
            "Azure AI consumption growing 100%+ YoY as enterprise adoption crosses the chasm",
            "Google DeepMind Gemini integration across Workspace and GCP accelerating",
            "Salesforce Agentforce, ServiceNow Now Assist — AI agents becoming SaaS pricing tailwinds",
        ],
        "stocks": ["MSFT", "GOOGL", "AMZN", "CRM", "NOW"],
        "timeframe": "12-36 months",
        "risk": "Multiple compression as growth moderates; open-source AI commoditising software",
        "opportunity_size": "$1T+ cloud and AI platform market by 2028",
    },
    {
        "theme": "Financial Infrastructure & Digital Payments",
        "conviction": "MEDIUM",
        "thesis": "Visa and Mastercard are AI-powered global infrastructure businesses with near-monopoly cross-border payment networks, 40%+ net margins, and secular volume growth driven by cash-to-digital conversion.",
        "catalysts": [
            "Cross-border payment volumes recovering to pre-pandemic growth trajectories",
            "Value-added services (tokenisation, fraud, advisory) growing 20%+ and expanding margins",
            "Emerging market penetration in MENA, SEA, Africa adding 1B+ new cardholders",
        ],
        "stocks": ["V", "MA", "JPM", "AXP", "BLK"],
        "timeframe": "12-24 months",
        "risk": "Antitrust action on interchange fees; central bank digital currency displacement",
        "opportunity_size": "$300T+ global payments flow — 1% fee on incremental digitisation",
    },
    {
        "theme": "Precision Medicine & Drug Innovation",
        "conviction": "MEDIUM",
        "thesis": "Gene editing, RNA medicine, and AI-designed drugs creating a step-change in treatment efficacy. CRISPR therapies now FDA-approved; next-gen immunology targets showing transformative clinical results.",
        "catalysts": [
            "Vertex CRISPR CTX001 scaling to more indications beyond sickle cell",
            "Regeneron IL-33 and dupilumab label expansions into new inflammatory diseases",
            "AbbVie Skyrizi/Rinvoq reaching $25B+ combined revenue, replacing Humira",
        ],
        "stocks": ["VRTX", "REGN", "ABBV", "ISRG"],
        "timeframe": "18-36 months",
        "risk": "Clinical trial failure; FDA rejection; pricing pressure from IRA drug negotiation",
        "opportunity_size": "$800B+ global biotech and drug market by 2030",
    },
    {
        "theme": "REIT Digital Infrastructure & Real Assets",
        "conviction": "MEDIUM",
        "thesis": "Data centre REITs capturing AI infrastructure buildout at the real estate layer. Cell tower REITs compounding from 5G densification. Industrial REITs benefiting from nearshoring-driven warehouse demand.",
        "catalysts": [
            "AI workload migration driving sustained co-location demand for EQIX and DLR",
            "Rate normalisation removing the primary REIT valuation headwind",
            "Nearshoring pushing 15%+ annual demand growth for Class A industrial logistics space",
        ],
        "stocks": ["EQIX", "DLR", "AMT", "PLD", "IRM"],
        "timeframe": "12-24 months",
        "risk": "Rate re-acceleration compressing cap rates; oversupply in select data centre markets",
        "opportunity_size": "$1.5T+ global data centre real estate market by 2030",
    },
    {
        "theme": "Critical Minerals & Battery Materials",
        "conviction": "MEDIUM",
        "thesis": "Energy transition structurally dependent on lithium, copper, and rare earths. IRA and EU Critical Raw Materials Act incentivising domestic production. EV, grid storage, and defence demand creating a decade-long supercycle.",
        "catalysts": [
            "IRA domestic content requirements driving North American lithium sourcing urgency",
            "Copper supply deficit widening to 6-8M tonnes by 2030 — no large mines in development",
            "DoD strategic funding for domestic battery supply chain including ALB, MP, and LAC",
        ],
        "stocks": ["ALB", "FCX", "MP", "LAC", "NEM"],
        "timeframe": "24-48 months",
        "risk": "EV adoption pace disappoints; China flooding markets with subsidised material production",
        "opportunity_size": "$500B+ annual critical minerals market by 2030",
    },
    {
        "theme": "Dividend Compounders & Capital Allocation Excellence",
        "conviction": "MEDIUM",
        "thesis": "Businesses with 20+ year dividend growth streaks and strong FCF offer risk-adjusted returns superior to bonds in a normalising rate environment. Inflation protection through pricing power and rising dividends.",
        "catalysts": [
            "Rate normalisation increasing relative attractiveness of 3-5% dividend yields",
            "Share buyback programs at historically elevated levels across S&P 500 aristocrats",
            "Recession-resistant revenue streams reducing portfolio beta",
        ],
        "stocks": ["JNJ", "PG", "KO", "ADP", "TXN"],
        "timeframe": "12-36 months",
        "risk": "Dividend cuts if earnings deteriorate in a hard landing; rate re-acceleration reducing relative appeal",
        "opportunity_size": "$4T+ dividend aristocrat market cap — stable income through cycles",
    },
    {
        "theme": "Consumer Fintech & Emerging Market Digital Finance",
        "conviction": "MEDIUM",
        "thesis": "NU Bank, Sea Limited, and GRAB building super-apps serving 500M+ underbanked consumers. Penetration in single digits for digital credit and investment products in LATAM and SEA — decade of runway remaining.",
        "catalysts": [
            "NU Bank reaching profitability in Mexico and Colombia — confirming multi-market replication",
            "GRAB SuperApp expanding beyond ride-hailing into financial services and digital banking",
            "Digital payment penetration in SEA at 20% vs 80%+ in US — structural growth decade ahead",
        ],
        "stocks": ["NU", "SE", "GRAB", "SOFI", "AFRM"],
        "timeframe": "18-36 months",
        "risk": "EM currency depreciation; regulatory crackdown on digital banking licenses; credit cycle deterioration",
        "opportunity_size": "$800B+ digital financial services market across LATAM and SEA by 2030",
    },
]


# ── Lightweight single-ticker scan (no news/peers/analyst — just score+signal) ─
def _quick_scan(ticker: str) -> Optional[dict]:
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        hist = t.history(period="1y")
        if hist is None or len(hist) < 20:
            return None

        current_price = float(hist["Close"].iloc[-1])

        # VF score
        score_data = _analyzer.calculate_score({"info": info, "history": hist})
        vf_score = score_data.get("total_score", 0) if isinstance(score_data, dict) else 0
        score_components = score_data.get("components", {}) if isinstance(score_data, dict) else {}

        raw_fcf = info.get("freeCashflow")
        raw_rev = info.get("totalRevenue")
        fcf_margin_raw = None
        if raw_fcf and raw_rev and float(raw_rev) != 0:
            fcf_margin_raw = round(float(raw_fcf) / float(raw_rev) * 100, 1)

        # Recent news check (last 7 days) — fetched before signals so count feeds signal_quality
        try:
            raw_news = t.news or []
            cutoff = time.time() - 7 * 86400
            news_recent = [n for n in raw_news[:10] if n.get("providerPublishTime", 0) > cutoff]
            has_recent_news = len(news_recent) > 0
            recent_news_count = len(news_recent)
        except Exception:
            has_recent_news = False
            recent_news_count = 0

        # Technical indicators + signals
        hist_ind = None
        if len(hist) >= 50:
            try:
                hist_ind = _analyzer.calculate_technical_indicators(hist.copy())
            except Exception:
                hist_ind = hist
        sig = _compute_trading_signals(hist_ind if hist_ind is not None else hist, current_price, recent_news_count=recent_news_count)

        # Analyst consensus target
        analyst_target = info.get("targetMeanPrice")
        analyst_upside = None
        if analyst_target and current_price and current_price > 0:
            analyst_upside = round((analyst_target - current_price) / current_price * 100, 1)

        # 52-week momentum (price position in range)
        low52 = info.get("fiftyTwoWeekLow")
        high52 = info.get("fiftyTwoWeekHigh")
        week52_momentum = None
        if low52 and high52 and (high52 - low52) > 0:
            week52_momentum = round((current_price - low52) / (high52 - low52) * 100, 1)

        # Key fundamentals
        raw_roe = info.get("returnOnEquity")
        roe = round(raw_roe * 100, 1) if raw_roe else None
        raw_gm = info.get("grossMargins")
        gross_margin = round(raw_gm * 100, 1) if raw_gm else None
        raw_rg = info.get("revenueGrowth")
        revenue_growth = round(raw_rg * 100, 1) if raw_rg else None
        pe = info.get("trailingPE") or info.get("forwardPE")
        pe = round(pe, 1) if pe else None
        market_cap = info.get("marketCap")

        # Combined conviction score (VF fundamentals 60% + signal confidence 40%)
        confidence = sig.confidence or 0
        combined = round(vf_score * 0.6 + confidence * 0.4, 1)

        # Generate "why now" rationale + conviction tier + score drivers
        why_now = _why_now(vf_score, sig, week52_momentum, roe, gross_margin, revenue_growth, analyst_upside)
        tier = _conviction_tier(combined)
        drivers = _score_drivers(
            score_components, gross_margin, roe, revenue_growth, pe,
            fcf_margin_raw, week52_momentum, analyst_upside, sig,
        )

        # Annualized volatility for position-sizing guidance
        try:
            daily_returns = hist["Close"].pct_change().dropna()
            vol_annual = round(float(daily_returns.std()) * (252 ** 0.5) * 100, 1)
            suggested_position_pct = (
                1.0 if vol_annual > 50 else
                2.0 if vol_annual > 35 else
                3.0 if vol_annual > 25 else
                5.0
            )
        except Exception:
            vol_annual = None
            suggested_position_pct = None

        # Analyst recommendation freshness
        rec_date_ts = info.get("recommendationDate")
        analyst_target_age_days = None
        if rec_date_ts:
            try:
                analyst_target_age_days = int((time.time() - float(rec_date_ts)) / 86400)
            except Exception:
                pass

        return {
            "ticker": ticker,
            "name": info.get("longName") or info.get("shortName"),
            "sector": info.get("sector"),
            "price": round(current_price, 2),
            "vf_score": vf_score,
            "signal": sig.signal,
            "confidence": confidence,
            "rsi": sig.rsi_value,
            "rsi_signal": sig.rsi_signal,
            "macd_signal": sig.macd_signal,
            "trend": sig.trend_strength,
            "stop_loss": sig.stop_loss,
            "tp1": sig.tp1,
            "tp2": sig.tp2,
            "tp3": sig.tp3,
            "risk_reward": sig.risk_reward,
            "analyst_target": round(analyst_target, 2) if analyst_target else None,
            "analyst_upside": analyst_upside,
            "week52_momentum": week52_momentum,
            "pe_ratio": pe,
            "roe": roe,
            "gross_margin": gross_margin,
            "revenue_growth": revenue_growth,
            "market_cap": market_cap,
            "combined_score": combined,
            "why_now": why_now,
            "conviction_tier": tier,
            "score_drivers": drivers,
            "domain": None,   # injected by _run_scan
            "has_recent_news": has_recent_news,
            "recent_news_count": recent_news_count,
            "analyst_target_age_days": analyst_target_age_days,
            "volatility_annual": vol_annual,
            "suggested_position_pct": suggested_position_pct,
            "signal_quality": sig.signal_quality,
        }
    except Exception as e:
        logger.warning("Quick scan failed for %s: %s", ticker, e)
        return None


def _why_now(vf: int, sig, momentum: Optional[float], roe: Optional[float],
             gm: Optional[float], rg: Optional[float], upside: Optional[float]) -> str:
    signal = sig.signal or ""
    rsi = sig.rsi_value or 50

    if vf >= 80 and "BUY" in signal:
        return "Elite fundamentals aligned with bullish technicals — rare high-conviction setup"
    if rsi < 35 and vf >= 60:
        return "Technically oversold with strong fundamentals — asymmetric reversal opportunity"
    if rsi < 45 and sig.macd_signal == "BULLISH" and vf >= 65:
        return "Momentum turning bullish while still early in the move — ideal entry zone"
    if momentum is not None and momentum < 25 and vf >= 70:
        return "Near 52-week lows with premium fundamentals — deep value entry point"
    if upside is not None and upside > 20 and vf >= 60:
        return f"Analyst consensus implies {upside:.0f}% upside — significant margin of safety"
    if rg is not None and rg > 25 and vf >= 70:
        return f"{rg:.0f}% revenue growth with high-quality fundamentals — growth at a reasonable price"
    if "STRONG BUY" in signal:
        return "Technical scoring at maximum bullish extreme — high-momentum entry"
    if vf >= 75 and "HOLD" in signal:
        return "World-class business at fair value — accumulate on weakness"
    if gm is not None and gm > 60 and vf >= 65:
        return f"{gm:.0f}% gross margins signal structural pricing power — quality compounder"
    return "Solid fundamentals with improving technical picture — monitor for entry"


def _conviction_tier(combined: float) -> str:
    if combined >= 75: return "STRONG BUY"
    if combined >= 60: return "BUY"
    if combined >= 45: return "WATCH"
    return "AVOID"


def _score_drivers(
    score_components: dict,
    gross_margin: Optional[float], roe: Optional[float],
    revenue_growth: Optional[float], pe: Optional[float],
    fcf_margin_raw: Optional[float], week52_momentum: Optional[float],
    analyst_upside: Optional[float], sig,
) -> list[str]:
    d: list[str] = []
    gm = score_components.get("Gross Margin", 0)
    if gm == 25 and gross_margin:   d.append(f"Gross margin {gross_margin:.0f}% — elite pricing power")
    elif gm >= 15 and gross_margin: d.append(f"Gross margin {gross_margin:.0f}% — above-average profitability")
    roe_pts = score_components.get("ROE", 0)
    if roe_pts == 20 and roe:   d.append(f"ROE {roe:.0f}% — exceptional capital efficiency")
    elif roe_pts >= 15 and roe: d.append(f"ROE {roe:.0f}% — strong returns on equity")
    fcf = score_components.get("FCF Margin", 0)
    if fcf >= 15 and fcf_margin_raw: d.append(f"FCF margin {fcf_margin_raw:.0f}% — strong cash generation")
    val = score_components.get("Valuation", 0)
    if val == 20 and pe: d.append(f"P/E {pe:.1f}x — attractive valuation")
    grw = score_components.get("Growth", 0)
    if grw >= 10 and revenue_growth: d.append(f"Revenue growth +{revenue_growth:.0f}% — expanding top line")
    rsi = sig.rsi_value
    if rsi and rsi < 30:       d.append(f"RSI {rsi:.0f} — technically oversold")
    elif rsi and rsi < 40:     d.append(f"RSI {rsi:.0f} — approaching oversold")
    if sig.macd_signal == "BULLISH" and sig.trend_strength in ("UPTREND", "STRONG UPTREND"):
        d.append("MACD bullish + uptrend confirmed")
    elif sig.macd_signal == "BULLISH":
        d.append("MACD crossover bullish")
    if week52_momentum and week52_momentum < 25:   d.append(f"{week52_momentum:.0f}% of 52w range — deep value entry")
    elif week52_momentum and week52_momentum > 80: d.append(f"{week52_momentum:.0f}% of 52w range — breakout momentum")
    if analyst_upside and analyst_upside > 25:  d.append(f"Analyst consensus +{analyst_upside:.0f}% upside")
    elif analyst_upside and analyst_upside > 15: d.append(f"Analyst target +{analyst_upside:.0f}% upside")
    return d[:3]


class EnhancedTheme(BaseModel):
    theme: str
    conviction: str
    thesis: str
    catalysts: list[str]
    stocks: list[str]
    timeframe: str
    risk: str
    opportunity_size: str


class ScannedStock(BaseModel):
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    price: Optional[float] = None
    vf_score: int = 0
    signal: Optional[str] = None
    confidence: Optional[int] = None
    rsi: Optional[float] = None
    rsi_signal: Optional[str] = None
    macd_signal: Optional[str] = None
    trend: Optional[str] = None
    stop_loss: Optional[float] = None
    tp1: Optional[float] = None
    tp2: Optional[float] = None
    tp3: Optional[float] = None
    risk_reward: Optional[float] = None
    analyst_target: Optional[float] = None
    analyst_upside: Optional[float] = None
    week52_momentum: Optional[float] = None
    pe_ratio: Optional[float] = None
    roe: Optional[float] = None
    gross_margin: Optional[float] = None
    revenue_growth: Optional[float] = None
    market_cap: Optional[int] = None
    combined_score: float = 0
    why_now: str = ""
    conviction_tier: str = "WATCH"
    score_drivers: list[str] = []
    domain: Optional[str] = None
    has_recent_news: bool = False
    recent_news_count: int = 0
    analyst_target_age_days: Optional[int] = None
    volatility_annual: Optional[float] = None
    suggested_position_pct: Optional[float] = None
    signal_quality: Optional[str] = None


class DomainStat(BaseModel):
    count: int
    avg_score: float
    buy_count: int


class MarketOpportunitiesResponse(BaseModel):
    themes: list[EnhancedTheme]
    top_picks: list[ScannedStock]
    all_ideas: list[ScannedStock]
    total_scanned: int
    passed_count: int
    buy_count: int
    hold_count: int
    sell_count: int
    avg_vf_score: float
    cached_at: Optional[float] = None
    domain_stats: dict[str, DomainStat] = {}


async def _run_scan() -> dict:
    """Run full 220-ticker scan and return raw payload dict."""
    global _cache, _cache_ts
    from collections import defaultdict

    # Build ticker→domain map (first domain wins for duplicates)
    ticker_domain: dict[str, str] = {}
    for domain, tickers in SCAN_UNIVERSE.items():
        for t in tickers:
            if t not in ticker_domain:
                ticker_domain[t] = domain
    unique_tickers = list(ticker_domain.keys())

    loop = asyncio.get_event_loop()

    async def fetch(ticker: str) -> Optional[dict]:
        async with _SEM:
            result = await loop.run_in_executor(None, _quick_scan, ticker)
            if result is not None:
                result["domain"] = ticker_domain[ticker]
            return result

    raw_results = await asyncio.gather(*[fetch(t) for t in unique_tickers], return_exceptions=True)
    results: list[dict] = [r for r in raw_results if isinstance(r, dict)]

    total = len(unique_tickers)
    buy_count  = sum(1 for r in results if r.get("signal") and "BUY"  in r["signal"])
    hold_count = sum(1 for r in results if r.get("signal") == "HOLD")
    sell_count = sum(1 for r in results if r.get("signal") and "SELL" in r["signal"])
    avg_vf = round(sum(r["vf_score"] for r in results) / len(results), 1) if results else 0

    # Lower threshold to VF ≥ 40, keep top 100 by combined score
    passing = sorted(
        [r for r in results if r["vf_score"] >= 40],
        key=lambda x: x["combined_score"], reverse=True
    )[:100]

    # Top 5 conviction picks (BUY signal + VF ≥ 65; fallback to top combined)
    top_5_raw = sorted(
        [r for r in passing if r.get("signal") and "BUY" in r["signal"] and r["vf_score"] >= 65],
        key=lambda x: x["combined_score"], reverse=True
    )
    top_5 = top_5_raw[:5]
    if len(top_5) < 5:
        top_5 += [r for r in passing if r not in top_5][:5 - len(top_5)]

    # Domain stats aggregation
    domain_buckets: dict[str, list] = defaultdict(list)
    for r in passing:
        if r.get("domain"):
            domain_buckets[r["domain"]].append(r)
    domain_stats = {
        domain: {
            "count": len(stocks),
            "avg_score": round(sum(s["combined_score"] for s in stocks) / len(stocks), 1),
            "buy_count": sum(1 for s in stocks if s.get("signal") and "BUY" in s["signal"]),
        }
        for domain, stocks in domain_buckets.items()
    }

    payload = {
        "themes": MARKET_THEMES,
        "top_picks": top_5,
        "all_ideas": passing,
        "total_scanned": total,
        "passed_count": len(passing),
        "buy_count": buy_count,
        "hold_count": hold_count,
        "sell_count": sell_count,
        "avg_vf_score": avg_vf,
        "cached_at": time.time(),
        "domain_stats": domain_stats,
    }

    _cache = payload
    _cache_ts = time.time()
    logger.info("Opportunities scan complete — %d/%d passed, cached for %d min", len(passing), total, CACHE_TTL // 60)
    return payload


def _payload_to_response(p: dict) -> MarketOpportunitiesResponse:
    return MarketOpportunitiesResponse(
        themes=[EnhancedTheme(**t) for t in p["themes"]],
        top_picks=[ScannedStock(**r) for r in p["top_picks"]],
        all_ideas=[ScannedStock(**r) for r in p["all_ideas"]],
        total_scanned=p["total_scanned"],
        passed_count=p["passed_count"],
        buy_count=p["buy_count"],
        hold_count=p["hold_count"],
        sell_count=p["sell_count"],
        avg_vf_score=p["avg_vf_score"],
        cached_at=p.get("cached_at"),
        domain_stats={k: DomainStat(**v) for k, v in p.get("domain_stats", {}).items()},
    )


@router.get("/opportunities", response_model=MarketOpportunitiesResponse)
async def get_opportunities(_: str = Depends(verify_token)):
    global _cache, _cache_ts
    age = time.time() - _cache_ts
    if _cache is not None and age < CACHE_TTL:
        logger.debug("Opportunities served from cache (age %.0fs)", age)
        return _payload_to_response(_cache)
    return _payload_to_response(await _run_scan())


@router.post("/opportunities/refresh", response_model=MarketOpportunitiesResponse)
async def refresh_opportunities(_: str = Depends(verify_token)):
    """Force a fresh scan, bypassing the cache."""
    global _cache_ts
    _cache_ts = 0.0
    return _payload_to_response(await _run_scan())
