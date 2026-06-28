export interface OHLCVRow {
  date: string
  open: number; high: number; low: number; close: number; volume: number
}

export interface ScoreBreakdown {
  total: number
  components: Record<string, number>
}

export interface StockMetrics {
  current_price?: number; pe_ratio?: number; forward_pe?: number
  peg_ratio?: number; price_to_book?: number; dividend_yield?: number
  market_cap?: number; gross_margin?: number; operating_margin?: number
  profit_margin?: number; roe?: number; roa?: number
  revenue_growth?: number; earnings_growth?: number; debt_to_equity?: number
  current_ratio?: number; quick_ratio?: number; beta?: number
  target_price?: number; analyst_rating?: string; number_of_analysts?: number
  recommendation_mean?: number; volume?: number; average_volume?: number
  fifty_two_week_high?: number; fifty_two_week_low?: number
}

export interface ForecastResult {
  current_price: number; forecast_price: number
  forecast_change_pct: number; forecast_type: string
  probability: number; momentum: number; volatility: number; trend: string
}

export interface IndicatorData {
  sma_20: (number|null)[]; sma_50: (number|null)[]; sma_200: (number|null)[]
  rsi: (number|null)[]; macd: (number|null)[]; macd_signal: (number|null)[]
  bb_upper: (number|null)[]; bb_lower: (number|null)[]
  obv?: (number|null)[]; vwap?: (number|null)[]
}

export interface ValuationTunnel {
  hist_mid: (number|null)[]; hist_upper: (number|null)[]; hist_lower: (number|null)[]
  future_dates: string[]
  fc_mid: number[]; fc_upper: number[]; fc_lower: number[]
  horizon_days: number; k: number; drift_annual: number; sigma_annual: number
}

export interface DecisionFactor {
  label: string; subscore: number | null; weight: number
  contribution: number | null; detail: string
}
export interface Decision {
  conviction: number
  direction: 'Long' | 'Short' | 'Stand aside'
  factors: DecisionFactor[]
  regime: { label: string; vix: number | null; multiplier: number }
  expected_value_r: number | null
  rationale: string
}

export interface Calibration {
  available: boolean
  as_of?: string | null
  horizon_days?: number | null
  n?: number | null
  bucket_label?: string | null
  hit_rate?: number | null
  avg_forward_return?: number | null
  low_sample?: boolean | null
  proxy_conviction?: number | null
  note?: string | null
}

export interface RiskProfile {
  volatility?: number
  var_5pct?: number
  sharpe_ratio?: number
  sortino_ratio?: number
  max_drawdown_pct?: number
}

export interface NewsArticle {
  title: string; summary?: string; url?: string
  published?: string; sentiment?: string
}

export interface AnalystRating {
  recommendation?: string; mean?: number; count?: number
  target_high?: number; target_low?: number; target_mean?: number
}

export interface PeerData {
  ticker: string; score?: number; price?: number
  pe_ratio?: number; gross_margin?: number
}

export interface ShortInterestData {
  short_ratio?: number | null
  short_pct_float?: number | null
  shares_short?: number | null
  insider_own_pct?: number | null
  institution_own_pct?: number | null
}

export interface EarningsDate {
  date: string
  eps_estimate?: number | null
  eps_actual?: number | null
  surprise_pct?: number | null
  beat?: boolean | null
}

export interface FullStockAnalysis {
  ticker: string; company_name?: string; sector?: string
  industry?: string; description?: string
  ohlcv: OHLCVRow[]; metrics?: StockMetrics; score?: ScoreBreakdown
  forecast?: ForecastResult; indicators?: IndicatorData
  valuation_tunnel?: ValuationTunnel
  decision?: Decision
  calibration?: Calibration
  trading_signals?: {
    signal?: string; confidence?: number
    optimal_entry?: number; stop_loss?: number
    tp1?: number; tp2?: number; tp3?: number
    rsi_value?: number; rsi_signal?: string
    macd_signal?: string; trend_strength?: string; risk_reward?: number
    rsi_reversal_zone_low?: number; rsi_reversal_zone_high?: number
    rsi_bullish_reversals?: number; rsi_bearish_reversals?: number
    rsi_at_reversal_zone?: boolean; rsi_reversal_signal?: string
    adx?: number; weekly_rsi?: number
    sr_nearest_support?: number; sr_nearest_resistance?: number
    sr_at_support?: boolean; sr_at_resistance?: boolean
    earnings_proximity?: string; signal_quality?: string
  }
  risk_profile?: RiskProfile
  news: NewsArticle[]; analyst_rating?: AnalystRating; peers: PeerData[]
  short_interest?: ShortInterestData | null
  earnings_dates?: EarningsDate[]
  relative_strength?: (number | null)[]
  analyst_target_age_days?: number
  error?: string
  data_source?: string
  cached_at?: string
  is_stale?: boolean
}

export interface BatchAnalysisResponse {
  results: FullStockAnalysis[]; total: number; failed: string[]
}

export interface GradeItem {
  grade: string; percentile?: number; tooltip?: string
}

export interface FactorGradesResponse {
  ticker: string; sector: string; n_peers: number
  grades: { value: GradeItem; growth: GradeItem; profitability: GradeItem; momentum: GradeItem; eps_revisions: GradeItem }
}

export interface DividendGradeSet {
  safety: GradeItem; growth: GradeItem; yield_grade: GradeItem; consistency: GradeItem
}

export interface DividendScorecardResponse {
  ticker: string; pays_dividend: boolean
  current_yield?: number; annual_rate?: number
  grades?: DividendGradeSet
}

export interface EpsHistoryItem {
  date: string; eps_actual?: number; eps_estimate?: number
  surprise_pct?: number; beat?: boolean
}

export interface EarningsAnalysisResponse {
  ticker: string; data_available: boolean
  eps_history: EpsHistoryItem[]
  beat_rate_4q?: number; avg_surprise_pct_4q?: number; next_earnings_date?: string
}

export interface AiAnalystSections {
  executive_summary?: string; bulls_say: string[]; bears_say: string[]
  key_risks?: string; investment_thesis?: string
}

export interface AiAnalystReportResponse {
  ticker: string; provider?: string; model_name?: string
  sections: AiAnalystSections; error?: string
}

export interface VerdictSignalDetail {
  label: string
  score: number
  weight: number
}

export interface VerdictResponse {
  verdict: string
  confidence: number
  vf_score: number
  signals: {
    technical: VerdictSignalDetail
    fundamental: VerdictSignalDetail
    ai_outlook: VerdictSignalDetail
    analyst: VerdictSignalDetail
    momentum: VerdictSignalDetail
    news_sentiment: VerdictSignalDetail
    earnings_quality: VerdictSignalDetail
    risk: VerdictSignalDetail
  }
  price_target?: number
  stop_loss?: number
  why: string
  time_horizon: string
  entry_timing: string
  entry_price_zone?: [number, number]
  price_target_bear?: number
  price_target_bull?: number
  position_size_pct?: number
  position_max_pct?: number
  catalyst_event?: string
  catalyst_days?: number
  conflict_note?: string
}

export interface RadarStock {
  ticker: string
  name?: string
  domain?: string
  price?: number
  verdict: string
  composite: number
  confidence: number
  signals: {
    technical: VerdictSignalDetail
    fundamental: VerdictSignalDetail
    ai_outlook: VerdictSignalDetail
    analyst: VerdictSignalDetail
    momentum: VerdictSignalDetail
    news_sentiment: VerdictSignalDetail
    earnings_quality: VerdictSignalDetail
    risk: VerdictSignalDetail
  }
  why: string
  price_target?: number
  price_target_bear?: number
  price_target_bull?: number
  stop_loss?: number
  analyst_upside?: number
  risk_reward?: number
  ai_price_target?: number
  entry_timing: string
  entry_price_zone?: [number, number]
  action_urgency: string
  catalyst_event?: string
  catalyst_days?: number
  conflict_note?: string
  position_size_pct?: number
}

export interface RadarResponse {
  mode: string
  stocks: RadarStock[]
  total_scanned: number
  shortlist_count: number
  cached_at?: number
  scan_duration_seconds?: number
}
