import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.factor_grades import _compute_percentile_in_peer_set, _normalize_sector
from config import SECTOR_METRIC_MEDIANS


def test_tie_break_gives_central_percentile():
    # 5 peers all equal to value → tied value should get ~50th pct, not minimum
    value = 10.0
    peers = [10.0, 10.0, 10.0, 10.0, 10.0]
    pct = _compute_percentile_in_peer_set(value, peers, higher_is_better=True)
    assert pct is not None
    # With 6 equal values: count_below=0, count_equal=6, rank=3.5, pct=3.5/6*100≈58.3
    # Should be well above 0 (not first-occurrence bias)
    assert pct > 40.0, f"Expected central percentile, got {pct}"

    # Sanity: higher_is_better=False inverts it
    pct_inv = _compute_percentile_in_peer_set(value, peers, higher_is_better=False)
    assert abs(pct + pct_inv - 100.0) < 1e-6


def test_tie_break_value_among_mixed_peers():
    # value=5, peers=[1,3,5,5,9] → count_below=2, count_equal=3, rank=2+2=4, n=6, pct=4/6*100≈66.7
    value = 5.0
    peers = [1.0, 3.0, 5.0, 5.0, 9.0]
    pct = _compute_percentile_in_peer_set(value, peers, higher_is_better=True)
    assert pct is not None
    # rank = 2 + (3+1)/2 = 4, pct = 4/6*100 = 66.67
    assert abs(pct - 66.67) < 0.1, f"Expected ~66.67, got {pct}"


def test_sector_normalization_financials():
    assert _normalize_sector("Financials") == "Financial Services"
    assert _normalize_sector("Financial Services") == "Financial Services"
    medians_alias = SECTOR_METRIC_MEDIANS.get(_normalize_sector("Financials"))
    medians_direct = SECTOR_METRIC_MEDIANS.get("Financial Services")
    assert medians_alias is medians_direct


def test_sector_normalization_consumer():
    assert _normalize_sector("Consumer Discretionary") == "Consumer Cyclical"
    assert _normalize_sector("Consumer Staples") == "Consumer Defensive"
    assert _normalize_sector("Consumer Cyclical") == "Consumer Cyclical"
    assert _normalize_sector("Consumer Defensive") == "Consumer Defensive"


def test_sector_normalization_unknown_falls_back_to_default():
    assert _normalize_sector("Unknown Sector XYZ") == "_default"
    assert _normalize_sector(None) == "_default"


def test_sector_normalization_case_insensitive():
    assert _normalize_sector("FINANCIALS") == "Financial Services"
    assert _normalize_sector("consumer cyclical") == "Consumer Cyclical"
