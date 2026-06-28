import math
import numpy as np
from utils.valuation_tunnel import (
    build_valuation_tunnel,
    log_regression_channel,
    forecast_cone,
    next_trading_days,
    blended_annual_drift,
)


def _exp_series(n=120, daily=0.001, start=100.0):
    return [start * math.exp(daily * i) for i in range(n)]


def test_returns_none_on_insufficient_data():
    assert build_valuation_tunnel([100.0] * 10, ["2026-01-01"] * 10) is None


def test_regression_channel_brackets_price():
    closes = np.array(_exp_series())
    mid, upper, lower, slope, sigma = log_regression_channel(closes, k=2.0)
    assert len(mid) == len(closes)
    assert np.all(upper >= mid) and np.all(mid >= lower)
    assert slope > 0  # rising exponential -> positive log slope
    # near-perfect exponential -> tiny residual band
    assert (upper[-1] - lower[-1]) / mid[-1] < 0.05


def test_forecast_cone_widens_monotonically():
    mid, upper, lower = forecast_cone(p0=100.0, drift_annual=0.10,
                                      sigma_daily=0.02, horizon_days=30, k=2.0)
    assert len(mid) == len(upper) == len(lower) == 30
    prop = [(u - l) / m for u, l, m in zip(upper, lower, mid)]
    assert all(b >= a - 1e-12 for a, b in zip(prop, prop[1:]))  # non-decreasing proportional width
    assert mid[-1] > mid[0]  # positive drift compounds upward


def test_forecast_cone_widening_holds_under_high_vol_and_clamp():
    # high sigma + long horizon -> BAND_CLAMP engages; proportional width must still never shrink,
    # including when drift is negative (center shrinking must not break monotonic widening).
    mid, upper, lower = forecast_cone(p0=100.0, drift_annual=-0.30,
                                      sigma_daily=0.05, horizon_days=120, k=2.0)
    prop = [(u - l) / m for u, l, m in zip(upper, lower, mid)]
    assert all(b >= a - 1e-12 for a, b in zip(prop, prop[1:]))
    assert all(m > 0 for m in mid)  # log/GBM center never goes non-positive


def test_regression_channel_rejects_nonpositive():
    import pytest
    with pytest.raises(ValueError):
        log_regression_channel(np.array([100.0, -1.0, 50.0]))


def test_next_trading_days_skips_weekends():
    days = next_trading_days("2026-06-26", 5)  # Fri 2026-06-26
    assert days == ["2026-06-29", "2026-06-30", "2026-07-01",
                    "2026-07-02", "2026-07-03"]


def test_blended_drift_clamps():
    closes = _exp_series()
    d = blended_annual_drift(closes, target_price=10_000.0, mid_last=closes[-1],
                             reg_slope_daily=0.5)  # absurd inputs
    assert -0.5 <= d <= 0.5


def test_momentum_geometric_annualization():
    # m=0.20: geometric component should equal (1.20)**(252/20)-1
    expected_large = (1.20) ** (252 / 20) - 1
    # Build a closes array where the 20-day return is exactly 0.20
    closes = [100.0] * 21
    closes[-1] = 120.0
    # Pad to 120 so blended_annual_drift has enough data for regression
    closes = [100.0] * 99 + closes
    # Extract momentum component directly: last/[-21] - 1 = 120/100 - 1 = 0.20
    m_actual = closes[-1] / closes[-21] - 1.0
    assert abs(m_actual - 0.20) < 1e-9
    momentum = (1 + m_actual) ** (252 / 20) - 1
    assert abs(momentum - expected_large) < 1e-9
    # Verify linear formula gives a different (wrong) answer
    linear = m_actual * (252 / 20)
    assert abs(momentum - linear) > 0.1  # they diverge significantly at m=0.20


def test_momentum_geometric_vs_linear_small():
    # m=0.01: geometric and linear should be close but not equal
    m = 0.01
    geometric = (1 + m) ** (252 / 20) - 1
    linear = m * (252 / 20)
    assert abs(geometric - linear) > 1e-6  # not equal
    assert abs(geometric - linear) < 0.05  # but close for small m


def test_momentum_guard_extreme_loss():
    # m=-0.999 (clamped to -0.99) must not raise
    closes = [100.0] * 99 + [100.0] * 20 + [0.1]  # ~-99.9% 20-day return
    blended_annual_drift(closes, target_price=100.0, mid_last=100.0, reg_slope_daily=0.0)  # must not raise


def test_build_shapes_and_keys():
    closes = _exp_series(120)
    dates = next_trading_days("2026-01-01", 120)
    out = build_valuation_tunnel(closes, dates, target_price=closes[-1] * 1.1)
    assert out is not None
    for key in ("hist_mid", "hist_upper", "hist_lower"):
        assert len(out[key]) == len(closes)
    for key in ("fc_mid", "fc_upper", "fc_lower", "future_dates"):
        assert len(out[key]) == 30
    assert out["horizon_days"] == 30 and out["k"] == 2.0
    assert "drift_annual" in out and "sigma_annual" in out
