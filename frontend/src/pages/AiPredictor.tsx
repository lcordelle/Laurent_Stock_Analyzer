import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Loader2, TrendingUp, TrendingDown, Minus, AlertTriangle } from 'lucide-react'
import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer } from 'recharts'
import { aiPredictorApi } from '../services/api'
import { fmt } from '../lib/formatters'
import PageWrapper from '../components/layout/PageWrapper'

interface SignalDetail {
  raw_score: number
  signal: 'bullish' | 'bearish' | 'neutral'
  value: number
  weight: number
}

interface PriceTargets {
  current: number
  conservative: number
  base: number
  aggressive: number
}

interface AIPrediction {
  ticker: string
  company_name?: string
  direction: 'BULL' | 'BEAR' | 'NEUTRAL'
  confidence: number
  bull_score: number
  weighted_sum: number
  signals: Record<string, SignalDetail>
  price_targets: PriceTargets
  entry: number
  stop_loss: number
  tp1: number
  tp2: number
  tp3: number
  risk_reward: number
  time_horizon: string
  volatility_pct: number
}

const DIRECTION_CONFIG = {
  BULL:    { color: '#00e676', label: 'BULLISH',  bg: 'rgba(0,230,118,0.12)',  Icon: TrendingUp },
  BEAR:    { color: '#ff1744', label: 'BEARISH',  bg: 'rgba(255,23,68,0.12)',  Icon: TrendingDown },
  NEUTRAL: { color: '#ffab00', label: 'NEUTRAL',  bg: 'rgba(255,171,0,0.12)',  Icon: Minus },
}

const SIGNAL_COLORS = {
  bullish: '#00e676',
  bearish: '#ff1744',
  neutral: '#ffab00',
}

function signalColor(s: string) {
  return SIGNAL_COLORS[s as keyof typeof SIGNAL_COLORS] ?? '#94a3b8'
}

function pctChange(price: number, ref: number) {
  const pct = ((price - ref) / ref) * 100
  return { pct, label: `${pct >= 0 ? '+' : ''}${pct.toFixed(1)}%`, color: pct >= 0 ? '#00e676' : '#ff1744' }
}

function BullGauge({ score, color }: { score: number; color: string }) {
  const data = [{ value: score, fill: color }]
  return (
    <div style={{ width: '100%', height: 200, position: 'relative' }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadialBarChart
          cx="50%" cy="50%"
          innerRadius="60%" outerRadius="90%"
          barSize={14} data={data}
          startAngle={180} endAngle={0}
        >
          <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
          <RadialBar background={{ fill: '#1a2235' }} dataKey="value" angleAxisId={0} cornerRadius={7} />
        </RadialBarChart>
      </ResponsiveContainer>
      <div style={{ position: 'absolute', bottom: '8%', left: 0, right: 0, textAlign: 'center' }}>
        <div className="text-4xl font-bold tabular-nums" style={{ color }}>{score.toFixed(0)}</div>
        <div className="text-xs mt-0.5" style={{ color: '#475569' }}>Bull Score / 100</div>
      </div>
    </div>
  )
}

function SignalBar({ name, detail }: { name: string; detail: SignalDetail }) {
  const contrib = detail.raw_score * detail.weight
  const maxContrib = 0.20
  const barPct = Math.abs(contrib) / maxContrib * 100
  const color = signalColor(detail.signal)

  return (
    <div className="flex items-center gap-3 py-2 border-b" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
      <div className="w-20 text-xs font-medium shrink-0" style={{ color: '#94a3b8' }}>{name}</div>
      <div className="flex-1 flex items-center gap-2">
        <div className="flex-1 flex items-center">
          {contrib < 0 && (
            <div className="ml-auto" style={{ width: `${barPct}%`, maxWidth: '50%' }}>
              <div className="h-2 rounded-l-full" style={{ backgroundColor: color, opacity: 0.8 }} />
            </div>
          )}
          <div className="w-px h-4 shrink-0" style={{ backgroundColor: 'rgba(255,255,255,0.15)' }} />
          {contrib >= 0 && (
            <div style={{ width: `${barPct}%`, maxWidth: '50%' }}>
              <div className="h-2 rounded-r-full" style={{ backgroundColor: color, opacity: 0.8 }} />
            </div>
          )}
        </div>
      </div>
      <div className="w-16 text-right text-xs tabular-nums font-medium" style={{ color }}>
        {contrib >= 0 ? '+' : ''}{contrib.toFixed(3)}
      </div>
      <div className="w-14 text-right text-xs" style={{ color: '#475569' }}>
        val: {detail.value.toFixed(1)}
      </div>
      <div
        className="w-16 text-center text-xs font-semibold rounded-full px-2 py-0.5"
        style={{ color, backgroundColor: `${color}18` }}
      >
        {detail.signal.toUpperCase().slice(0, 4)}
      </div>
    </div>
  )
}

function MetricCard({ label, value, sub, subColor }: { label: string; value: string; sub?: string; subColor?: string }) {
  return (
    <div
      className="rounded-xl border p-4 text-center"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
    >
      <div className="text-xs font-medium uppercase tracking-wide mb-1" style={{ color: '#475569' }}>{label}</div>
      <div className="text-xl font-bold tabular-nums" style={{ color: '#e2e8f0' }}>{value}</div>
      {sub && <div className="text-xs mt-0.5 font-medium" style={{ color: subColor ?? '#94a3b8' }}>{sub}</div>}
    </div>
  )
}

function TargetCard({ label, price, current, icon }: { label: string; price: number; current: number; icon: string }) {
  const { label: pctLabel, color } = pctChange(price, current)
  return (
    <div
      className="rounded-xl border p-4 text-center"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
    >
      <div className="text-xs font-medium uppercase tracking-wide mb-1" style={{ color: '#475569' }}>
        {icon} {label}
      </div>
      <div className="text-xl font-bold tabular-nums" style={{ color: '#e2e8f0' }}>{fmt.price(price)}</div>
      <div className="text-sm font-semibold mt-0.5" style={{ color }}>{pctLabel}</div>
    </div>
  )
}

export default function AiPredictor() {
  const [inputTicker, setInputTicker] = useState('')
  const [ticker, setTicker] = useState('')

  const { data, isLoading, isError, error } = useQuery<AIPrediction>({
    queryKey: ['ai-predictor', ticker],
    queryFn: () => aiPredictorApi.predict(ticker),
    enabled: !!ticker,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const t = inputTicker.trim().toUpperCase()
    if (t) setTicker(t)
  }

  const cfg = data ? DIRECTION_CONFIG[data.direction] : null

  return (
    <PageWrapper>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold" style={{ color: '#e2e8f0' }}>🤖 AI Price Predictor</h1>
        <p className="text-sm mt-1" style={{ color: '#475569' }}>
          9-indicator weighted signal model · 5-day price horizon
        </p>
      </div>

      {/* Search */}
      <form onSubmit={handleSubmit} className="flex gap-3 mb-8 max-w-md">
        <input
          value={inputTicker}
          onChange={e => setInputTicker(e.target.value.toUpperCase())}
          placeholder="Enter ticker — e.g. AAPL, NVDA"
          className="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium outline-none border"
          style={{
            backgroundColor: '#111827',
            borderColor: 'rgba(255,255,255,0.08)',
            color: '#e2e8f0',
          }}
        />
        <button
          type="submit"
          disabled={isLoading}
          className="px-5 py-2.5 rounded-xl text-sm font-semibold transition-opacity disabled:opacity-50"
          style={{ backgroundColor: '#00d4ff', color: '#0a0e1a' }}
        >
          {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Predict'}
        </button>
      </form>

      {/* Loading */}
      {isLoading && (
        <div className="flex flex-col items-center justify-center py-24 gap-4">
          <Loader2 className="w-10 h-10 animate-spin" style={{ color: '#00d4ff' }} />
          <p className="text-sm" style={{ color: '#475569' }}>Running AI analysis for {ticker}…</p>
        </div>
      )}

      {/* Error */}
      {isError && (
        <div
          className="flex items-center gap-3 rounded-xl border p-4 max-w-md"
          style={{ backgroundColor: 'rgba(255,23,68,0.08)', borderColor: 'rgba(255,23,68,0.3)' }}
        >
          <AlertTriangle className="w-5 h-5 shrink-0" style={{ color: '#ff1744' }} />
          <p className="text-sm" style={{ color: '#ff1744' }}>
            {(error as any)?.response?.data?.detail ?? `Could not load data for ${ticker}`}
          </p>
        </div>
      )}

      {/* Results */}
      {data && cfg && (
        <div className="space-y-6">

          {/* Company + direction hero */}
          <div
            className="rounded-xl border p-5 flex items-center gap-4"
            style={{ backgroundColor: cfg.bg, borderColor: `${cfg.color}30` }}
          >
            <div
              className="flex items-center justify-center w-14 h-14 rounded-full shrink-0"
              style={{ backgroundColor: `${cfg.color}20` }}
            >
              <cfg.Icon className="w-7 h-7" style={{ color: cfg.color }} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-xs font-medium mb-0.5" style={{ color: '#475569' }}>
                {data.company_name ?? data.ticker}
              </div>
              <div className="text-3xl font-black tracking-wide" style={{ color: cfg.color }}>
                {cfg.label}
              </div>
              <div className="text-xs mt-0.5" style={{ color: '#475569' }}>
                5-day horizon · Volatility {data.volatility_pct.toFixed(1)}% ann.
              </div>
            </div>
            <div className="text-right shrink-0">
              <div className="text-xs font-medium mb-0.5" style={{ color: '#475569' }}>Composite Score</div>
              <div className="text-3xl font-black tabular-nums" style={{ color: cfg.color }}>
                {data.weighted_sum >= 0 ? '+' : ''}{data.weighted_sum.toFixed(3)}
              </div>
            </div>
          </div>

          {/* Gauge + targets */}
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">

            {/* Gauge card */}
            <div
              className="lg:col-span-2 rounded-xl border p-5"
              style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
            >
              <h3 className="text-sm font-semibold uppercase tracking-wide mb-1" style={{ color: '#94a3b8' }}>
                Bull Score
              </h3>
              <BullGauge score={data.bull_score} color={cfg.color} />
              {/* Confidence bar */}
              <div className="mt-3">
                <div className="flex justify-between text-xs mb-1" style={{ color: '#475569' }}>
                  <span>Confidence</span>
                  <span style={{ color: cfg.color }}>{data.confidence.toFixed(0)}%</span>
                </div>
                <div className="w-full h-2 rounded-full" style={{ backgroundColor: '#1a2235' }}>
                  <div
                    className="h-2 rounded-full transition-all duration-500"
                    style={{ width: `${data.confidence}%`, backgroundColor: cfg.color }}
                  />
                </div>
              </div>
            </div>

            {/* Targets + trade setup */}
            <div className="lg:col-span-3 space-y-4">
              {/* Price targets */}
              <div className="grid grid-cols-3 gap-3">
                <TargetCard label="Conservative" price={data.price_targets.conservative} current={data.price_targets.current} icon="▸" />
                <TargetCard label="Base Target"  price={data.price_targets.base}         current={data.price_targets.current} icon="▸▸" />
                <TargetCard label="Aggressive"   price={data.price_targets.aggressive}   current={data.price_targets.current} icon="▸▸▸" />
              </div>

              {/* Trade setup */}
              <div
                className="rounded-xl border p-4"
                style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
              >
                <div className="text-xs font-semibold uppercase tracking-wide mb-3" style={{ color: '#475569' }}>
                  Trade Setup
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                  <MetricCard label="Entry" value={fmt.price(data.entry)} />
                  <MetricCard
                    label="Stop Loss"
                    value={fmt.price(data.stop_loss)}
                    sub={pctChange(data.stop_loss, data.entry).label}
                    subColor="#ff1744"
                  />
                  <MetricCard
                    label="TP 1"
                    value={fmt.price(data.tp1)}
                    sub={pctChange(data.tp1, data.entry).label}
                    subColor="#00e676"
                  />
                  <MetricCard
                    label="TP 2"
                    value={fmt.price(data.tp2)}
                    sub={pctChange(data.tp2, data.entry).label}
                    subColor="#00e676"
                  />
                  <MetricCard
                    label="Risk / Reward"
                    value={`${data.risk_reward.toFixed(1)}×`}
                    sub={data.risk_reward >= 2 ? 'Favourable' : 'Tight'}
                    subColor={data.risk_reward >= 2 ? '#00e676' : '#ffab00'}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Signal breakdown */}
          <div
            className="rounded-xl border p-5"
            style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
          >
            <h3 className="text-sm font-semibold uppercase tracking-wide mb-1" style={{ color: '#94a3b8' }}>
              Signal Breakdown
            </h3>
            <p className="text-xs mb-4" style={{ color: '#475569' }}>
              Weighted contribution to bull score. Positive = bullish, negative = bearish.
            </p>

            {/* Axis labels */}
            <div className="flex items-center gap-3 mb-1 pb-1 border-b" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
              <div className="w-20 text-xs" style={{ color: '#334155' }}>Indicator</div>
              <div className="flex-1 flex">
                <div className="flex-1 text-right text-xs pr-1" style={{ color: '#475569' }}>← Bearish</div>
                <div className="w-px" />
                <div className="flex-1 text-left text-xs pl-1" style={{ color: '#475569' }}>Bullish →</div>
              </div>
              <div className="w-16 text-right text-xs" style={{ color: '#475569' }}>Wgt.</div>
              <div className="w-14 text-right text-xs" style={{ color: '#475569' }}>Value</div>
              <div className="w-16 text-center text-xs" style={{ color: '#475569' }}>Signal</div>
            </div>

            {Object.entries(data.signals).map(([name, detail]) => (
              <SignalBar key={name} name={name} detail={detail} />
            ))}

            <div className="mt-4 text-xs" style={{ color: '#334155' }}>
              Composite: {data.weighted_sum >= 0 ? '+' : ''}{data.weighted_sum.toFixed(4)} ·
              Threshold ±0.15 · {data.time_horizon} horizon
            </div>
          </div>

        </div>
      )}

      {/* Empty state */}
      {!ticker && !isLoading && (
        <div className="flex flex-col items-center justify-center py-24 gap-3">
          <div className="text-5xl">🤖</div>
          <p className="text-sm" style={{ color: '#475569' }}>
            Enter a ticker above to run the AI prediction model
          </p>
        </div>
      )}
    </PageWrapper>
  )
}
