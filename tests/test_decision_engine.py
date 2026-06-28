from utils.decision_engine import compute_conviction

BULL_SIG = {"signal": "STRONG BUY", "confidence": 80, "signal_quality": "PRIME",
            "trend_strength": "STRONG UPTREND", "adx": 30,
            "optimal_entry": 100.0, "stop_loss": 90.0, "tp1": 120.0, "risk_reward": 2.0}
FCAST_UP = {"forecast_change_pct": 8.0, "trend": "Bullish"}
TUN = {"current_vs_fair_pct": -5.0}  # 5% below fair value (bullish)
RISK_ON = {"regime": "Risk-On", "vix": 14.0}
DANGER  = {"regime": "Danger", "vix": 40.0}


def test_strong_bull_is_long_high_conviction():
    d = compute_conviction(85, BULL_SIG, FCAST_UP, TUN, RISK_ON)
    assert d["direction"] == "Long"
    assert d["conviction"] >= 7.0
    assert 0 <= d["conviction"] <= 10


def test_regime_danger_dampens_long():
    on = compute_conviction(85, BULL_SIG, FCAST_UP, TUN, RISK_ON)["conviction"]
    dg = compute_conviction(85, BULL_SIG, FCAST_UP, TUN, DANGER)["conviction"]
    assert dg < on


def test_higher_fundamentals_raise_conviction():
    lo = compute_conviction(55, BULL_SIG, FCAST_UP, TUN, RISK_ON)["conviction"]
    hi = compute_conviction(95, BULL_SIG, FCAST_UP, TUN, RISK_ON)["conviction"]
    assert hi >= lo


def test_conflict_is_stand_aside():
    bear_sig = {**BULL_SIG, "signal": "SELL", "trend_strength": "WEAK DOWNTREND"}
    d = compute_conviction(50, bear_sig, {"forecast_change_pct": 0.5}, {"current_vs_fair_pct": 0.0}, RISK_ON)
    assert d["direction"] in ("Stand aside", "Short")


def test_weights_renormalize_when_factor_missing():
    # no forecast / tunnel -> valuation factor dropped, still bounded, still Long
    d = compute_conviction(85, BULL_SIG, None, None, RISK_ON)
    assert 0 <= d["conviction"] <= 10
    assert d["direction"] == "Long"


def test_ev_r_present_with_stop_absent_without():
    d = compute_conviction(85, BULL_SIG, FCAST_UP, TUN, RISK_ON)
    assert d["expected_value_r"] is not None
    no_stop = {**BULL_SIG, "stop_loss": None}
    d2 = compute_conviction(85, no_stop, FCAST_UP, TUN, RISK_ON)
    assert d2["expected_value_r"] is None
