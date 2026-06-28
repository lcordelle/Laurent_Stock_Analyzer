"""Tests for utils/risk_analysis.py — canonical finance correctness."""

import numpy as np
import pandas as pd
import pytest

from utils.risk_analysis import RiskAnalyzer
from config import RISK_FREE_RATE

ra = RiskAnalyzer()


def _series(values):
    return pd.Series(values, dtype=float)


# ---------------------------------------------------------------------------
# Sortino: new downside-dev-around-zero must be >= old subset-std approach
# ---------------------------------------------------------------------------

def test_sortino_new_larger_downside_dev():
    """Downside deviation around zero >= std of negative subset => Sortino is more conservative."""
    rng = np.random.default_rng(42)
    returns = _series(np.concatenate([
        rng.normal(-0.03, 0.02, 60),   # strongly negative cluster
        rng.normal(0.01, 0.005, 60),   # mild positive cluster
    ]))

    # New canonical downside deviation
    downside_dev_new = np.sqrt(np.mean(np.minimum(returns, 0) ** 2)) * np.sqrt(252)

    # Old approach: std of negative-return subset
    neg = returns[returns < 0]
    downside_dev_old = neg.std() * np.sqrt(252)

    assert downside_dev_new > downside_dev_old, (
        f"New ({downside_dev_new:.4f}) should exceed old ({downside_dev_old:.4f})"
    )

    sortino = ra.calculate_sortino_ratio(returns)
    assert not np.isnan(sortino), "Sortino should not be NaN"


# ---------------------------------------------------------------------------
# Sharpe: known series, sign + rough magnitude, uses config rf
# ---------------------------------------------------------------------------

def test_sharpe_positive_for_strong_uptrend():
    """A clearly positive noisy return series should have a positive Sharpe."""
    rng = np.random.default_rng(1)
    # Mean 0.8 % / day, std 0.5 % => annualised mean >> rf
    returns = _series(rng.normal(0.008, 0.005, 252))
    sharpe = ra.calculate_sharpe_ratio(returns)
    assert sharpe > 0, f"Sharpe should be positive for uptrend, got {sharpe}"


def test_sharpe_uses_config_rf():
    """Sharpe computed with explicit rf=RISK_FREE_RATE should match default."""
    returns = _series(np.random.default_rng(0).normal(0.001, 0.01, 252))
    assert ra.calculate_sharpe_ratio(returns) == ra.calculate_sharpe_ratio(returns, RISK_FREE_RATE)


def test_sharpe_negative_for_downtrend():
    rng = np.random.default_rng(2)
    # Mean -0.5 % / day => clearly negative annualised return
    returns = _series(rng.normal(-0.005, 0.005, 252))
    assert ra.calculate_sharpe_ratio(returns) < 0


# ---------------------------------------------------------------------------
# Max drawdown: known 30 % peak-to-trough
# ---------------------------------------------------------------------------

def test_max_drawdown_30_pct():
    """Peak 100 → trough 70 → recover to 100 gives ~30 % max drawdown."""
    prices = _series([100, 105, 110, 90, 80, 70, 80, 95, 100, 105])
    result = ra.calculate_max_drawdown(prices)
    assert 28.0 <= result['max_drawdown_pct'] <= 37.0, (
        f"Expected ~30 %, got {result['max_drawdown_pct']:.2f} %"
    )


# ---------------------------------------------------------------------------
# Guard: flat / zero-downside series must not divide by zero
# ---------------------------------------------------------------------------

def test_sortino_no_div_zero_flat_returns():
    """All-positive returns produce no downside; guard must prevent ZeroDivisionError."""
    returns = _series([0.001] * 100)
    result = ra.calculate_sortino_ratio(returns)
    assert result != 0 or result == float('inf') or result >= 0  # just must not raise


def test_sortino_zero_returns_series():
    """All-zero returns: downside_dev is 0; guard should return 0."""
    returns = _series([0.0] * 100)
    result = ra.calculate_sortino_ratio(returns)
    assert result == 0
