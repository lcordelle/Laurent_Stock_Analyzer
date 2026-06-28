import { useState, useEffect, type FormEvent } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Loader2, TrendingUp, TrendingDown, Bookmark, BookmarkCheck } from 'lucide-react'
import { stockApi } from '../services/api'
import { addRecentTicker } from './Home'
import { addToWatchlist, removeFromWatchlist, isInWatchlist } from '../lib/watchlist'
import type { FullStockAnalysis } from '../lib/types'
import { fmt, scoreColor, changeColor } from '../lib/formatters'
import PageWrapper from '../components/layout/PageWrapper'
import CandlestickChart from '../components/charts/CandlestickChart'
import MetricsTable from '../components/stocks/MetricsTable'
import NewsPanel from '../components/stocks/NewsPanel'
import { AiResearch } from '../components/stocks/AiResearch'
import FactorGrades from '../components/stocks/FactorGrades'
import DividendScorecard from '../components/stocks/DividendScorecard'
import EarningsPanel from '../components/stocks/EarningsPanel'
import RiskProfile from '../components/stocks/RiskProfile'
import ScoreCard from '../components/stocks/ScoreCard'
import ScoreGauge from '../components/charts/ScoreGauge'
import AiAnalystReport from '../components/stocks/AiAnalystReport'

// ── Analyst price target range chart ─────────────────────────────────────────
function AnalystTargetChart({ rating, currentPrice }: {
  rating: NonNullable<FullStockAnalysis['analyst_rating']>
  currentPrice?: number
}) {
  const low  = rating.target_low
  const mean = rating.target_mean
  const high = rating.target_high
  const cur  = currentPrice
  if (!low || !high || !mean) return null

  const rangeMin = Math.min(low, cur ?? low) * 0.97
  const rangeMax = Math.max(high, cur ?? high) * 1.03
  const span = rangeMax - rangeMin
  const pct = (v: number) => ((v - rangeMin) / span) * 100

  const upsideMean = cur ? ((mean - cur) / cur * 100) : null
  const upsideHigh = cur ? ((high - cur) / cur * 100) : null
  const recColor = (r?: string | null) => {
    if (!r) return '#94a3b8'
    const u = r.toUpperCase()
    if (u.includes('BUY') || u.includes('OUTPERFORM') || u.includes('OVERWEIGHT')) return '#00e676'
    if (u.includes('SELL') || u.includes('UNDERPERFORM') || u.includes('UNDERWEIGHT')) return '#ff1744'
    return '#ffab00'
  }

  return (
    <div className="rounded-xl border p-5 flex flex-col gap-4"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <h3 className="text-xs font-semibold uppercase tracking-wide" style={{ color: '#475569' }}>
            Wall Street Analyst Consensus
          </h3>
          {rating.count && (
            <span className="text-xs px-2 py-0.5 rounded" style={{ backgroundColor: 'rgba(255,255,255,0.04)', color: '#475569' }}>
              {rating.count} analysts
            </span>
          )}
        </div>
        {rating.recommendation && (
          <span className="text-xs font-bold px-2.5 py-1 rounded-lg capitalize"
            style={{ color: recColor(rating.recommendation), backgroundColor: `${recColor(rating.recommendation)}15` }}>
            {rating.recommendation}
          </span>
        )}
      </div>

      {/* Price spectrum bar */}
      <div className="relative" style={{ height: 56 }}>
        {/* Track */}
        <div className="absolute rounded-full" style={{ top: 22, left: `${pct(low)}%`, right: `${100 - pct(high)}%`, height: 12, backgroundColor: 'rgba(255,255,255,0.06)' }} />
        {/* Filled range low→mean */}
        <div className="absolute rounded-l-full" style={{ top: 22, left: `${pct(low)}%`, width: `${pct(mean) - pct(low)}%`, height: 12, backgroundColor: 'rgba(0,230,118,0.25)' }} />
        {/* Filled range mean→high */}
        <div className="absolute rounded-r-full" style={{ top: 22, left: `${pct(mean)}%`, width: `${pct(high) - pct(mean)}%`, height: 12, backgroundColor: 'rgba(0,230,118,0.12)' }} />

        {/* Low marker */}
        <div className="absolute flex flex-col items-center" style={{ left: `${pct(low)}%`, transform: 'translateX(-50%)' }}>
          <span className="text-xs tabular-nums font-semibold" style={{ color: '#ff1744' }}>{fmt.price(low)}</span>
          <div style={{ width: 2, height: 12, backgroundColor: '#ff1744', marginTop: 1 }} />
          <span className="text-xs mt-1" style={{ color: '#475569' }}>Low</span>
        </div>

        {/* Mean marker */}
        <div className="absolute flex flex-col items-center" style={{ left: `${pct(mean)}%`, transform: 'translateX(-50%)' }}>
          <span className="text-xs tabular-nums font-bold" style={{ color: '#00e676' }}>{fmt.price(mean)}</span>
          <div style={{ width: 2, height: 12, backgroundColor: '#00e676', marginTop: 1 }} />
          <span className="text-xs mt-1" style={{ color: '#475569' }}>Target</span>
        </div>

        {/* High marker */}
        <div className="absolute flex flex-col items-center" style={{ left: `${pct(high)}%`, transform: 'translateX(-50%)' }}>
          <span className="text-xs tabular-nums font-semibold" style={{ color: '#00d4ff' }}>{fmt.price(high)}</span>
          <div style={{ width: 2, height: 12, backgroundColor: '#00d4ff', marginTop: 1 }} />
          <span className="text-xs mt-1" style={{ color: '#475569' }}>High</span>
        </div>

        {/* Current price marker */}
        {cur && (
          <div className="absolute flex flex-col items-center" style={{ left: `${pct(cur)}%`, transform: 'translateX(-50%)', zIndex: 10 }}>
            <span className="text-xs tabular-nums font-black" style={{ color: '#e2e8f0' }}>{fmt.price(cur)}</span>
            <div style={{ width: 3, height: 12, backgroundColor: '#e2e8f0', borderRadius: 2, marginTop: 1 }} />
            <span className="text-xs mt-1 font-semibold" style={{ color: '#e2e8f0' }}>Now</span>
          </div>
        )}
      </div>

      {/* Upside summary row */}
      {cur && (
        <div className="flex gap-4 flex-wrap pt-1 border-t" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
          <div>
            <div className="text-xs mb-0.5" style={{ color: '#475569' }}>To consensus target</div>
            <div className="text-sm font-bold tabular-nums" style={{ color: upsideMean! >= 0 ? '#00e676' : '#ff1744' }}>
              {upsideMean != null ? (upsideMean >= 0 ? '+' : '') + upsideMean.toFixed(1) + '%' : '—'}
            </div>
          </div>
          <div>
            <div className="text-xs mb-0.5" style={{ color: '#475569' }}>To bull case (high)</div>
            <div className="text-sm font-bold tabular-nums" style={{ color: upsideHigh! >= 0 ? '#00d4ff' : '#ff1744' }}>
              {upsideHigh != null ? (upsideHigh >= 0 ? '+' : '') + upsideHigh.toFixed(1) + '%' : '—'}
            </div>
          </div>
          {rating.mean && (
            <div>
              <div className="text-xs mb-0.5" style={{ color: '#475569' }}>Conviction score</div>
              <div className="text-sm font-bold tabular-nums" style={{ color: rating.mean <= 2 ? '#00e676' : rating.mean <= 2.5 ? '#ffab00' : '#ff1744' }}>
                {rating.mean.toFixed(2)} / 5.0
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Colour + conviction helpers ───────────────────────────────────────────────
function sigColor(s?: string | null) {
  if (!s) return '#94a3b8'
  if (s.includes('BUY')) return '#00e676'
  if (s.includes('SELL')) return '#ff1744'
  return '#ffab00'
}
function tierColor(tier: string) {
  if (tier === 'STRONG BUY') return '#00e676'
  if (tier === 'BUY')        return '#69f0ae'
  if (tier === 'WATCH')      return '#ffab00'
  return '#ff1744'
}
function computeTier(signal?: string | null, score?: number, confidence?: number): string {
  const s = (signal ?? '').toUpperCase()
  if (s.includes('SELL')) return 'AVOID'
  if (!s.includes('BUY')) return 'WATCH'
  const c = (score ?? 0) * 0.6 + (confidence ?? 0) * 0.4
  return c >= 75 ? 'STRONG BUY' : 'BUY'
}
function computeWhyNow(
  score: number, signal?: string | null, rsi?: number | null, macd?: string | null,
  momentum?: number | null, _roe?: number | null, gm?: number | null,
  rg?: number | null, upside?: number | null
): string {
  const sig = signal ?? ''; const r = rsi ?? 50
  if (score >= 80 && sig.includes('BUY'))  return 'Elite fundamentals aligned with bullish technicals — rare high-conviction setup'
  if (r < 35 && score >= 60)              return 'Technically oversold with strong fundamentals — asymmetric reversal opportunity'
  if (r < 45 && macd === 'BULLISH' && score >= 65) return 'Momentum turning bullish while still early in the move — ideal entry zone'
  if (momentum != null && momentum < 25 && score >= 70) return 'Near 52-week lows with premium fundamentals — deep value entry point'
  if (upside != null && upside > 20 && score >= 60) return `Analyst consensus implies ${upside.toFixed(0)}% upside — significant margin of safety`
  if (rg != null && rg > 25 && score >= 70) return `${rg.toFixed(0)}% revenue growth with high-quality fundamentals — growth at a reasonable price`
  if (sig.includes('STRONG BUY')) return 'Technical scoring at maximum bullish extreme — high-momentum entry'
  if (score >= 75 && sig.includes('HOLD')) return 'World-class business at fair value — accumulate on weakness'
  if (gm != null && gm > 60 && score >= 65) return `${gm.toFixed(0)}% gross margins signal structural pricing power — quality compounder`
  return 'Solid fundamentals with improving technical picture — monitor for entry'
}
function computeDrivers(
  components: Record<string, number>,
  gm?: number | null, roe?: number | null, rg?: number | null, pe?: number | null,
  rsi?: number | null, macd?: string | null, trend?: string | null,
  momentum?: number | null, upside?: number | null
): string[] {
  const d: string[] = []
  const gmPts = components['Gross Margin'] ?? 0
  if (gmPts === 25 && gm) d.push(`Gross margin ${gm.toFixed(0)}% — elite pricing power`)
  else if (gmPts >= 15 && gm) d.push(`Gross margin ${gm.toFixed(0)}% — above-average profitability`)
  const roePts = components['ROE'] ?? 0
  if (roePts === 20 && roe) d.push(`ROE ${roe.toFixed(0)}% — exceptional capital efficiency`)
  else if (roePts >= 15 && roe) d.push(`ROE ${roe.toFixed(0)}% — strong returns on equity`)
  if ((components['Valuation'] ?? 0) === 20 && pe) d.push(`P/E ${pe.toFixed(1)}x — attractive valuation`)
  if ((components['Growth'] ?? 0) >= 10 && rg) d.push(`Revenue growth +${rg.toFixed(0)}% — expanding top line`)
  if (rsi != null && rsi < 30) d.push(`RSI ${rsi.toFixed(0)} — technically oversold`)
  else if (rsi != null && rsi < 40) d.push(`RSI ${rsi.toFixed(0)} — approaching oversold`)
  if (macd === 'BULLISH' && (trend === 'UPTREND' || trend === 'STRONG UPTREND')) d.push('MACD bullish + uptrend confirmed')
  else if (macd === 'BULLISH') d.push('MACD crossover bullish')
  if (momentum != null && momentum < 25) d.push(`${momentum.toFixed(0)}% of 52w range — deep value entry`)
  else if (momentum != null && momentum > 80) d.push(`${momentum.toFixed(0)}% of 52w range — breakout momentum`)
  if (upside != null && upside > 25) d.push(`Analyst consensus +${upside.toFixed(0)}% upside`)
  else if (upside != null && upside > 15) d.push(`Analyst target +${upside.toFixed(0)}% upside`)
  return d.slice(0, 3)
}

// ── Price ladder ──────────────────────────────────────────────────────────────
function PriceLadder({ signals }: { signals: NonNullable<FullStockAnalysis['trading_signals']> }) {
  const { optimal_entry: entry, stop_loss: sl, tp1, tp2, tp3 } = signals
  if (!entry || !sl) return <p className="text-xs" style={{ color: '#475569' }}>No trade setup available</p>
  const levels = [
    tp3 != null && { label: 'TP3', price: tp3, pct: (tp3 - entry) / entry * 100, color: '#00e676',  bg: '#00e67614' },
    tp2 != null && { label: 'TP2', price: tp2, pct: (tp2 - entry) / entry * 100, color: '#4ade80',  bg: '#00e67610' },
    tp1 != null && { label: 'TP1', price: tp1, pct: (tp1 - entry) / entry * 100, color: '#86efac',  bg: '#00e6760a' },
    { label: 'Entry', price: entry, pct: 0, color: '#00d4ff', bg: '#00d4ff18', isEntry: true as const },
    { label: 'SL',    price: sl,    pct: (sl - entry) / entry * 100, color: '#ff1744', bg: '#ff174415' },
  ].filter(Boolean) as Array<{ label: string; price: number; pct: number; color: string; bg: string; isEntry?: true }>
  return (
    <div className="flex flex-col gap-1">
      {levels.map(({ label, price, pct, color, bg, isEntry }) => (
        <div key={label} className="flex items-center justify-between px-2.5 py-1.5 rounded-lg"
          style={{ backgroundColor: bg, border: `1px solid ${color}${isEntry ? '55' : '25'}` }}>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold w-8 shrink-0" style={{ color }}>{label}</span>
            <span className="text-sm font-bold tabular-nums font-mono" style={{ color: isEntry ? '#e2e8f0' : '#94a3b8' }}>
              {fmt.price(price)}
            </span>
          </div>
          <span className="text-xs font-semibold tabular-nums" style={{ color: pct === 0 ? '#475569' : color }}>
            {pct === 0 ? 'entry' : `${pct > 0 ? '+' : ''}${pct.toFixed(1)}%`}
          </span>
        </div>
      ))}
    </div>
  )
}

// ── Metrics strip (horizontal scroll) ────────────────────────────────────────
function MetricPill({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="flex flex-col items-center px-4 py-2.5 rounded-xl shrink-0"
      style={{ backgroundColor: '#111827', border: '1px solid rgba(255,255,255,0.06)', minWidth: 80 }}>
      <span className="text-xs font-semibold uppercase tracking-wide mb-1 whitespace-nowrap" style={{ color: '#475569' }}>{label}</span>
      <span className="text-sm font-black tabular-nums" style={{ color: color ?? '#e2e8f0' }}>{value}</span>
    </div>
  )
}
function MetricsStrip({ data }: { data: FullStockAnalysis }) {
  const m = data.metrics; const r = data.risk_profile
  const items: Array<{ label: string; value: string; color?: string }> = []
  if (m?.pe_ratio != null)       items.push({ label: 'P/E',       value: m.pe_ratio.toFixed(1) + 'x',  color: m.pe_ratio < 25 ? '#00e676' : m.pe_ratio < 40 ? '#ffab00' : '#ff1744' })
  if (m?.forward_pe != null)     items.push({ label: 'Fwd P/E',   value: m.forward_pe.toFixed(1) + 'x', color: m.forward_pe < 25 ? '#00e676' : m.forward_pe < 40 ? '#ffab00' : '#ff1744' })
  if (m?.roe != null)            items.push({ label: 'ROE',        value: m.roe.toFixed(1) + '%',        color: m.roe > 15 ? '#00e676' : m.roe > 0 ? '#ffab00' : '#ff1744' })
  if (m?.gross_margin != null)   items.push({ label: 'Grs Margin', value: m.gross_margin.toFixed(1) + '%', color: m.gross_margin > 40 ? '#00e676' : m.gross_margin > 20 ? '#ffab00' : '#ff1744' })
  if (m?.revenue_growth != null) items.push({ label: 'Rev Growth', value: (m.revenue_growth > 0 ? '+' : '') + m.revenue_growth.toFixed(1) + '%', color: changeColor(m.revenue_growth) })
  if (m?.earnings_growth != null) items.push({ label: 'EPS Growth', value: (m.earnings_growth > 0 ? '+' : '') + m.earnings_growth.toFixed(1) + '%', color: changeColor(m.earnings_growth) })
  if (m?.beta != null)           items.push({ label: 'Beta',       value: m.beta.toFixed(2),             color: m.beta < 1.2 ? '#00e676' : '#ffab00' })
  if (m?.market_cap != null)     items.push({ label: 'Mkt Cap',    value: fmt.mcap(m.market_cap) })
  if (r?.sharpe_ratio != null)   items.push({ label: 'Sharpe',     value: r.sharpe_ratio.toFixed(2),     color: r.sharpe_ratio > 1 ? '#00e676' : r.sharpe_ratio > 0 ? '#ffab00' : '#ff1744' })
  if (r?.var_5pct != null)       items.push({ label: 'VaR 5%',     value: r.var_5pct.toFixed(2) + '%',   color: r.var_5pct <= 2 ? '#00e676' : r.var_5pct <= 4 ? '#ffab00' : '#ff1744' })
  if (r?.max_drawdown_pct != null) items.push({ label: 'Max DD',   value: r.max_drawdown_pct.toFixed(1) + '%', color: r.max_drawdown_pct <= 15 ? '#00e676' : r.max_drawdown_pct <= 30 ? '#ffab00' : '#ff1744' })
  if (r?.volatility != null)     items.push({ label: 'Vol / yr',   value: r.volatility.toFixed(1) + '%', color: r.volatility <= 20 ? '#00e676' : r.volatility <= 35 ? '#ffab00' : '#ff1744' })
  if (m?.dividend_yield != null && m.dividend_yield > 0) items.push({ label: 'Div Yield', value: m.dividend_yield.toFixed(2) + '%', color: '#00d4ff' })
  if (items.length === 0) return null
  return (
    <div className="overflow-x-auto pb-1">
      <div className="flex gap-2" style={{ minWidth: 'max-content' }}>
        {items.map(({ label, value, color }) => (
          <MetricPill key={label} label={label} value={value} color={color} />
        ))}
      </div>
    </div>
  )
}

// ── Deep research tabs ────────────────────────────────────────────────────────
import EarningsPreview from '../components/stocks/EarningsPreview'
import CatalystCalendar from '../components/stocks/CatalystCalendar'
import ValuationTools from '../components/stocks/ValuationTools'
import VerdictBanner from '../components/stocks/VerdictBanner'

type Tab = 'fundamentals' | 'earnings' | 'news' | 'ai' | 'valuation' | 'catalysts'

function DeepTabs({ data, period: _period, onPeriodChange: _onPeriodChange }: {
  data: FullStockAnalysis; period: string; onPeriodChange: (p: string) => void
}) {
  const [tab, setTab] = useState<Tab>(() =>
    typeof window !== 'undefined' && window.location.hash === '#ai' ? 'ai' : 'fundamentals'
  )
  const tabs: Array<{ id: Tab; label: string }> = [
    { id: 'fundamentals', label: 'Fundamentals' },
    { id: 'earnings',     label: 'Earnings' },
    { id: 'valuation',    label: 'Valuation' },
    { id: 'catalysts',    label: 'Catalysts' },
    { id: 'news',         label: 'News & Analyst' },
    { id: 'ai',           label: 'AI Research' },
  ]

  return (
    <div className="rounded-xl border overflow-hidden" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
      <div className="flex border-b overflow-x-auto" style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className="px-5 py-3 text-xs font-semibold uppercase tracking-wide whitespace-nowrap transition-colors shrink-0"
            style={{
              color: tab === t.id ? '#00d4ff' : '#475569',
              borderBottom: `2px solid ${tab === t.id ? '#00d4ff' : 'transparent'}`,
              backgroundColor: 'transparent',
            }}>
            {t.label}
          </button>
        ))}
      </div>
      <div className="p-5 flex flex-col gap-5" style={{ backgroundColor: '#0d1117' }}>
        {tab === 'fundamentals' && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {data.score && <ScoreCard score={data.score} />}
              {data.score && <ScoreGauge score={data.score.total} />}
            </div>
            {data.metrics && <MetricsTable metrics={data.metrics} shortInterest={data.short_interest} />}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FactorGrades ticker={data.ticker} sector={data.sector ?? ''} />
              <DividendScorecard ticker={data.ticker} sector={data.sector ?? ''} />
            </div>
            {data.risk_profile && <RiskProfile riskProfile={data.risk_profile} ticker={data.ticker} />}
          </>
        )}
        {tab === 'earnings' && (
          <>
            <EarningsPanel ticker={data.ticker} />
            <EarningsPreview data={data} />
          </>
        )}
        {tab === 'valuation' && <ValuationTools data={data} />}
        {tab === 'catalysts' && <CatalystCalendar data={data} />}
        {tab === 'news' && (
          <>
            <NewsPanel articles={data.news} />
            {data.analyst_rating && (
              <AnalystTargetChart
                rating={data.analyst_rating}
                currentPrice={data.metrics?.current_price ?? data.ohlcv.at(-1)?.close}
              />
            )}
            {data.forecast && (
              <div className="rounded-xl border p-5" style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
                <h3 className="text-xs font-semibold uppercase tracking-wide mb-3" style={{ color: '#475569' }}>Statistical Forecast</h3>
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-xl font-bold" style={{ color: '#e2e8f0' }}>{fmt.price(data.forecast.forecast_price)}</span>
                  {data.forecast.forecast_change_pct != null && (
                    <span className="flex items-center gap-0.5 text-sm font-semibold" style={{ color: changeColor(data.forecast.forecast_change_pct) }}>
                      {data.forecast.forecast_change_pct >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                      {(Math.abs(data.forecast.forecast_change_pct)).toFixed(2)}%
                    </span>
                  )}
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  {[
                    { label: 'Type', value: data.forecast.forecast_type },
                    { label: 'Fundamental Confidence', value: data.forecast.probability != null ? data.forecast.probability.toFixed(1) + '%' : '—' },
                    { label: 'Momentum', value: data.forecast.momentum != null ? (data.forecast.momentum >= 0 ? '+' : '') + data.forecast.momentum.toFixed(2) + '%' : '—' },
                    { label: 'Trend', value: data.forecast.trend },
                  ].map(({ label, value }) => (
                    <div key={label} className="rounded-lg p-2.5" style={{ backgroundColor: '#0a0e1a' }}>
                      <div className="mb-0.5" style={{ color: '#475569' }}>{label}</div>
                      <div className="font-semibold capitalize" style={{ color: '#e2e8f0' }}>{value}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
        {tab === 'ai' && (
          <>
            <AiAnalystReport ticker={data.ticker} data={data} />
            <AiResearch ticker={data.ticker} data={data} />
          </>
        )}
      </div>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function Analysis() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [inputTicker, setInputTicker] = useState(searchParams.get('ticker') ?? '')
  const [period, setPeriod] = useState('1y')
  const [watchlisted, setWatchlisted] = useState(false)
  const ticker = searchParams.get('ticker') ?? ''

  const { data, isLoading, isError, error } = useQuery<FullStockAnalysis>({
    queryKey: ['analysis', ticker, period],
    queryFn: () => stockApi.analyze(ticker, period),
    enabled: !!ticker,
    staleTime: 5 * 60_000,
    retry: 1,
  })

  useEffect(() => {
    if (data && !data.error && data.ticker) {
      addRecentTicker(data.ticker)
      setWatchlisted(isInWatchlist(data.ticker))
    }
  }, [data])

  useEffect(() => { setWatchlisted(isInWatchlist(ticker)) }, [ticker])

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const t = inputTicker.trim().toUpperCase()
    if (t) setSearchParams({ ticker: t })
  }

  // ── Derived values ──────────────────────────────────────────────────────────
  const met = data?.metrics
  const sig = data?.trading_signals
  const rat = data?.analyst_rating
  const rsk = data?.risk_profile
  const sco = data?.score
  const fct = data?.forecast

  const currentPrice  = met?.current_price
  const prevClose     = data?.ohlcv?.[data.ohlcv.length - 2]?.close
  const priceChange   = currentPrice && prevClose ? currentPrice - prevClose : undefined
  const pricePct      = priceChange && prevClose ? (priceChange / prevClose) * 100 : undefined
  const signal        = sig?.signal
  const sc            = sigColor(signal)

  const momentum52 = (met?.fifty_two_week_high != null && met?.fifty_two_week_low != null &&
                      currentPrice != null && (met.fifty_two_week_high - met.fifty_two_week_low) > 0)
    ? Math.round((currentPrice - met.fifty_two_week_low) / (met.fifty_two_week_high - met.fifty_two_week_low) * 100)
    : null

  const analystUpside = (rat?.target_mean && currentPrice && currentPrice > 0)
    ? (rat.target_mean - currentPrice) / currentPrice * 100
    : null

  const tier    = computeTier(signal, sco?.total, sig?.confidence)
  const whyNow  = computeWhyNow(sco?.total ?? 0, signal, sig?.rsi_value, sig?.macd_signal,
                    momentum52, met?.roe, met?.gross_margin, met?.revenue_growth, analystUpside)
  const drivers = computeDrivers(sco?.components ?? {}, met?.gross_margin, met?.roe,
                    met?.revenue_growth, met?.pe_ratio, sig?.rsi_value, sig?.macd_signal,
                    sig?.trend_strength, momentum52, analystUpside)

  const recentNewsCount = (data?.news ?? []).filter(n => {
    if (!n.published) return false
    const d = new Date(n.published)
    return !isNaN(d.getTime()) && (Date.now() - d.getTime()) < 7 * 86400 * 1000
  }).length
  const suggestedPosition = rsk?.volatility != null
    ? (rsk.volatility > 50 ? 1 : rsk.volatility > 35 ? 2 : rsk.volatility > 25 ? 3 : 5)
    : null

  return (
    <PageWrapper>
      <div className="flex flex-col gap-4">

        {/* ── Command bar ──────────────────────────────────────────────────── */}
        <div className="flex flex-wrap items-center gap-3">
          <form onSubmit={handleSubmit} className="flex gap-2 shrink-0" data-testid="analysis-form">
            <input
              type="text"
              value={inputTicker}
              onChange={e => setInputTicker(e.target.value.toUpperCase())}
              placeholder="Ticker…"
              className="w-32 px-3 py-2 rounded-xl text-sm font-mono outline-none"
              style={{ backgroundColor: '#111827', border: '1px solid rgba(255,255,255,0.08)', color: '#e2e8f0' }}
              data-testid="ticker-input"
            />
            <button type="submit" className="px-4 py-2 rounded-xl text-sm font-semibold"
              style={{ background: 'linear-gradient(135deg, #00d4ff, #0088cc)', color: '#0a0e1a' }}
              data-testid="analyze-btn">
              Analyze
            </button>
          </form>

          {data && !data.error && (
            <>
              <span className="px-2.5 py-1 rounded-lg text-sm font-black font-mono tracking-wider"
                style={{ backgroundColor: `${sc}20`, color: sc }}>
                {data.ticker}
              </span>
              <div>
                <div className="text-sm font-bold leading-tight" style={{ color: '#e2e8f0' }}>{data.company_name ?? data.ticker}</div>
                <div className="flex items-center gap-2">
                  {data.sector && <span className="text-xs" style={{ color: '#475569' }}>{data.sector}{data.industry ? ` · ${data.industry}` : ''}</span>}
                  {data.data_source && (
                    <span className="text-xs px-1.5 py-0.5 rounded font-medium"
                      style={{ backgroundColor: 'rgba(99,102,241,0.12)', color: '#818cf8', border: '1px solid rgba(99,102,241,0.2)' }}>
                      {data.data_source}
                    </span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3 ml-auto">
                {currentPrice && (
                  <>
                    <span className="text-2xl font-black tabular-nums" style={{ color: '#e2e8f0' }}>{fmt.price(currentPrice)}</span>
                    {pricePct != null && (
                      <span className="flex items-center gap-0.5 text-sm font-semibold" style={{ color: changeColor(pricePct) }}>
                        {pricePct >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                        {(pricePct >= 0 ? '+' : '') + pricePct.toFixed(2) + '%'}
                      </span>
                    )}
                  </>
                )}
                {data.is_stale && (
                  <div
                    title={data.cached_at ? `Live data unavailable (Alpha Vantage limit reached). Showing cached data from ${new Date(data.cached_at + 'Z').toLocaleString()}.` : 'Live data unavailable. Showing cached data.'}
                    className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold cursor-help"
                    style={{ backgroundColor: 'rgba(234,179,8,0.12)', color: '#fbbf24', border: '1px solid rgba(234,179,8,0.25)' }}
                  >
                    <svg className="w-3.5 h-3.5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                    </svg>
                    Cached{data.cached_at && ` · ${new Date(data.cached_at + 'Z').toLocaleDateString()}`}
                  </div>
                )}
                {ticker && (
                  <button
                    onClick={() => {
                      if (watchlisted) { removeFromWatchlist(ticker); setWatchlisted(false) }
                      else { addToWatchlist(ticker); setWatchlisted(true) }
                    }}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
                    style={{
                      color: watchlisted ? '#00d4ff' : '#94a3b8',
                      backgroundColor: watchlisted ? 'rgba(0,212,255,0.1)' : '#1a2235',
                      border: `1px solid ${watchlisted ? 'rgba(0,212,255,0.3)' : 'rgba(255,255,255,0.06)'}`,
                    }}
                  >
                    {watchlisted ? <BookmarkCheck className="w-4 h-4" /> : <Bookmark className="w-4 h-4" />}
                    {watchlisted ? 'In Watchlist' : 'Add to Watchlist'}
                  </button>
                )}
              </div>
            </>
          )}
        </div>

        {/* ── Quick actions ────────────────────────────────────────────────── */}
        {data && !data.error && ticker && (
          <div className="flex gap-2 flex-wrap">
            <Link
              to={`/alerts?ticker=${ticker}`}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-opacity hover:opacity-80"
              style={{ backgroundColor: '#ffab0015', border: '1px solid rgba(255,171,0,0.25)', color: '#ffab00' }}
            >
              🔔 Set Alert
            </Link>
          </div>
        )}

        {/* ── Empty / loading / error states ────────────────────────────────── */}
        {!ticker && (
          <div className="rounded-xl border p-12 flex items-center justify-center"
            style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
            <p className="text-sm" style={{ color: '#475569' }}>Enter a ticker symbol above to begin analysis</p>
          </div>
        )}
        {isLoading && (
          <div className="rounded-xl border p-12 flex flex-col items-center gap-3"
            style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }} data-testid="loading-state">
            <Loader2 className="w-8 h-8 animate-spin" style={{ color: '#00d4ff' }} />
            <p className="text-sm" style={{ color: '#94a3b8' }}>Analyzing {ticker}…</p>
          </div>
        )}
        {isError && (
          <div className="rounded-xl border p-5" style={{ backgroundColor: 'rgba(255,23,68,0.05)', borderColor: 'rgba(255,23,68,0.2)' }}
            role="alert" data-testid="error-state">
            <p className="text-sm font-semibold" style={{ color: '#ff1744' }}>Analysis failed</p>
            <p className="text-xs mt-1" style={{ color: '#94a3b8' }}>{(error as Error)?.message ?? 'Check the ticker and try again.'}</p>
          </div>
        )}

        {data && !data.error && (
          <div className="flex flex-col gap-4">

            {/* ── Verdict banner ─────────────────────────────────────────────── */}
            {ticker && <VerdictBanner ticker={ticker} period={period} />}

            {/* ── Company description ────────────────────────────────────────── */}
            {data.description && (
              <div className="px-3 py-2 rounded-xl border"
                style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
                <p className="text-xs leading-relaxed line-clamp-3" style={{ color: '#94a3b8' }}>
                  {data.description}
                </p>
              </div>
            )}

            {/* ── Decision cockpit: verdict sidebar + chart ──────────────────── */}
            <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-4" data-testid="stock-header">

              {/* Left: Verdict & trade panel */}
              <div className="flex flex-col gap-3">

                {/* Verdict card */}
                <div className="rounded-xl border p-4 flex flex-col gap-3"
                  style={{ backgroundColor: '#111827', borderColor: `${sc}25` }}>

                  <div className="flex items-start justify-between">
                    <div>
                      <div className="text-xs uppercase tracking-widest mb-0.5" style={{ color: '#475569' }}>Tech Signal</div>
                      <div className="text-2xl font-black tracking-tight" style={{ color: sc }}>{signal ?? '—'}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-3xl font-black" style={{ color: scoreColor(sco?.total ?? 0) }}>{sco?.total ?? '—'}</div>
                      <div className="text-xs" style={{ color: '#475569' }}>VF Score</div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-bold px-2.5 py-1 rounded-lg"
                      style={{ backgroundColor: `${tierColor(tier)}20`, color: tierColor(tier) }}>{tier}</span>
                    {sig?.signal_quality && (() => {
                      const qc = sig.signal_quality === 'PRIME' ? '#ffd700' : sig.signal_quality === 'CONFIRMED' ? '#00e676' : sig.signal_quality === 'STANDARD' ? '#ffab00' : '#475569'
                      return <span className="text-xs font-bold px-2 py-0.5 rounded" style={{ backgroundColor: `${qc}15`, color: qc }}>
                        {sig.signal_quality}
                        {sig.signal_quality === 'PRIME' ? ' ★' : ''}
                      </span>
                    })()}
                    {sig?.earnings_proximity && (
                      <span className="text-xs font-semibold px-2 py-0.5 rounded" style={{ backgroundColor: '#ff174415', color: '#ff1744' }}>
                        ⚠ EARNINGS {sig.earnings_proximity}
                      </span>
                    )}
                    {sig?.confidence != null && (
                      <div className="flex items-center gap-1.5 flex-1">
                        <div className="flex-1 bg-white/10 rounded-full h-1.5">
                          <div className="h-1.5 rounded-full" style={{ width: `${sig.confidence}%`, background: `linear-gradient(90deg, ${sc}80, ${sc})` }} />
                        </div>
                        <span className="text-xs font-bold tabular-nums w-8 text-right" style={{ color: '#94a3b8' }}>{sig.confidence}%</span>
                      </div>
                    )}
                  </div>

                  {fct && (
                    <div className="flex items-center justify-between text-xs px-2.5 py-2 rounded-lg"
                      style={{ backgroundColor: '#0a0e1a' }}>
                      <span style={{ color: '#475569' }}>AI Forecast</span>
                      <span className="font-bold" style={{ color: changeColor(fct.forecast_change_pct) }}>
                        {fmt.price(fct.forecast_price)}{fct.forecast_change_pct != null && ` (${fct.forecast_change_pct >= 0 ? '+' : ''}${fct.forecast_change_pct.toFixed(1)}%)`}
                      </span>
                    </div>
                  )}

                  <div className="rounded-lg px-3 py-2 text-xs leading-relaxed"
                    style={{ backgroundColor: '#0a0e1a', color: '#94a3b8', borderLeft: `2px solid ${sc}` }}>
                    {whyNow}
                  </div>

                  {drivers.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {drivers.map((d, i) => (
                        <span key={i} className="text-xs px-2 py-0.5 rounded-full"
                          style={{ backgroundColor: '#00d4ff10', color: '#94a3b8', border: '1px solid rgba(0,212,255,0.12)' }}>
                          {d}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Trade setup */}
                {sig && (sig.optimal_entry != null || sig.stop_loss != null) && (
                  <div className="rounded-xl border p-4 flex flex-col gap-3"
                    style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
                    <div className="flex items-center justify-between">
                      <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: '#475569' }}>Trade Setup</p>
                      {sig.risk_reward != null && (
                        <span className="text-sm font-black" style={{ color: sig.risk_reward >= 2 ? '#00e676' : '#ffab00' }}>
                          R:R {sig.risk_reward.toFixed(1)}:1
                        </span>
                      )}
                    </div>
                    <PriceLadder signals={sig} />
                    {suggestedPosition != null && (
                      <div className="flex items-center justify-between text-xs pt-2 border-t" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
                        <span style={{ color: '#475569' }}>Max position</span>
                        <span style={{ color: '#94a3b8' }}>
                          {suggestedPosition}% portfolio
                          {rsk?.volatility != null && <span style={{ color: '#334155' }}> · vol {rsk.volatility.toFixed(0)}%</span>}
                        </span>
                      </div>
                    )}
                  </div>
                )}

                {/* Market context */}
                <div className="rounded-xl border p-4 flex flex-col gap-1.5"
                  style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
                  <p className="text-xs font-semibold uppercase tracking-wide mb-1" style={{ color: '#475569' }}>Context</p>

                  {rat?.target_mean != null && (
                    <div className="flex items-center justify-between text-xs">
                      <span style={{ color: '#475569' }}>Analyst target</span>
                      <div className="text-right">
                        <span className="font-bold" style={{ color: analystUpside != null ? changeColor(analystUpside) : '#e2e8f0' }}>
                          {fmt.price(rat.target_mean)}
                          {analystUpside != null && <> ({analystUpside >= 0 ? '+' : ''}{analystUpside.toFixed(1)}%)</>}
                        </span>
                        {data.analyst_target_age_days != null && (
                          <div style={{ color: data.analyst_target_age_days > 90 ? '#ff5252' : '#475569' }}>
                            {data.analyst_target_age_days}d old{data.analyst_target_age_days > 90 ? ' ⚠' : ''}
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {rat?.recommendation && (
                    <div className="flex items-center justify-between text-xs">
                      <span style={{ color: '#475569' }}>Consensus</span>
                      <span className="font-semibold capitalize" style={{ color: '#e2e8f0' }}>
                        {rat.recommendation}{rat.count != null ? ` (${rat.count})` : ''}
                      </span>
                    </div>
                  )}

                  {momentum52 != null && (
                    <div className="flex items-center justify-between text-xs">
                      <span style={{ color: '#475569' }}>52-wk position</span>
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-white/10 rounded-full h-1.5">
                          <div className="h-1.5 rounded-full" style={{ width: `${momentum52}%`, backgroundColor: momentum52 < 30 ? '#ff1744' : momentum52 > 70 ? '#00e676' : '#ffab00' }} />
                        </div>
                        <span className="tabular-nums" style={{ color: momentum52 < 30 ? '#ff1744' : momentum52 > 70 ? '#00e676' : '#ffab00' }}>{momentum52}%</span>
                      </div>
                    </div>
                  )}

                  <div className="flex items-center justify-between text-xs">
                    <span style={{ color: '#475569' }}>Recent news (7d)</span>
                    {recentNewsCount > 0
                      ? <span style={{ color: '#00e676' }}>✓ {recentNewsCount} article{recentNewsCount !== 1 ? 's' : ''}</span>
                      : <span style={{ color: '#ffab00' }}>⚠ None — verify catalyst</span>
                    }
                  </div>

                  {sig?.rsi_value != null && (
                    <div className="flex flex-col gap-0.5">
                      <div className="flex items-center justify-between text-xs">
                        <span style={{ color: '#475569' }}>RSI (14)</span>
                        <span className="font-bold tabular-nums"
                          style={{ color: sig.rsi_value <= (sig.rsi_reversal_zone_low ?? 30) ? '#00e676' : sig.rsi_value >= (sig.rsi_reversal_zone_high ?? 70) ? '#ff1744' : '#ffab00' }}>
                          {sig.rsi_value.toFixed(1)} · {sig.rsi_signal ?? '—'}
                        </span>
                      </div>
                      {sig.rsi_reversal_zone_low != null && (
                        <div className="flex items-center justify-between text-xs">
                          <span style={{ color: '#334155' }}>Historical zones</span>
                          <span style={{ color: '#475569' }}>
                            <span style={{ color: '#00e676' }}>{sig.rsi_reversal_zone_low}</span>
                            {' — '}
                            <span style={{ color: '#ff1744' }}>{sig.rsi_reversal_zone_high}</span>
                            <span style={{ color: '#334155' }}> ({sig.rsi_bullish_reversals}↑ {sig.rsi_bearish_reversals}↓)</span>
                          </span>
                        </div>
                      )}
                      {sig.rsi_reversal_signal && (
                        <div className="flex justify-end">
                          <span className="text-xs font-semibold px-2 py-0.5 rounded" style={{
                            color: sig.rsi_reversal_signal.includes('OVERSOLD') || sig.rsi_reversal_signal.includes('SUPPORT') ? '#00e676' : '#ff1744',
                            backgroundColor: sig.rsi_reversal_signal.includes('OVERSOLD') || sig.rsi_reversal_signal.includes('SUPPORT') ? '#00e67615' : '#ff174415',
                          }}>
                            {sig.rsi_reversal_signal}
                          </span>
                        </div>
                      )}
                    </div>
                  )}

                  {sig?.macd_signal && (
                    <div className="flex items-center justify-between text-xs">
                      <span style={{ color: '#475569' }}>MACD</span>
                      <span className="font-bold" style={{ color: sig.macd_signal === 'BULLISH' ? '#00e676' : sig.macd_signal === 'BEARISH' ? '#ff1744' : '#ffab00' }}>
                        {sig.macd_signal}
                      </span>
                    </div>
                  )}

                  {sig?.trend_strength && (
                    <div className="flex items-center justify-between text-xs">
                      <span style={{ color: '#475569' }}>Trend</span>
                      <span className="font-bold" style={{ color: sig.trend_strength.includes('UP') ? '#00e676' : sig.trend_strength.includes('DOWN') ? '#ff1744' : '#ffab00' }}>
                        {sig.trend_strength}
                      </span>
                    </div>
                  )}

                  {sig?.adx != null && (
                    <div className="flex items-center justify-between text-xs">
                      <span style={{ color: '#475569' }}>ADX (trend strength)</span>
                      <span className="font-bold" style={{ color: sig.adx > 40 ? '#00e676' : sig.adx > 25 ? '#ffab00' : '#ff1744' }}>
                        {sig.adx.toFixed(1)} · {sig.adx < 20 ? 'RANGING' : sig.adx < 25 ? 'WEAK TREND' : sig.adx < 40 ? 'TRENDING' : 'STRONG TREND'}
                      </span>
                    </div>
                  )}

                  {sig?.weekly_rsi != null && (
                    <div className="flex items-center justify-between text-xs">
                      <span style={{ color: '#475569' }}>Weekly RSI</span>
                      <span className="font-bold tabular-nums" style={{ color: sig.weekly_rsi < 40 ? '#00e676' : sig.weekly_rsi > 60 ? '#ff1744' : '#ffab00' }}>
                        {sig.weekly_rsi.toFixed(1)} · {sig.weekly_rsi < 40 ? 'OVERSOLD' : sig.weekly_rsi > 60 ? 'OVERBOUGHT' : 'NEUTRAL'}
                      </span>
                    </div>
                  )}

                  {(sig?.sr_nearest_support != null || sig?.sr_nearest_resistance != null) && (
                    <div className="flex items-center justify-between text-xs">
                      <span style={{ color: '#475569' }}>S/R levels</span>
                      <span className="tabular-nums" style={{ color: '#475569' }}>
                        {sig.sr_nearest_support != null && <span style={{ color: sig.sr_at_support ? '#00e676' : '#475569' }}>S {sig.sr_nearest_support.toFixed(2)}</span>}
                        {sig.sr_nearest_support != null && sig.sr_nearest_resistance != null && <span style={{ color: '#334155' }}> · </span>}
                        {sig.sr_nearest_resistance != null && <span style={{ color: sig.sr_at_resistance ? '#ff1744' : '#475569' }}>R {sig.sr_nearest_resistance.toFixed(2)}</span>}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Right: Chart (dominant) */}
              <div>
                {data.ohlcv.length > 0 && (
                  <CandlestickChart
                    ohlcv={data.ohlcv}
                    indicators={data.indicators}
                    valuationTunnel={data.valuation_tunnel}
                    tradingSignals={data.trading_signals}
                    earningsDates={data.earnings_dates}
                    relativeStrength={data.relative_strength}
                    period={period}
                    onPeriodChange={setPeriod}
                  />
                )}
              </div>
            </div>

            {/* ── Metrics strip ──────────────────────────────────────────────── */}
            <MetricsStrip data={data} />

            {/* ── Analyst price target range ─────────────────────────────────── */}
            {data.analyst_rating && (
              <AnalystTargetChart
                rating={data.analyst_rating}
                currentPrice={data.metrics?.current_price ?? data.ohlcv.at(-1)?.close}
              />
            )}

            {/* ── Deep research tabs ─────────────────────────────────────────── */}
            <DeepTabs data={data} period={period} onPeriodChange={setPeriod} />
          </div>
        )}

        {data?.error && (
          <div className="rounded-xl border p-5" style={{ backgroundColor: 'rgba(255,23,68,0.05)', borderColor: 'rgba(255,23,68,0.2)' }} role="alert">
            <p className="text-sm" style={{ color: '#ff1744' }}>{data.error}</p>
          </div>
        )}
      </div>
    </PageWrapper>
  )
}
