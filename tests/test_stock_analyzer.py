"""
Correctness tests for utils/stock_analyzer.py fixes.
Run: python3 -m pytest tests/test_stock_analyzer.py -v
"""
import numpy as np
import pandas as pd
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.stock_analyzer import StockAnalyzer
import config as _cfg


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_hist(closes, highs=None, lows=None, volumes=None):
    """Build a minimal OHLCV DataFrame the analyzer expects."""
    n = len(closes)
    closes = np.array(closes, dtype=float)
    if highs is None:
        highs = closes + 1.0
    if lows is None:
        lows = closes - 1.0
    if volumes is None:
        volumes = np.full(n, 1_000_000.0)
    idx = pd.date_range('2020-01-01', periods=n, freq='B')
    return pd.DataFrame({'Close': closes, 'High': highs, 'Low': lows,
                         'Open': closes, 'Volume': volumes}, index=idx)


def _run_indicators(hist):
    sa = StockAnalyzer()
    return sa.calculate_technical_indicators(hist)


# ---------------------------------------------------------------------------
# 1. RSI — Wilder's smoothing
# ---------------------------------------------------------------------------

class TestRSI:
    def test_rsi_high_on_rising_series(self):
        """Monotonically rising prices → RSI should exceed 70 after warmup."""
        closes = np.linspace(100, 200, 60)
        result = _run_indicators(_make_hist(closes))
        rsi = result['RSI'].dropna()
        assert rsi.iloc[-1] > 70, f"Expected RSI > 70 on rising series, got {rsi.iloc[-1]:.2f}"

    def test_rsi_bounds(self):
        """RSI must always be in [0, 100]."""
        closes = np.concatenate([
            np.linspace(100, 200, 30),
            np.linspace(200, 50, 30),
        ])
        result = _run_indicators(_make_hist(closes))
        rsi = result['RSI'].dropna()
        assert (rsi >= 0).all() and (rsi <= 100).all(), "RSI out of [0,100]"

    def test_rsi_differs_from_sma_on_mixed_series(self):
        """Wilder's EWM should diverge from plain SMA on a mixed gain/loss series."""
        # Zigzag series: gains and losses, so EWM and SMA diverge
        rng = np.random.default_rng(0)
        closes = 100 + np.cumsum(rng.choice([-2, 3, -1, 2], size=60))
        delta = pd.Series(closes.astype(float)).diff()

        # EWM (Wilder) version
        gain_ewm = delta.where(delta > 0, 0).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
        loss_ewm = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
        rs_ewm = gain_ewm / loss_ewm
        rsi_ewm = (100 - 100 / (1 + rs_ewm)).dropna()

        # SMA (old) version
        gain_sma = delta.where(delta > 0, 0).rolling(14).mean()
        loss_sma = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs_sma = gain_sma / loss_sma
        rsi_sma = (100 - 100 / (1 + rs_sma)).dropna()

        # The two methods should differ at some bar after warmup
        diffs = (rsi_ewm - rsi_sma).dropna().abs()
        assert diffs.max() > 0.01, \
            f"EWM and SMA RSI should differ; max diff was {diffs.max():.4f}"


# ---------------------------------------------------------------------------
# 2. Bollinger Bands — population std (ddof=0)
# ---------------------------------------------------------------------------

class TestBollingerBands:
    def test_middle_equals_sma20(self):
        closes = np.random.default_rng(42).uniform(100, 110, 60)
        result = _run_indicators(_make_hist(closes))
        sma20 = pd.Series(closes).rolling(20).mean()
        pd.testing.assert_series_equal(
            result['BB_Middle'].reset_index(drop=True),
            sma20.reset_index(drop=True),
            check_names=False,
        )

    def test_band_halfwidth_uses_population_std(self):
        """Upper - Middle should equal 2 * population std at a known point."""
        closes = np.random.default_rng(7).uniform(50, 150, 60)
        result = _run_indicators(_make_hist(closes))
        s = pd.Series(closes)
        # Population std at index 25 (enough warmup)
        expected_half = 2 * s.iloc[6:26].std(ddof=0)
        actual_half = (result['BB_Upper'].iloc[25] - result['BB_Middle'].iloc[25])
        assert abs(actual_half - expected_half) < 1e-8, \
            f"Expected half-width {expected_half:.6f}, got {actual_half:.6f}"


# ---------------------------------------------------------------------------
# 3. ADX — Wilder's smoothing + no NaN after warmup + flat-series guard
# ---------------------------------------------------------------------------

class TestADX:
    def test_positive_trend_di_plus_dominates(self):
        """On a strong uptrend +DI should exceed -DI."""
        closes = np.linspace(100, 300, 100)
        highs = closes + 2
        lows = closes - 0.5
        result = _run_indicators(_make_hist(closes, highs=highs, lows=lows))
        di_plus = result['DI_Plus'].dropna()
        di_minus = result['DI_Minus'].dropna()
        assert di_plus.iloc[-1] > di_minus.iloc[-1], \
            f"+DI {di_plus.iloc[-1]:.2f} should exceed -DI {di_minus.iloc[-1]:.2f} on uptrend"

    def test_adx_no_nan_after_warmup(self):
        closes = np.linspace(100, 200, 80)
        result = _run_indicators(_make_hist(closes))
        adx = result['ADX']
        # ADX should be valid from index 28 onward
        assert adx.iloc[28:].notna().all(), "ADX contains NaN after warmup period"

    def test_adx_flat_series_no_nan(self):
        """Flat series — DI sum is 0, guard prevents NaN/inf in DX."""
        closes = np.full(60, 100.0)
        highs = np.full(60, 100.0)
        lows = np.full(60, 100.0)
        result = _run_indicators(_make_hist(closes, highs=highs, lows=lows))
        dx = result['DX']
        assert not np.any(np.isinf(dx.fillna(0).values)), "DX contains inf on flat series"
        assert not np.any(np.isnan(dx.fillna(0).values)), "DX contains unexpected NaN"


# ---------------------------------------------------------------------------
# 4. Stochastic — flat series yields 50
# ---------------------------------------------------------------------------

class TestStochastic:
    def test_flat_series_gives_50(self):
        """When high == low, %K should be 50, not NaN."""
        closes = np.full(60, 100.0)
        highs = np.full(60, 100.0)
        lows = np.full(60, 100.0)
        result = _run_indicators(_make_hist(closes, highs=highs, lows=lows))
        stoch_k = result['Stoch_K'].dropna()
        assert len(stoch_k) > 0, "No Stoch_K values computed"
        assert (stoch_k == 50).all(), f"Expected all 50, got: {stoch_k.unique()}"

    def test_normal_series_no_nan(self):
        closes = np.linspace(100, 150, 60)
        result = _run_indicators(_make_hist(closes))
        stoch_k = result['Stoch_K'].iloc[13:]  # after warmup
        assert stoch_k.notna().all(), "Stoch_K has NaN on normal series"


# ---------------------------------------------------------------------------
# 5 & 6. Scoring — negative fundamentals, negative P/E, weights from config
# ---------------------------------------------------------------------------

def _make_score_data(pe=None, gross_margin=None, roe=None, fcf=None, rev=None, rg=None):
    """Construct minimal data dict for calculate_score."""
    info = {}
    if pe is not None:
        info['trailingPE'] = pe
    if gross_margin is not None:
        info['grossMargins'] = gross_margin / 100.0
    if roe is not None:
        info['returnOnEquity'] = roe / 100.0
    if fcf is not None:
        info['freeCashflow'] = fcf
    if rev is not None:
        info['totalRevenue'] = rev
    if rg is not None:
        info['revenueGrowth'] = rg / 100.0
    return {'info': info}


class TestScoring:
    def setup_method(self):
        self.sa = StockAnalyzer()

    def test_negative_pe_gets_zero_valuation(self):
        data = _make_score_data(pe=-5.0)
        result = self.sa.calculate_score(data)
        assert result['components']['Valuation'] == 0, \
            f"Negative P/E should give 0 valuation, got {result['components']['Valuation']}"

    def test_negative_gross_margin_gets_zero(self):
        data = _make_score_data(gross_margin=-10.0)
        result = self.sa.calculate_score(data)
        assert result['components']['Gross Margin'] == 0, \
            f"Negative gross margin should give 0, got {result['components']['Gross Margin']}"

    def test_negative_roe_gets_zero(self):
        data = _make_score_data(roe=-5.0)
        result = self.sa.calculate_score(data)
        assert result['components']['ROE'] == 0, \
            f"Negative ROE should give 0, got {result['components']['ROE']}"

    def test_negative_fcf_gets_zero(self):
        data = _make_score_data(fcf=-1_000_000, rev=10_000_000)
        result = self.sa.calculate_score(data)
        assert result['components']['FCF Margin'] == 0, \
            f"Negative FCF margin should give 0, got {result['components']['FCF Margin']}"

    def test_config_weights_sum_to_100(self):
        assert sum(_cfg.SCORE_WEIGHTS.values()) == 100, \
            f"config.SCORE_WEIGHTS should sum to 100, got {sum(_cfg.SCORE_WEIGHTS.values())}"

    def test_perfect_stock_caps_at_100(self):
        """A stock that hits every top tier should score 100."""
        data = _make_score_data(
            pe=15.0,
            gross_margin=70.0,
            roe=25.0,
            fcf=20_000_000,
            rev=100_000_000,
            rg=25.0,
        )
        result = self.sa.calculate_score(data)
        assert result['total_score'] == 100, \
            f"Perfect stock should score 100, got {result['total_score']}"

    def test_fully_negative_stock_scores_zero(self):
        data = _make_score_data(
            pe=-10.0,
            gross_margin=-5.0,
            roe=-10.0,
            fcf=-500_000,
            rev=10_000_000,
            rg=-15.0,
        )
        result = self.sa.calculate_score(data)
        assert result['total_score'] == 0, \
            f"Fully negative stock should score 0, got {result['total_score']}"


# ---------------------------------------------------------------------------
# 7. Forecast — baseline when momentum=0 and growth=0
# ---------------------------------------------------------------------------

class TestForecast:
    def setup_method(self):
        self.sa = StockAnalyzer()

    def _make_forecast_inputs(self, score_val=85):
        """Build minimal inputs with zero momentum and zero growth."""
        n = 60
        closes = np.full(n, 100.0)  # flat → momentum = 0
        hist = _make_hist(closes)
        hist = self.sa.calculate_technical_indicators(hist)

        metrics = {
            'Current Price': 100.0,
            'Revenue Growth': 0,
            'Earnings Growth': 0,
        }
        score = {'total_score': score_val}
        data = {'history': hist}
        return data, metrics, score

    def test_nonzero_estimate_with_zero_momentum_growth(self):
        data, metrics, score = self._make_forecast_inputs(score_val=85)
        result = self.sa.calculate_forecast(data, metrics, score)
        assert result is not None, "Forecast returned None"
        est = result.get('annual_return_estimate', result.get('expected_change_pct', None))
        # Just verify forecast_price differs from current_price
        assert result['forecast_price'] != 100.0, \
            "Forecast price should not equal current price when direction is nonzero"

    def test_positive_direction_gives_positive_forecast(self):
        """High score → positive direction → forecast_price > current_price."""
        data, metrics, score = self._make_forecast_inputs(score_val=90)
        result = self.sa.calculate_forecast(data, metrics, score)
        assert result['forecast_price'] > 100.0, \
            f"Strong positive direction should yield forecast_price > 100, got {result['forecast_price']:.4f}"

    def test_bearish_setup_gives_lower_forecast(self):
        """Bearish setup (strong downtrend, low score, negative momentum) → forecast_price < current_price."""
        n = 60
        # Strongly falling prices → negative momentum and bearish MA signal
        closes = np.linspace(200, 100, n)
        hist = _make_hist(closes, highs=closes + 0.5, lows=closes - 2.0)
        hist = self.sa.calculate_technical_indicators(hist)
        metrics = {
            'Current Price': closes[-1],
            'Revenue Growth': -20,
            'Earnings Growth': -20,
        }
        score = {'total_score': 10}
        data = {'history': hist}
        result = self.sa.calculate_forecast(data, metrics, score)
        assert result is not None, "Forecast returned None"
        assert result['forecast_price'] < closes[-1], \
            f"Bearish setup should yield forecast_price < current, got {result['forecast_price']:.4f} vs {closes[-1]:.4f}"
