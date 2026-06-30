# tests/test_calibration.py
import math
import numpy as np
import pandas as pd
from utils.calibration import (
    regime_for_vix, synth_signals, bar_conviction,
    observations_for_history, bucketize, lookup, HORIZON_DAYS,
)


def test_regime_for_vix_bands():
    assert regime_for_vix(12)["regime"] == "Risk-On"
    assert regime_for_vix(20)["regime"] == "Risk-Off"
    assert regime_for_vix(30)["regime"] == "Danger"
    assert regime_for_vix(None)["regime"] == "Unknown"


def test_synth_signals_directions():
    bull = synth_signals(rsi=65, macd_hist=1.2, sma20=110, sma50=105, sma200=100, adx=30, close=112)
    assert "UP" in (bull["trend_strength"] or "")
    assert "BUY" in bull["signal"]
    bear = synth_signals(rsi=35, macd_hist=-1.2, sma20=90, sma50=95, sma200=100, adx=30, close=88)
    assert "DOWN" in (bear["trend_strength"] or "")
    assert "SELL" in bear["signal"]


def test_bar_conviction_bounds_and_direction():
    conv, direction = bar_conviction(rsi=70, macd_hist=1.5, sma20=110, sma50=105, sma200=100,
                                     adx=30, close=112, vix=12)
    assert 0 <= conv <= 10
    assert direction in ("Long", "Short", "Stand aside")
    assert direction == "Long"  # strong bull, calm regime


def test_observations_no_lookahead_and_count():
    n = 160  # > 60 + HORIZON warmup so observations are actually generated
    close = pd.Series([100 * (1.002 ** i) for i in range(n)])
    hist = pd.DataFrame({"Open": close, "High": close, "Low": close, "Close": close,
                         "Volume": [1e6] * n})
    vix = pd.Series([14.0] * n)
    obs = observations_for_history(hist, vix, horizon=HORIZON_DAYS)
    # last HORIZON bars dropped (no forward data)
    assert len(obs) <= n - HORIZON_DAYS
    assert len(obs) > 0  # non-vacuous: a working impl emits observations
    for o in obs:
        assert set(o) == {"conviction", "direction", "fwd_return"}
        assert 0 <= o["conviction"] <= 10


def test_bucketize_and_lookup():
    obs = [
        {"conviction": 9.0, "direction": "Long", "fwd_return": 0.05},
        {"conviction": 9.0, "direction": "Long", "fwd_return": -0.01},
        {"conviction": 9.0, "direction": "Long", "fwd_return": 0.03},
        {"conviction": 1.0, "direction": "Stand aside", "fwd_return": 0.10},  # excluded from hit
    ]
    buckets = bucketize(obs)
    top = lookup(buckets, 8.5)
    assert top["label"] == "8–10"
    assert top["n"] == 3                         # the 3 Long obs
    assert abs(top["hit_rate"] - round(2 / 3 * 100, 1)) < 0.05
    low = lookup(buckets, 1.0)
    assert low["n"] == 0 or low["hit_rate"] is None   # stand-aside-only -> no hit-rate


def test_lookup_clamps_to_range():
    buckets = bucketize([{"conviction": 5.0, "direction": "Long", "fwd_return": 0.01}])
    assert lookup(buckets, 10.0) is not None
    assert lookup(buckets, 0.0) is not None


from utils.calibration import conviction_percentiles, percentile_of, band_for


def test_conviction_percentiles_span_and_monotonic():
    obs = [{"conviction": float(i % 11), "direction": "Long", "fwd_return": 0.01} for i in range(500)]
    bp = conviction_percentiles(obs)
    assert bp[0]["p"] == 0 and bp[-1]["p"] == 100
    vals = [b["value"] for b in bp]
    assert all(b >= a for a, b in zip(vals, vals[1:]))


def test_percentile_of_interpolates_and_clamps():
    obs = [{"conviction": float(i) / 100 * 10, "direction": "Long", "fwd_return": 0.0} for i in range(101)]
    bp = conviction_percentiles(obs)
    assert abs(percentile_of(bp, 5.0) - 50) < 12
    assert percentile_of(bp, -1) == 0.0
    assert percentile_of(bp, 99) == 100.0
    assert percentile_of([], 5.0) is None


def test_band_for_cutoffs():
    assert band_for(49) == "Weak"
    assert band_for(50) == "Fair"
    assert band_for(80) == "Strong"
    assert band_for(95) == "Prime"
    assert band_for(None) is None


def test_observations_honor_weights():
    import numpy as np
    import pandas as pd
    from utils.calibration import observations_for_history, HORIZON_DAYS
    n = 200
    close = pd.Series([100 * (1.001 ** i) + (i % 7) for i in range(n)])
    hist = pd.DataFrame({"Open": close, "High": close * 1.01, "Low": close * 0.99,
                         "Close": close, "Volume": [1e6] * n})
    vix = pd.Series([16.0] * n)
    day = observations_for_history(hist, vix, HORIZON_DAYS, {"Technical": 0.6, "Trend": 0.3, "Valuation": 0.1})
    lng = observations_for_history(hist, vix, HORIZON_DAYS, {"Technical": 0.2, "Trend": 0.3, "Valuation": 0.5})
    assert len(day) == len(lng) and len(day) > 0
    # different weight profiles must move at least some convictions
    assert any(abs(d["conviction"] - l["conviction"]) > 1e-6 for d, l in zip(day, lng))
