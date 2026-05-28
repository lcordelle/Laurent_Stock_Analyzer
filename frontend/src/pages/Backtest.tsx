import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { backtestApi } from '../services/api'
import PageWrapper from '../components/layout/PageWrapper'

const CARD: React.CSSProperties = {
  backgroundColor: '#111827',
  border: '1px solid rgba(255,255,255,0.06)',
  borderRadius: 12,
  padding: '16px',
}

const STRATEGIES: Record<string, string> = {
  ma_crossover: 'MA Crossover (SMA20 > SMA50)',
  rsi: 'RSI Strategy (Buy <30, Sell >70)',
  golden_cross: 'Golden Cross (SMA50 > SMA200)',
}

const STRATEGY_HINTS: Record<string, string> = {
  ma_crossover: 'Buy when the 20-day MA crosses above the 50-day MA. Sell when it crosses below. Captures medium-term trends.',
  rsi: 'Buy when RSI(14) drops below 30 (oversold). Sell when RSI exceeds 70 (overbought). Works best in ranging markets.',
  golden_cross: 'Buy when SMA(50) crosses above SMA(200). Sell when it crosses below. Long-term momentum signal.',
}

function KPI({ label, value, color = '#e2e8f0', sub }: { label: string; value: string; color?: string; sub?: string }) {
  return (
    <div style={CARD}>
      <p className="text-xs mb-1" style={{ color: '#475569' }}>{label}</p>
      <p className="text-2xl font-bold" style={{ color }}>{value}</p>
      {sub && <p className="text-xs mt-1" style={{ color: '#475569' }}>{sub}</p>}
    </div>
  )
}

const PERIODS = ['1y', '2y', '3y', '5y']

export default function Backtest() {
  const [searchParams] = useSearchParams()
  const [ticker, setTicker] = useState(searchParams.get('ticker') ?? 'AAPL')
  const [strategy, setStrategy] = useState('ma_crossover')

  useEffect(() => {
    const t = searchParams.get('ticker')
    if (t) setTicker(t)
  }, [searchParams])
  const [period, setPeriod] = useState('2y')
  const [capital, setCapital] = useState('10000')

  const { mutate, data, isPending, isError, error } = useMutation({
    mutationFn: () => backtestApi.run(ticker.toUpperCase(), strategy, period, parseFloat(capital) || 10000),
  })

  const m = data?.metrics
  const pnlColor = (v: number) => v >= 0 ? '#00e676' : '#ff1744'

  // Merge equity + spy curves by date for Recharts
  const chartData = (() => {
    if (!data?.equity_curve?.length) return []
    const spyMap: Record<string, number> = {}
    for (const p of data.spy_curve || []) spyMap[p.date] = p.value
    return data.equity_curve.map((p: any) => ({
      date: p.date,
      Strategy: p.value,
      SPY: spyMap[p.date] ?? null,
    }))
  })()

  return (
    <PageWrapper title="Backtesting">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-1" style={{ color: '#e2e8f0' }}>Backtesting</h1>
        <p className="text-sm" style={{ color: '#475569' }}>Simulate strategies on historical data · compare vs SPY</p>
      </div>

      {/* Controls */}
      <div style={CARD} className="mb-6">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="text-xs block mb-1" style={{ color: '#475569' }}>Ticker</label>
            <input value={ticker} onChange={e => setTicker(e.target.value.toUpperCase())}
              className="w-full px-3 py-2 rounded-lg text-sm outline-none"
              style={{ backgroundColor: '#1e2535', border: '1px solid rgba(255,255,255,0.08)', color: '#e2e8f0' }} />
          </div>
          <div>
            <label className="text-xs block mb-1" style={{ color: '#475569' }}>Strategy</label>
            <select value={strategy} onChange={e => setStrategy(e.target.value)}
              className="w-full px-3 py-2 rounded-lg text-sm outline-none"
              style={{ backgroundColor: '#1e2535', border: '1px solid rgba(255,255,255,0.08)', color: '#e2e8f0' }}>
              {Object.entries(STRATEGIES).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs block mb-1" style={{ color: '#475569' }}>Period</label>
            <select value={period} onChange={e => setPeriod(e.target.value)}
              className="w-full px-3 py-2 rounded-lg text-sm outline-none"
              style={{ backgroundColor: '#1e2535', border: '1px solid rgba(255,255,255,0.08)', color: '#e2e8f0' }}>
              {PERIODS.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs block mb-1" style={{ color: '#475569' }}>Initial Capital ($)</label>
            <input type="number" value={capital} onChange={e => setCapital(e.target.value)}
              className="w-full px-3 py-2 rounded-lg text-sm outline-none"
              style={{ backgroundColor: '#1e2535', border: '1px solid rgba(255,255,255,0.08)', color: '#e2e8f0' }} />
          </div>
        </div>
        <p className="text-xs mb-4" style={{ color: '#475569' }}>{STRATEGY_HINTS[strategy]}</p>
        <button
          onClick={() => mutate()}
          disabled={isPending || !ticker}
          className="px-6 py-2 rounded-lg text-sm font-semibold disabled:opacity-50 transition-opacity hover:opacity-80"
          style={{ backgroundColor: '#00d4ff', color: '#0a0e1a' }}
        >
          {isPending ? 'Running backtest…' : 'Run Backtest'}
        </button>
      </div>

      {isError && (
        <div className="mb-4 p-3 rounded-lg" style={{ backgroundColor: '#ff174422', border: '1px solid #ff1744' }}>
          <p className="text-sm" style={{ color: '#ff1744' }}>Backtest failed: {(error as Error)?.message}</p>
        </div>
      )}

      {data?.error && (
        <div className="mb-4 p-3 rounded-lg" style={{ backgroundColor: '#ff174422', border: '1px solid #ff1744' }}>
          <p className="text-sm" style={{ color: '#ff1744' }}>{data.error}</p>
        </div>
      )}

      {m && (
        <>
          {/* KPI Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-6">
            <KPI label="Strategy Return" value={`${m.total_return > 0 ? '+' : ''}${m.total_return?.toFixed(1)}%`}
              color={pnlColor(m.total_return)} sub={`${m.alpha > 0 ? '+' : ''}${m.alpha?.toFixed(1)}% vs SPY`} />
            <KPI label="SPY Return" value={`${m.spy_return > 0 ? '+' : ''}${m.spy_return?.toFixed(1)}%`}
              color={pnlColor(m.spy_return)} />
            <KPI label="Sharpe Ratio" value={m.sharpe?.toFixed(2)}
              color={m.sharpe >= 1 ? '#00e676' : m.sharpe >= 0.5 ? '#ffab00' : '#ff1744'} />
            <KPI label="Max Drawdown" value={`${m.max_drawdown?.toFixed(1)}%`} color="#ff1744" />
            <KPI label="Win Rate" value={`${m.win_rate}%`} color={m.win_rate >= 50 ? '#00e676' : '#ff1744'}
              sub={`${m.total_trades} trades`} />
          </div>

          <div className="mb-4 text-sm" style={{ color: '#475569' }}>
            Final value:{' '}
            <span style={{ color: pnlColor(m.total_return) }} className="font-semibold">
              ${m.final_value?.toLocaleString('en-US', { maximumFractionDigits: 2 })}
            </span>
            {' '}(started with ${m.initial_capital?.toLocaleString()})
          </div>

          {/* Equity Curve */}
          {chartData.length > 0 && (
            <div style={CARD}>
              <h3 className="text-sm font-semibold mb-4" style={{ color: '#94a3b8' }}>
                {data.ticker} — {data.strategy_label} ({data.period})
              </h3>
              <ResponsiveContainer width="100%" height={360}>
                <AreaChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                  <defs>
                    <linearGradient id="stratGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#00d4ff" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="spyGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#475569" stopOpacity={0.15} />
                      <stop offset="95%" stopColor="#475569" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="date" tick={{ fill: '#475569', fontSize: 10 }} tickLine={false}
                    interval={Math.floor(chartData.length / 6)} />
                  <YAxis tick={{ fill: '#475569', fontSize: 10 }} tickLine={false} axisLine={false}
                    tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e2535', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
                    labelStyle={{ color: '#94a3b8' }}
                    formatter={(v: any) => [`$${Number(v).toLocaleString('en-US', { maximumFractionDigits: 0 })}`, '']}
                  />
                  <Legend iconType="circle" wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
                  <Area type="monotone" dataKey="Strategy" stroke="#00d4ff" strokeWidth={2}
                    fill="url(#stratGrad)" connectNulls />
                  <Area type="monotone" dataKey="SPY" stroke="#475569" strokeWidth={1.5}
                    strokeDasharray="4 4" fill="url(#spyGrad)" connectNulls />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </PageWrapper>
  )
}
