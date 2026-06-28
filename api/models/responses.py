from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OHLCVRow(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class ScoreBreakdown(BaseModel):
    total: int
    components: dict[str, int]


class StockMetrics(BaseModel):
    current_price: Optional[float] = None
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    peg_ratio: Optional[float] = None
    price_to_book: Optional[float] = None
    dividend_yield: Optional[float] = None
    market_cap: Optional[float] = None
    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    profit_margin: Optional[float] = None
    roe: Optional[float] = None
    roa: Optional[float] = None
    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None
    beta: Optional[float] = None
    target_price: Optional[float] = None
    analyst_rating: Optional[str] = None
    number_of_analysts: Optional[int] = None
    recommendation_mean: Optional[float] = None
    volume: Optional[float] = None
    average_volume: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None


class ForecastResult(BaseModel):
    current_price: float
    forecast_price: float
    forecast_change_pct: float
    forecast_type: str
    probability: float
    momentum: float
    volatility: float
    trend: str


class IndicatorData(BaseModel):
    sma_20: list[Optional[float]] = []
    sma_50: list[Optional[float]] = []
    sma_200: list[Optional[float]] = []
    rsi: list[Optional[float]] = []
    macd: list[Optional[float]] = []
    macd_signal: list[Optional[float]] = []
    bb_upper: list[Optional[float]] = []
    bb_lower: list[Optional[float]] = []
    obv: list[Optional[float]] = []
    vwap: list[Optional[float]] = []


class ValuationTunnel(BaseModel):
    hist_mid: list[Optional[float]]
    hist_upper: list[Optional[float]]
    hist_lower: list[Optional[float]]
    future_dates: list[str]
    fc_mid: list[float]
    fc_upper: list[float]
    fc_lower: list[float]
    horizon_days: int
    k: float
    drift_annual: float
    sigma_annual: float


class DecisionFactor(BaseModel):
    label: str
    subscore: Optional[float] = None
    weight: float
    contribution: Optional[float] = None
    detail: str


class DecisionRegime(BaseModel):
    label: str
    vix: Optional[float] = None
    multiplier: float


class Decision(BaseModel):
    conviction: float
    direction: str
    factors: list[DecisionFactor]
    regime: DecisionRegime
    expected_value_r: Optional[float] = None
    rationale: str


class TradingSignals(BaseModel):
    signal: Optional[str] = None
    confidence: Optional[int] = None
    optimal_entry: Optional[float] = None
    stop_loss: Optional[float] = None
    tp1: Optional[float] = None
    tp2: Optional[float] = None
    tp3: Optional[float] = None
    rsi_value: Optional[float] = None
    rsi_signal: Optional[str] = None
    macd_signal: Optional[str] = None
    trend_strength: Optional[str] = None
    risk_reward: Optional[float] = None
    rsi_reversal_zone_low: Optional[float] = None
    rsi_reversal_zone_high: Optional[float] = None
    rsi_bullish_reversals: Optional[int] = None
    rsi_bearish_reversals: Optional[int] = None
    rsi_at_reversal_zone: Optional[bool] = None
    rsi_reversal_signal: Optional[str] = None
    adx: Optional[float] = None
    weekly_rsi: Optional[float] = None
    sr_nearest_support: Optional[float] = None
    sr_nearest_resistance: Optional[float] = None
    sr_at_support: Optional[bool] = None
    sr_at_resistance: Optional[bool] = None
    earnings_proximity: Optional[str] = None
    signal_quality: Optional[str] = None


class NewsArticle(BaseModel):
    title: str
    summary: Optional[str] = None
    url: Optional[str] = None
    published: Optional[str] = None
    sentiment: Optional[str] = None


class AnalystRating(BaseModel):
    recommendation: Optional[str] = None
    mean: Optional[float] = None
    count: Optional[int] = None
    target_high: Optional[float] = None
    target_low: Optional[float] = None
    target_mean: Optional[float] = None


class PeerData(BaseModel):
    ticker: str
    score: Optional[int] = None
    price: Optional[float] = None
    pe_ratio: Optional[float] = None
    gross_margin: Optional[float] = None


class ShortInterestData(BaseModel):
    short_ratio: Optional[float] = None
    short_pct_float: Optional[float] = None
    shares_short: Optional[int] = None
    insider_own_pct: Optional[float] = None
    institution_own_pct: Optional[float] = None


class EarningsDate(BaseModel):
    date: str
    eps_estimate: Optional[float] = None
    eps_actual: Optional[float] = None
    surprise_pct: Optional[float] = None
    beat: Optional[bool] = None


class RiskProfileData(BaseModel):
    volatility: Optional[float] = None
    var_5pct: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    max_drawdown_pct: Optional[float] = None


class Calibration(BaseModel):
    available: bool
    as_of: Optional[str] = None
    horizon_days: Optional[int] = None
    n: Optional[int] = None
    bucket_label: Optional[str] = None
    hit_rate: Optional[float] = None
    avg_forward_return: Optional[float] = None
    low_sample: Optional[bool] = None
    proxy_conviction: Optional[float] = None
    note: Optional[str] = None


class FullStockAnalysis(BaseModel):
    ticker: str
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    ohlcv: list[OHLCVRow] = []
    metrics: Optional[StockMetrics] = None
    score: Optional[ScoreBreakdown] = None
    forecast: Optional[ForecastResult] = None
    indicators: Optional[IndicatorData] = None
    valuation_tunnel: Optional["ValuationTunnel"] = None
    decision: Optional["Decision"] = None
    calibration: Optional["Calibration"] = None
    trading_signals: Optional[TradingSignals] = None
    risk_profile: Optional[RiskProfileData] = None
    news: list[NewsArticle] = []
    analyst_rating: Optional[AnalystRating] = None
    peers: list[PeerData] = []
    short_interest: Optional[ShortInterestData] = None
    earnings_dates: list[EarningsDate] = []
    relative_strength: list[Optional[float]] = []
    analyst_target_age_days: Optional[int] = None
    error: Optional[str] = None
    data_source: Optional[str] = None
    cached_at: Optional[str] = None
    is_stale: bool = False


class BatchAnalysisResponse(BaseModel):
    results: list[FullStockAnalysis]
    total: int
    failed: list[str] = []


class ScreenerResult(BaseModel):
    results: list[FullStockAnalysis]
    total_screened: int
    total_passed: int


class GradeItem(BaseModel):
    grade: str = "N/A"
    percentile: Optional[float] = None
    tooltip: str = ""


class FactorGradesResponse(BaseModel):
    ticker: str
    sector: str
    n_peers: int
    grades: dict[str, GradeItem]


class DividendGradeSet(BaseModel):
    safety: GradeItem = GradeItem()
    growth: GradeItem = GradeItem()
    yield_grade: GradeItem = GradeItem()
    consistency: GradeItem = GradeItem()


class DividendScorecardResponse(BaseModel):
    ticker: str
    pays_dividend: bool
    current_yield: Optional[float] = None
    annual_rate: Optional[float] = None
    grades: Optional[DividendGradeSet] = None


class EpsHistoryItem(BaseModel):
    date: str
    eps_actual: Optional[float] = None
    eps_estimate: Optional[float] = None
    surprise_pct: Optional[float] = None
    beat: Optional[bool] = None


class EarningsAnalysisResponse(BaseModel):
    ticker: str
    data_available: bool
    eps_history: list[EpsHistoryItem] = []
    beat_rate_4q: Optional[float] = None
    avg_surprise_pct_4q: Optional[float] = None
    next_earnings_date: Optional[str] = None


class AiAnalystSections(BaseModel):
    executive_summary: Optional[str] = None
    bulls_say: list[str] = []
    bears_say: list[str] = []
    key_risks: Optional[str] = None
    investment_thesis: Optional[str] = None


class AiAnalystReportResponse(BaseModel):
    ticker: str
    provider: Optional[str] = None
    model_name: Optional[str] = None
    sections: AiAnalystSections = AiAnalystSections()
    error: Optional[str] = None


class VerdictSignalDetail(BaseModel):
    label: str
    score: int
    weight: float


class VerdictResponse(BaseModel):
    verdict: str
    confidence: int
    vf_score: int
    signals: dict[str, VerdictSignalDetail]
    price_target: Optional[float] = None
    stop_loss: Optional[float] = None
    why: str
    # decision layer
    time_horizon: str = "swing"
    entry_timing: str = "EVALUATE"
    entry_price_zone: Optional[list[float]] = None  # [low, high]
    price_target_bear: Optional[float] = None
    price_target_bull: Optional[float] = None
    position_size_pct: Optional[float] = None
    position_max_pct: Optional[float] = None
    catalyst_event: Optional[str] = None
    catalyst_days: Optional[int] = None
    conflict_note: Optional[str] = None


class RadarStock(BaseModel):
    ticker: str
    name: Optional[str] = None
    domain: Optional[str] = None
    price: Optional[float] = None
    verdict: str
    composite: int
    confidence: int
    signals: dict[str, VerdictSignalDetail]
    why: str
    price_target: Optional[float] = None
    price_target_bear: Optional[float] = None
    price_target_bull: Optional[float] = None
    stop_loss: Optional[float] = None
    analyst_upside: Optional[float] = None
    risk_reward: Optional[float] = None
    ai_price_target: Optional[float] = None
    # decision layer
    entry_timing: str = "EVALUATE"
    entry_price_zone: Optional[list[float]] = None
    action_urgency: str = "WATCH"   # ACT_NOW | WATCH | REST
    catalyst_event: Optional[str] = None
    catalyst_days: Optional[int] = None
    conflict_note: Optional[str] = None
    position_size_pct: Optional[float] = None


class RadarResponse(BaseModel):
    mode: str
    stocks: list[RadarStock]
    total_scanned: int
    shortlist_count: int
    cached_at: Optional[float] = None
    scan_duration_seconds: Optional[float] = None
