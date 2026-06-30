import asyncio

from api.models.responses import (
    FullStockAnalysis, Decision, HorizonDecision, Quality, Setup,
    DecisionRegime, StockMetrics,
)
from api.routes import opportunities


def _mk_setup(score, band, pct, direction="Long"):
    return Setup(
        score=score, direction=direction, percentile=pct, band=band,
        factors=[], regime=DecisionRegime(label="Neutral", vix=15.0, multiplier=1.0),
        horizon_days=30,
    )


def test_radar_builder_mirrors_decision(monkeypatch):
    dec = Decision(
        quality=Quality(score=90, grade="A"),
        default_horizon="swing",
        horizons={
            "day":   HorizonDecision(action="AVOID",      read="r", setup=_mk_setup(2.0, "Weak", 10)),
            "swing": HorizonDecision(action="WATCH",      read="r", setup=_mk_setup(4.0, "Weak", 20)),
            "long":  HorizonDecision(action="ACCUMULATE", read="r", setup=_mk_setup(4.0, "Weak", 20)),
        },
    )
    fake = FullStockAnalysis(
        ticker="INTU", company_name="Intuit",
        metrics=StockMetrics(current_price=600.0),
        earnings_dates=[], decision=dec,
    )
    monkeypatch.setattr(opportunities, "_analyze_ticker", lambda t, p="1y": fake)

    out = asyncio.run(opportunities._full_scan_ticker("INTU", domain="SaaS"))

    assert out is not None
    assert out.quality_grade == "A" and out.quality_score == 90
    assert out.default_horizon == "swing"
    assert set(out.horizons) == {"day", "swing", "long"}
    # urgency derived from the unified action, not a separate engine
    assert out.horizons["swing"].urgency == "WATCH"   # WATCH -> WATCH
    assert out.horizons["day"].urgency == "REST"       # AVOID -> REST
    assert out.horizons["long"].urgency == "WATCH"     # ACCUMULATE -> WATCH
    # band/action mirror the decision exactly
    assert out.horizons["long"].band == "Weak"
    assert out.horizons["day"].action == "AVOID"
    # conviction 4.0 -> size cap 40%
    assert out.horizons["swing"].size_cap_pct == 40


def test_radar_builder_skips_when_no_decision(monkeypatch):
    fake = FullStockAnalysis(ticker="XYZ", metrics=StockMetrics(current_price=10.0),
                             earnings_dates=[], decision=None)
    monkeypatch.setattr(opportunities, "_analyze_ticker", lambda t, p="1y": fake)
    assert asyncio.run(opportunities._full_scan_ticker("XYZ")) is None


from api.routes.opportunities import _keep_previous_cache


def test_keep_previous_cache_guard():
    # healthy cache, thin new scan -> keep previous
    assert _keep_previous_cache(10, 100) is True
    assert _keep_previous_cache(50, 100) is True       # 50 < 60
    # new scan as complete (or more) than previous -> accept
    assert _keep_previous_cache(64, 100) is False      # 64 >= 60
    assert _keep_previous_cache(100, 100) is False
    assert _keep_previous_cache(120, 100) is False
    # near-empty new scan with any previous -> keep
    assert _keep_previous_cache(3, 10) is True
    # cold start (no previous) -> accept whatever we got
    assert _keep_previous_cache(10, 0) is False
    # small previous (<20) only protected by the <5 rule
    assert _keep_previous_cache(8, 15) is False
    assert _keep_previous_cache(2, 15) is True
