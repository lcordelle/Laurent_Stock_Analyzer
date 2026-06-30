from utils.decision_engine import compute_conviction

BULL_SIG = {"signal": "STRONG BUY", "confidence": 80, "signal_quality": "PRIME",
            "trend_strength": "STRONG UPTREND", "adx": 30,
            "optimal_entry": 100.0, "stop_loss": 90.0, "tp1": 120.0, "risk_reward": 2.0}
FCAST_UP = {"forecast_change_pct": 8.0, "trend": "Bullish"}
TUN = {"current_vs_fair_pct": -5.0}  # 5% below fair value (bullish)
RISK_ON = {"regime": "Risk-On", "vix": 14.0}
DANGER  = {"regime": "Danger", "vix": 40.0}

BEAR_SIG = {
    "signal": "STRONG SELL", "confidence": 80, "signal_quality": "PRIME",
    "trend_strength": "STRONG DOWNTREND", "adx": 30,
    "optimal_entry": 100.0, "stop_loss": 110.0, "tp1": 80.0, "risk_reward": 2.0
}
FCAST_DN = {"forecast_change_pct": -8.0}
TUN_OVER = {"current_vs_fair_pct": 5.0}  # 5% above fair value (bearish)


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
    # Strong bullish fundamentals (score=95) vs strongly bearish technicals
    # (SELL signal + STRONG DOWNTREND) with bullish valuation -> raw ~0.055, Stand aside
    bear_sig = {**BULL_SIG, "signal": "SELL", "trend_strength": "STRONG DOWNTREND"}
    d = compute_conviction(
        95, bear_sig,
        {"forecast_change_pct": 8.0},
        {"current_vs_fair_pct": -10.0},
        RISK_ON,
    )
    assert d["direction"] == "Stand aside"


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


def test_short_in_danger_not_dampened():
    # Short direction should NOT be dampened by Danger regime (effective_mult=1.0)
    ro = compute_conviction(30, BEAR_SIG, FCAST_DN, TUN_OVER, RISK_ON)
    dg = compute_conviction(30, BEAR_SIG, FCAST_DN, TUN_OVER, DANGER)

    assert ro["direction"] == "Short", f"Expected Short, got {ro['direction']!r}"
    assert dg["direction"] == "Short", f"Expected Short, got {dg['direction']!r}"
    # Short conviction is identical in Risk-On vs Danger (effective_mult=1.0 in both)
    assert dg["conviction"] == ro["conviction"], (
        f"Short conviction should not be dampened: "
        f"Danger={dg['conviction']} vs Risk-On={ro['conviction']}"
    )
    # Long IS dampened in Danger
    long_ro = compute_conviction(85, BULL_SIG, FCAST_UP, TUN, RISK_ON)["conviction"]
    long_dg = compute_conviction(85, BULL_SIG, FCAST_UP, TUN, DANGER)["conviction"]
    assert long_dg < long_ro, (
        f"Long conviction should be dampened in Danger: "
        f"Danger={long_dg} vs Risk-On={long_ro}"
    )


from utils.decision_engine import quality_grade, read_line


def test_quality_grade_cutoffs():
    assert quality_grade(85) == "A"
    assert quality_grade(70) == "B"
    assert quality_grade(55) == "C"
    assert quality_grade(40) == "D"
    assert quality_grade(20) == "F"
    assert quality_grade(None) is None


def test_read_line_quality_strong_setup_weak():
    s = read_line("A", "Weak", "Long")
    assert "watchlist" in s.lower() or "wait" in s.lower()
    assert "compan" in s.lower() or "quality" in s.lower()


def test_read_line_aligned_strong():
    s = read_line("A", "Prime", "Long")
    assert "buy" in s.lower() or "align" in s.lower() or "strong" in s.lower()


def test_read_line_low_quality():
    s = read_line("F", "Strong", "Long")
    assert "weak" in s.lower() or "poor" in s.lower() or "caution" in s.lower() or "trade" in s.lower()


from utils.decision_engine import decide_action


def test_decide_action_matrix():
    assert decide_action("A", "Prime", "Long") == "STRONG BUY"
    assert decide_action("B", "Strong", "Long") == "BUY"
    assert decide_action("A", "Fair", "Long") == "ACCUMULATE"
    assert decide_action("A", "Weak", "Long") == "WATCH"
    assert decide_action("C", "Strong", "Long") == "BUY"
    assert decide_action("C", "Fair", "Long") == "WATCH"
    assert decide_action("F", "Prime", "Long") == "SPECULATIVE"
    assert decide_action("D", "Weak", "Long") == "AVOID"


def test_decide_action_direction_and_missing():
    assert decide_action("A", "Prime", "Short") == "AVOID"
    assert decide_action("A", "Strong", "Stand aside") == "WATCH"
    assert decide_action(None, "Strong", "Long") == "WATCH"
    assert decide_action("A", None, "Long") == "WATCH"


from utils.decision_engine import HORIZON_PROFILES


def test_decide_action_horizon_divergence():
    from utils.decision_engine import decide_action as da
    # A-quality, Weak setup, Long direction — diverges by horizon
    assert da("A", "Weak", "Long", "day") == "AVOID"
    assert da("A", "Weak", "Long", "swing") == "WATCH"
    assert da("A", "Weak", "Long", "long") == "ACCUMULATE"
    # strong setup
    assert da("A", "Prime", "Long", "day") == "STRONG BUY"
    assert da("F", "Weak", "Long", "long") == "AVOID"


def test_horizon_profiles_shape():
    assert set(HORIZON_PROFILES) == {"day", "swing", "long"}
    for k, p in HORIZON_PROFILES.items():
        assert set(p["weights"]) == {"Technical", "Trend", "Valuation"}
        assert p["window"] > 0 and p["label"]
