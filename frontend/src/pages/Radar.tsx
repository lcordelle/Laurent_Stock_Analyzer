import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { radarApi } from '../services/api'
import type { RadarStock, RadarResponse } from '../lib/types'

function verdictColor(verdict: string): string {
  if (verdict.includes('BUY')) return '#00e676'
  if (verdict.includes('SELL')) return '#ff1744'
  return '#ffab00'
}

function signalKey(key: string): string {
  const MAP: Record<string, string> = {
    ai_outlook: 'AI Outlook',
    news_sentiment: 'News',
    earnings_quality: 'Earnings',
  }
  return MAP[key] ?? key.charAt(0).toUpperCase() + key.slice(1)
}

function ModeToggle({
  mode, setMode,
}: {
  mode: 'universe' | 'custom'
  setMode: (m: 'universe' | 'custom') => void
}) {
  return (
    <div
      className="flex rounded-lg overflow-hidden border"
      style={{ borderColor: 'rgba(255,255,255,0.1)' }}
    >
      {(['universe', 'custom'] as const).map((m, i) => (
        <button
          key={m}
          onClick={() => setMode(m)}
          className="px-4 py-1.5 text-sm font-medium transition-colors"
          style={{
            backgroundColor: mode === m ? '#00d4ff18' : 'transparent',
            color: mode === m ? '#00d4ff' : '#64748b',
            borderRight: i === 0 ? '1px solid rgba(255,255,255,0.1)' : undefined,
          }}
        >
          {m === 'universe' ? '⚡ Universe' : '📋 My List'}
        </button>
      ))}
    </div>
  )
}

function StatusBar({
  data, onRefresh,
}: {
  data?: RadarResponse
  onRefresh: () => void
}) {
  const age = data?.cached_at
    ? Math.round((Date.now() / 1000 - data.cached_at) / 60)
    : null
  return (
    <div className="flex items-center gap-3 text-xs mb-4" style={{ color: '#64748b' }}>
      <span>{data?.total_scanned ?? '—'} stocks scanned</span>
      <span>·</span>
      <span>{data?.shortlist_count ?? '—'} in shortlist</span>
      {age !== null && (
        <>
          <span>·</span>
          <span>{age}m ago</span>
        </>
      )}
      <button
        onClick={onRefresh}
        className="ml-1 transition-colors hover:opacity-80"
        style={{ color: '#00d4ff' }}
      >
        Refresh
      </button>
    </div>
  )
}

function FilterBar({
  domain, setDomain,
  verdict, setVerdict,
  domains,
}: {
  domain: string
  setDomain: (d: string) => void
  verdict: string
  setVerdict: (v: string) => void
  domains: string[]
}) {
  return (
    <div className="flex flex-wrap items-center gap-2 mb-4">
      <div className="flex gap-1.5 flex-wrap">
        {domains.slice(0, 8).map(d => (
          <button
            key={d}
            onClick={() => setDomain(d)}
            className="px-2.5 py-1 rounded-full text-xs font-medium transition-colors"
            style={{
              backgroundColor: domain === d ? '#00d4ff18' : 'rgba(255,255,255,0.04)',
              border: `1px solid ${domain === d ? '#00d4ff40' : 'rgba(255,255,255,0.08)'}`,
              color: domain === d ? '#00d4ff' : '#94a3b8',
            }}
          >
            {d}
          </button>
        ))}
      </div>
      <div className="flex gap-1.5 ml-auto">
        {['All', 'STRONG BUY', 'BUY', 'HOLD'].map(v => {
          const vc = v === 'All' ? '#94a3b8' : verdictColor(v)
          return (
            <button
              key={v}
              onClick={() => setVerdict(v)}
              className="px-2.5 py-1 rounded-full text-xs font-medium transition-colors"
              style={{
                backgroundColor: verdict === v ? `${vc}18` : 'rgba(255,255,255,0.04)',
                border: `1px solid ${verdict === v ? `${vc}40` : 'rgba(255,255,255,0.08)'}`,
                color: verdict === v ? vc : '#94a3b8',
              }}
            >
              {v}
            </button>
          )
        })}
      </div>
    </div>
  )
}

function HeroCard({
  stock, onNavigate,
}: {
  stock: RadarStock
  onNavigate: () => void
}) {
  const color = verdictColor(stock.verdict)
  return (
    <div
      className="rounded-xl border p-6 mb-4"
      style={{ backgroundColor: '#111827', borderColor: `${color}30` }}
    >
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span
              className="text-xs font-bold px-2 py-0.5 rounded"
              style={{ backgroundColor: '#00d4ff18', color: '#00d4ff' }}
            >
              #1 TOP PICK
            </span>
            <span
              className="text-sm font-bold px-3 py-1 rounded-lg"
              style={{
                backgroundColor: `${color}18`,
                color,
                border: `1px solid ${color}30`,
              }}
            >
              {stock.verdict}
            </span>
          </div>
          <div className="flex items-baseline gap-3">
            <span className="text-3xl font-bold" style={{ color: '#e2e8f0' }}>
              {stock.ticker}
            </span>
            {stock.name && (
              <span className="text-sm" style={{ color: '#64748b' }}>
                {stock.name}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 mt-1">
            <span className="text-4xl font-bold tabular-nums" style={{ color }}>
              {stock.composite}
            </span>
            <span className="text-sm" style={{ color: '#475569' }}>/ 100</span>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2">
          {stock.price != null && (
            <span className="text-2xl font-bold tabular-nums" style={{ color: '#e2e8f0' }}>
              ${stock.price.toFixed(2)}
            </span>
          )}
          <div className="flex flex-wrap gap-3 text-xs justify-end">
            {stock.stop_loss != null && (
              <span style={{ color: '#94a3b8' }}>
                SL{' '}
                <span style={{ color: '#ff1744' }}>${stock.stop_loss.toFixed(2)}</span>
              </span>
            )}
            {stock.price_target != null && (
              <span style={{ color: '#94a3b8' }}>
                Target{' '}
                <span style={{ color: '#00e676' }}>${stock.price_target.toFixed(2)}</span>
              </span>
            )}
            {stock.risk_reward != null && (
              <span style={{ color: '#94a3b8' }}>
                R:R{' '}
                <span style={{ color: '#00d4ff' }}>{stock.risk_reward.toFixed(1)}×</span>
              </span>
            )}
            {stock.analyst_upside != null && (
              <span style={{ color: '#94a3b8' }}>
                Analyst{' '}
                <span
                  style={{
                    color: stock.analyst_upside > 0 ? '#00e676' : '#ff1744',
                  }}
                >
                  {stock.analyst_upside > 0 ? '+' : ''}
                  {stock.analyst_upside.toFixed(0)}%
                </span>
              </span>
            )}
          </div>
        </div>
      </div>

      <div
        className="mt-4 px-4 py-2 rounded-lg text-sm italic"
        style={{
          backgroundColor: `${color}08`,
          borderLeft: `3px solid ${color}50`,
          color: '#94a3b8',
        }}
      >
        {stock.why}
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {Object.entries(stock.signals).map(([key, detail]) => {
          const sc = detail.score
          const pc = sc > 60 ? '#00e676' : sc >= 40 ? '#ffab00' : '#ff1744'
          return (
            <div
              key={key}
              className="flex items-center gap-2 rounded-lg px-3 py-1.5"
              style={{ background: `${pc}0d`, border: `1px solid ${pc}30` }}
            >
              <span
                className="w-1.5 h-1.5 rounded-full shrink-0"
                style={{ backgroundColor: pc }}
              />
              <span className="text-xs font-semibold" style={{ color: '#e2e8f0' }}>
                {signalKey(key)}
              </span>
              <span className="text-xs font-bold" style={{ color: pc }}>
                {detail.label}
              </span>
              <span className="text-xs tabular-nums" style={{ color: '#475569' }}>
                {detail.score}
              </span>
            </div>
          )
        })}
      </div>

      <div className="mt-4">
        <button
          onClick={onNavigate}
          className="px-5 py-2 rounded-lg text-sm font-semibold transition-colors hover:opacity-80"
          style={{
            backgroundColor: '#00d4ff18',
            border: '1px solid #00d4ff40',
            color: '#00d4ff',
          }}
        >
          Full Analysis →
        </button>
      </div>
    </div>
  )
}

function StockCard({
  stock, rank, onClick,
}: {
  stock: RadarStock
  rank: number
  onClick: () => void
}) {
  const color = verdictColor(stock.verdict)
  const topSignals = Object.entries(stock.signals)
    .sort((a, b) => Math.abs(b[1].score - 50) - Math.abs(a[1].score - 50))
    .slice(0, 3)

  return (
    <div
      className="rounded-xl border p-4 cursor-pointer transition-all"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
      onClick={onClick}
      onMouseEnter={e => {
        ;(e.currentTarget as HTMLDivElement).style.borderColor =
          'rgba(255,255,255,0.15)'
      }}
      onMouseLeave={e => {
        ;(e.currentTarget as HTMLDivElement).style.borderColor =
          'rgba(255,255,255,0.06)'
      }}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-start gap-2">
          <span
            className="text-xs font-bold mt-1 w-5 tabular-nums shrink-0"
            style={{ color: '#475569' }}
          >
            #{rank}
          </span>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-bold" style={{ color: '#e2e8f0' }}>
                {stock.ticker}
              </span>
              <span
                className="text-xs font-bold px-2 py-0.5 rounded"
                style={{
                  backgroundColor: `${color}18`,
                  color,
                  border: `1px solid ${color}30`,
                }}
              >
                {stock.verdict}
              </span>
            </div>
            {stock.name && (
              <span className="text-xs" style={{ color: '#475569' }}>
                {stock.name}
              </span>
            )}
          </div>
        </div>

        <div className="text-right shrink-0">
          <div className="text-xl font-bold tabular-nums" style={{ color }}>
            {stock.composite}
          </div>
          {stock.price != null && (
            <div
              className="text-xs tabular-nums mt-0.5"
              style={{ color: '#64748b' }}
            >
              ${stock.price.toFixed(2)}
            </div>
          )}
        </div>
      </div>

      <p
        className="text-xs mt-2 overflow-hidden"
        style={{
          color: '#64748b',
          display: '-webkit-box',
          WebkitLineClamp: 1,
          WebkitBoxOrient: 'vertical',
        }}
      >
        {stock.why}
      </p>

      <div className="flex gap-1.5 mt-2 flex-wrap">
        {topSignals.map(([key, detail]) => {
          const sc = detail.score
          const pc = sc > 60 ? '#00e676' : sc >= 40 ? '#ffab00' : '#ff1744'
          return (
            <span
              key={key}
              className="text-xs px-2 py-0.5 rounded"
              style={{
                backgroundColor: `${pc}12`,
                color: pc,
                border: `1px solid ${pc}25`,
              }}
            >
              {signalKey(key)} {detail.score}
            </span>
          )
        })}
      </div>
    </div>
  )
}

function MyListInput({
  onSubmit, isLoading,
}: {
  onSubmit: (tickers: string[]) => void
  isLoading: boolean
}) {
  const [input, setInput] = useState('')
  const tickerCount = input.split(/[\s,]+/).filter(Boolean).length

  const handleSubmit = () => {
    const tickers = input
      .split(/[\s,]+/)
      .map(t => t.trim().toUpperCase())
      .filter(Boolean)
      .slice(0, 20)
    if (tickers.length > 0) onSubmit(tickers)
  }

  return (
    <div
      className="rounded-xl border p-6 mb-4"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.08)' }}
    >
      <p className="text-sm mb-3" style={{ color: '#94a3b8' }}>
        Enter up to 20 tickers — comma or space separated
      </p>
      <textarea
        value={input}
        onChange={e => setInput(e.target.value)}
        placeholder="AAPL MSFT NVDA GOOGL AMZN"
        rows={3}
        className="w-full rounded-lg px-4 py-3 text-sm font-mono resize-none outline-none"
        style={{
          backgroundColor: 'rgba(255,255,255,0.04)',
          border: '1px solid rgba(255,255,255,0.1)',
          color: '#e2e8f0',
        }}
      />
      <div className="flex items-center justify-between mt-3">
        <span className="text-xs" style={{ color: '#475569' }}>
          {tickerCount} / 20 tickers
        </span>
        <button
          onClick={handleSubmit}
          disabled={isLoading || tickerCount === 0}
          className="px-5 py-2 rounded-lg text-sm font-semibold transition-colors disabled:opacity-40"
          style={{
            backgroundColor: '#00d4ff18',
            border: '1px solid #00d4ff40',
            color: '#00d4ff',
          }}
        >
          {isLoading ? 'Running verdict…' : 'Run Verdict'}
        </button>
      </div>
    </div>
  )
}

function RadarSkeleton() {
  return (
    <div className="space-y-3 animate-pulse">
      <div
        className="rounded-xl border p-6 h-52"
        style={{
          backgroundColor: '#111827',
          borderColor: 'rgba(255,255,255,0.06)',
        }}
      />
      <div className="grid grid-cols-2 gap-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="rounded-xl border p-4 h-24"
            style={{
              backgroundColor: '#111827',
              borderColor: 'rgba(255,255,255,0.06)',
            }}
          />
        ))}
      </div>
    </div>
  )
}

export default function Radar() {
  const navigate = useNavigate()
  const [mode, setMode] = useState<'universe' | 'custom'>('universe')
  const [customStocks, setCustomStocks] = useState<RadarStock[] | null>(null)
  const [domainFilter, setDomainFilter] = useState('All')
  const [verdictFilter, setVerdictFilter] = useState('All')

  const { data, isLoading, refetch } = useQuery<RadarResponse>({
    queryKey: ['radar'],
    queryFn: radarApi.getUniverse,
    staleTime: 30 * 60_000,
    enabled: mode === 'universe',
  })

  const mutation = useMutation({
    mutationFn: (tickers: string[]) => radarApi.runCustom(tickers),
    onSuccess: (result: RadarResponse) => setCustomStocks(result.stocks),
  })

  const handleModeSwitch = (m: 'universe' | 'custom') => {
    setMode(m)
    setDomainFilter('All')
    setVerdictFilter('All')
    if (m === 'universe') setCustomStocks(null)
  }

  const allStocks = mode === 'universe' ? (data?.stocks ?? []) : (customStocks ?? [])

  const filtered = allStocks.filter(s => {
    if (domainFilter !== 'All' && s.domain !== domainFilter) return false
    if (verdictFilter !== 'All' && s.verdict !== verdictFilter) return false
    return true
  })

  const hero = filtered[0]
  const shortlist = filtered.slice(1, 25)
  const domains = [
    'All',
    ...Array.from(
      new Set(allStocks.map(s => s.domain).filter((d): d is string => Boolean(d)))
    ),
  ]

  const showResults =
    mode === 'universe' || (mode === 'custom' && customStocks !== null)

  return (
    <main
      className="pt-14 min-h-screen"
      style={{ backgroundColor: '#0a0e1a', color: '#e2e8f0' }}
    >
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex items-start justify-between mb-5">
          <div>
            <h1 className="text-2xl font-bold" style={{ color: '#e2e8f0' }}>
              Radar
            </h1>
            <p className="text-sm mt-0.5" style={{ color: '#475569' }}>
              8-signal verdict engine · ranked by conviction
            </p>
          </div>
          <ModeToggle mode={mode} setMode={handleModeSwitch} />
        </div>

        {mode === 'universe' && (
          <StatusBar data={data} onRefresh={() => refetch()} />
        )}

        {mode === 'custom' && customStocks !== null && (
          <div
            className="flex items-center gap-3 mb-4 text-xs"
            style={{ color: '#64748b' }}
          >
            <span>{customStocks.length} stocks analysed</span>
            <button
              onClick={() => {
                setCustomStocks(null)
                setDomainFilter('All')
                setVerdictFilter('All')
              }}
              style={{ color: '#00d4ff' }}
            >
              Clear ×
            </button>
          </div>
        )}

        {mode === 'custom' && customStocks === null && (
          <MyListInput
            onSubmit={t => mutation.mutate(t)}
            isLoading={mutation.isPending}
          />
        )}

        {showResults && (
          <>
            <FilterBar
              domain={domainFilter}
              setDomain={setDomainFilter}
              verdict={verdictFilter}
              setVerdict={setVerdictFilter}
              domains={domains}
            />

            {isLoading && mode === 'universe' ? (
              <RadarSkeleton />
            ) : (
              <>
                {hero && (
                  <HeroCard
                    stock={hero}
                    onNavigate={() =>
                      navigate(`/analysis?ticker=${hero.ticker}`)
                    }
                  />
                )}
                {filtered.length === 0 && !isLoading && (
                  <div
                    className="text-center py-16"
                    style={{ color: '#475569' }}
                  >
                    No stocks match the selected filters
                  </div>
                )}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
                  {shortlist.map((stock, i) => (
                    <StockCard
                      key={stock.ticker}
                      stock={stock}
                      rank={i + 2}
                      onClick={() =>
                        navigate(`/analysis?ticker=${stock.ticker}`)
                      }
                    />
                  ))}
                </div>
              </>
            )}
          </>
        )}
      </div>
    </main>
  )
}
