import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { radarApi } from '../services/api'
import type { RadarStock, RadarResponse } from '../lib/types'
import { fmt } from '../lib/formatters'

// ── Colour helpers ─────────────────────────────────────────────────────────────

function verdictColor(v: string) {
  if (v.includes('BUY'))  return '#00e676'
  if (v.includes('SELL')) return '#ff1744'
  return '#ffab00'
}

function entryColor(t: string) {
  if (t.startsWith('ENTER NOW'))  return '#00e676'
  if (t.startsWith('ENTER'))      return '#69f0ae'
  if (t.startsWith('SCALE'))      return '#ffab00'
  if (t.startsWith('WAIT'))       return '#ff9800'
  if (t.startsWith('DO NOT'))     return '#ff1744'
  return '#64748b'
}

// ── Warming banner ─────────────────────────────────────────────────────────────

function WarmingBanner({ onRefetch }: { onRefetch: () => void }) {
  const [dots, setDots] = useState('.')
  useEffect(() => {
    const id = setInterval(() => setDots(d => d.length >= 3 ? '.' : d + '.'), 600)
    return () => clearInterval(id)
  }, [])
  useEffect(() => {
    const id = setInterval(onRefetch, 8000)
    return () => clearInterval(id)
  }, [onRefetch])
  return (
    <div className="rounded-xl border p-8 flex flex-col items-center gap-3"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
      <div className="text-2xl font-black" style={{ color: '#00d4ff' }}>RADAR SCANNING{dots}</div>
      <div className="text-sm" style={{ color: '#64748b' }}>
        Running two-pass scan across ~850 stocks. Takes 3–5 minutes on first load.
      </div>
      <div className="text-xs" style={{ color: '#334155' }}>
        This page refreshes automatically every 8 seconds until results are ready.
      </div>
    </div>
  )
}

// ── ACT NOW card ──────────────────────────────────────────────────────────────

function ActNowCard({ stock, onNavigate }: { stock: RadarStock; onNavigate: () => void }) {
  const vc = verdictColor(stock.verdict)
  const ec = entryColor(stock.entry_timing)
  const urgentCatalyst = stock.catalyst_days != null && stock.catalyst_days <= 7
  return (
    <div
      onClick={onNavigate}
      className="rounded-xl border p-4 flex flex-col gap-3 cursor-pointer transition-all hover:scale-[1.01]"
      style={{
        backgroundColor: '#111827',
        borderColor: `${vc}40`,
        background: `linear-gradient(135deg, ${vc}08, #111827 70%)`,
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xl font-black" style={{ color: '#e2e8f0' }}>{stock.ticker}</div>
          {stock.name && (
            <div className="text-xs truncate max-w-[140px]" style={{ color: '#475569' }}>{stock.name}</div>
          )}
        </div>
        <div className="flex flex-col items-end gap-1">
          <span className="text-xs font-bold px-2 py-0.5 rounded"
            style={{ backgroundColor: `${vc}18`, color: vc, border: `1px solid ${vc}30` }}>
            {stock.verdict}
          </span>
          <span className="text-xs font-black tabular-nums" style={{ color: '#64748b' }}>
            {stock.composite}/100
          </span>
        </div>
      </div>

      {/* Entry timing */}
      <div className="flex items-center gap-2 rounded-lg px-3 py-1.5"
        style={{ backgroundColor: `${ec}12`, border: `1px solid ${ec}30` }}>
        <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: ec }} />
        <span className="text-xs font-bold" style={{ color: ec }}>{stock.entry_timing}</span>
      </div>

      {/* Price info */}
      <div className="flex items-center justify-between text-xs">
        <span className="font-bold tabular-nums" style={{ color: '#e2e8f0' }}>
          {stock.price != null ? fmt.price(stock.price) : '—'}
        </span>
        {stock.analyst_upside != null && (
          <span className="font-semibold" style={{ color: stock.analyst_upside >= 0 ? '#00e676' : '#ff1744' }}>
            {stock.analyst_upside >= 0 ? '+' : ''}{stock.analyst_upside.toFixed(1)}% upside
          </span>
        )}
      </div>

      {/* Target range */}
      {(stock.price_target_bear != null || stock.price_target != null || stock.price_target_bull != null) && (
        <div className="flex items-center gap-2 text-xs">
          {stock.price_target_bear != null && (
            <span style={{ color: '#ff1744' }}>{fmt.price(stock.price_target_bear)}</span>
          )}
          {stock.price_target != null && (
            <span className="font-bold" style={{ color: '#00d4ff' }}>→ {fmt.price(stock.price_target)}</span>
          )}
          {stock.price_target_bull != null && (
            <span style={{ color: '#00e676' }}>{fmt.price(stock.price_target_bull)}</span>
          )}
        </div>
      )}

      {/* Catalyst */}
      {stock.catalyst_event && (
        <div className="text-xs font-semibold px-2 py-1 rounded"
          style={{
            backgroundColor: urgentCatalyst ? '#ff174418' : '#ffab0010',
            color: urgentCatalyst ? '#ff1744' : '#ffab00',
          }}>
          {stock.catalyst_event}
        </div>
      )}

      {/* Position sizing */}
      {stock.position_size_pct != null && (
        <div className="text-xs" style={{ color: '#475569' }}>
          Suggested: <span className="font-bold" style={{ color: '#e2e8f0' }}>{stock.position_size_pct}%</span> of portfolio
        </div>
      )}

      {/* Why */}
      <div className="text-xs leading-relaxed" style={{ color: '#64748b' }}>
        {stock.why}
      </div>

      <div className="text-xs font-semibold mt-auto" style={{ color: '#00d4ff' }}>
        Full analysis →
      </div>
    </div>
  )
}

// ── Watch row ─────────────────────────────────────────────────────────────────

function WatchRow({ stock, onNavigate }: { stock: RadarStock; onNavigate: () => void }) {
  const vc = verdictColor(stock.verdict)
  const ec = entryColor(stock.entry_timing)
  return (
    <div
      onClick={onNavigate}
      className="flex items-center gap-4 px-4 py-3 rounded-lg border cursor-pointer transition-colors hover:border-white/10"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.05)' }}
    >
      <div className="w-16 shrink-0">
        <div className="font-bold text-sm" style={{ color: '#e2e8f0' }}>{stock.ticker}</div>
        <div className="text-xs tabular-nums" style={{ color: '#475569' }}>
          {stock.price != null ? fmt.price(stock.price) : '—'}
        </div>
      </div>

      <span className="text-xs font-bold px-2 py-0.5 rounded shrink-0"
        style={{ backgroundColor: `${vc}15`, color: vc, border: `1px solid ${vc}25` }}>
        {stock.verdict}
      </span>

      <div className="text-xs font-black tabular-nums w-10 shrink-0" style={{ color: '#64748b' }}>
        {stock.composite}
      </div>

      <span className="text-xs font-semibold shrink-0" style={{ color: ec }}>
        {stock.entry_timing}
      </span>

      {stock.catalyst_event && (
        <span className="text-xs shrink-0"
          style={{ color: (stock.catalyst_days ?? 99) <= 14 ? '#ffab00' : '#475569' }}>
          {stock.catalyst_event}
        </span>
      )}

      {stock.analyst_upside != null && (
        <span className="text-xs font-semibold ml-auto shrink-0"
          style={{ color: stock.analyst_upside >= 0 ? '#00e676' : '#ff1744' }}>
          {stock.analyst_upside >= 0 ? '+' : ''}{stock.analyst_upside.toFixed(1)}%
        </span>
      )}

      <div className="text-xs shrink-0" style={{ color: '#64748b' }}>
        {stock.why.length > 60 ? stock.why.slice(0, 60) + '…' : stock.why}
      </div>
    </div>
  )
}

// ── Custom ticker input ───────────────────────────────────────────────────────

function CustomInput({ onScan }: { onScan: (tickers: string[]) => void }) {
  const [text, setText] = useState('')
  return (
    <div className="flex gap-2">
      <input
        value={text}
        onChange={e => setText(e.target.value)}
        placeholder="AAPL, NVDA, MSFT, TSLA..."
        className="flex-1 rounded-lg px-3 py-2 text-sm border outline-none"
        style={{
          backgroundColor: '#0a0e1a',
          borderColor: 'rgba(255,255,255,0.1)',
          color: '#e2e8f0',
        }}
      />
      <button
        onClick={() => {
          const tickers = text.split(/[,\s]+/).map(t => t.trim().toUpperCase()).filter(Boolean)
          if (tickers.length) onScan(tickers)
        }}
        className="px-4 py-2 rounded-lg text-sm font-bold"
        style={{ backgroundColor: '#00d4ff18', color: '#00d4ff', border: '1px solid #00d4ff30' }}
      >
        Scan
      </button>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function RadarPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [mode, setMode] = useState<'universe' | 'custom'>('universe')
  const [filterDomain, setFilterDomain] = useState('All')
  const [showRest, setShowRest] = useState(false)

  const { data, isLoading, refetch } = useQuery<RadarResponse>({
    queryKey: ['radar', mode],
    queryFn: () => radarApi.getUniverse(),
    staleTime: 5 * 60 * 1000,
    refetchInterval: (query) => {
      // Auto-poll while warming (no stocks yet)
      if (mode === 'universe' && query.state.data && query.state.data.stocks.length === 0) return 8000
      return false
    },
  })

  const customMutation = useMutation({
    mutationFn: (tickers: string[]) => radarApi.runCustom(tickers),
    onSuccess: (result) => {
      queryClient.setQueryData(['radar', 'custom'], result)
      setMode('custom')
    },
  })

  const refreshMutation = useMutation({
    mutationFn: () => radarApi.refresh(),
    onSuccess: (result) => {
      queryClient.setQueryData(['radar', 'universe'], result)
    },
  })

  const stocks = (mode === 'custom'
    ? (queryClient.getQueryData(['radar', 'custom']) as RadarResponse | undefined)?.stocks
    : data?.stocks) ?? []

  // Apply domain filter
  const filtered = filterDomain === 'All'
    ? stocks
    : stocks.filter(s => s.domain === filterDomain)

  const actNow  = filtered.filter(s => s.action_urgency === 'ACT_NOW')
  const watch   = filtered.filter(s => s.action_urgency === 'WATCH')
  const rest    = filtered.filter(s => s.action_urgency === 'REST')

  const domains = ['All', ...Array.from(new Set(stocks.map(s => s.domain).filter(Boolean) as string[]))]

  const isWarming = mode === 'universe' && !isLoading && stocks.length === 0

  const cacheAge = data?.cached_at
    ? Math.round((Date.now() / 1000 - data.cached_at) / 60)
    : null

  return (
    <div className="min-h-screen p-4 md:p-6" style={{ backgroundColor: '#0a0e1a', color: '#e2e8f0' }}>

      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3 mb-6">
        <div>
          <h1 className="text-2xl font-black tracking-tight" style={{ color: '#e2e8f0' }}>
            RADAR
          </h1>
          <div className="text-xs mt-0.5" style={{ color: '#475569' }}>
            {isWarming
              ? 'Scanning universe...'
              : `${stocks.length} stocks · ${actNow.length} actionable${cacheAge != null ? ` · refreshed ${cacheAge}m ago` : ''}`
            }
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Mode toggle */}
          <div className="flex rounded-lg border overflow-hidden" style={{ borderColor: 'rgba(255,255,255,0.1)' }}>
            {(['universe', 'custom'] as const).map((m, i) => (
              <button key={m} onClick={() => setMode(m)}
                className="px-4 py-1.5 text-sm font-medium transition-colors"
                style={{
                  backgroundColor: mode === m ? '#00d4ff18' : 'transparent',
                  color: mode === m ? '#00d4ff' : '#64748b',
                  borderRight: i === 0 ? '1px solid rgba(255,255,255,0.1)' : undefined,
                }}>
                {m === 'universe' ? '⚡ Universe' : '📋 My List'}
              </button>
            ))}
          </div>

          <button
            onClick={() => refreshMutation.mutate()}
            disabled={refreshMutation.isPending}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-opacity disabled:opacity-40"
            style={{ backgroundColor: 'rgba(255,255,255,0.05)', color: '#64748b' }}>
            {refreshMutation.isPending ? 'Scanning…' : '↺ Refresh'}
          </button>
        </div>
      </div>

      {/* Custom scan input */}
      {mode === 'custom' && (
        <div className="mb-4">
          <CustomInput onScan={tickers => customMutation.mutate(tickers)} />
          {customMutation.isPending && (
            <div className="text-xs mt-2" style={{ color: '#00d4ff' }}>Scanning {customMutation.variables?.length ?? 0} tickers…</div>
          )}
        </div>
      )}

      {/* Domain filter pills */}
      {stocks.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-5">
          {domains.slice(0, 12).map(d => (
            <button key={d} onClick={() => setFilterDomain(d)}
              className="px-2.5 py-1 rounded-full text-xs font-medium transition-colors"
              style={{
                backgroundColor: filterDomain === d ? '#00d4ff18' : 'rgba(255,255,255,0.04)',
                border: `1px solid ${filterDomain === d ? '#00d4ff40' : 'rgba(255,255,255,0.08)'}`,
                color: filterDomain === d ? '#00d4ff' : '#94a3b8',
              }}>
              {d}
            </button>
          ))}
        </div>
      )}

      {/* Warming state */}
      {isWarming && <WarmingBanner onRefetch={refetch} />}

      {/* Loading skeleton */}
      {isLoading && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-48 rounded-xl animate-pulse"
              style={{ backgroundColor: 'rgba(255,255,255,0.04)' }} />
          ))}
        </div>
      )}

      {/* ── ACT NOW zone ──────────────────────────────────────────────────────── */}
      {actNow.length > 0 && (
        <section className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#00e676' }} />
              <h2 className="text-sm font-black uppercase tracking-widest" style={{ color: '#00e676' }}>
                ACT NOW
              </h2>
            </div>
            <span className="text-xs px-2 py-0.5 rounded-full font-bold"
              style={{ backgroundColor: '#00e67620', color: '#00e676' }}>
              {actNow.length} stock{actNow.length !== 1 ? 's' : ''} with live entry signal
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {actNow.map(s => (
              <ActNowCard
                key={s.ticker}
                stock={s}
                onNavigate={() => navigate(`/analysis?ticker=${s.ticker}`)}
              />
            ))}
          </div>
        </section>
      )}

      {/* ── WATCH zone ────────────────────────────────────────────────────────── */}
      {watch.length > 0 && (
        <section className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#ffab00' }} />
              <h2 className="text-sm font-black uppercase tracking-widest" style={{ color: '#ffab00' }}>
                WATCH
              </h2>
            </div>
            <span className="text-xs px-2 py-0.5 rounded-full font-bold"
              style={{ backgroundColor: '#ffab0020', color: '#ffab00' }}>
              {watch.length} stocks — BUY signal, waiting for entry
            </span>
          </div>
          <div className="flex flex-col gap-1.5">
            {watch.map(s => (
              <WatchRow
                key={s.ticker}
                stock={s}
                onNavigate={() => navigate(`/analysis?ticker=${s.ticker}`)}
              />
            ))}
          </div>
        </section>
      )}

      {/* ── REST zone (collapsed) ─────────────────────────────────────────────── */}
      {rest.length > 0 && (
        <section>
          <button
            onClick={() => setShowRest(r => !r)}
            className="flex items-center gap-3 mb-3 group"
          >
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#334155' }} />
              <h2 className="text-sm font-black uppercase tracking-widest" style={{ color: '#475569' }}>
                REST
              </h2>
            </div>
            <span className="text-xs px-2 py-0.5 rounded-full"
              style={{ backgroundColor: 'rgba(255,255,255,0.05)', color: '#475569' }}>
              {rest.length} stocks — HOLD / SELL / no entry signal
            </span>
            <span className="text-xs" style={{ color: '#334155' }}>
              {showRest ? '▲ collapse' : '▼ expand'}
            </span>
          </button>
          {showRest && (
            <div className="flex flex-col gap-1.5">
              {rest.map(s => (
                <WatchRow
                  key={s.ticker}
                  stock={s}
                  onNavigate={() => navigate(`/analysis?ticker=${s.ticker}`)}
                />
              ))}
            </div>
          )}
        </section>
      )}

      {/* Empty state */}
      {!isLoading && !isWarming && stocks.length === 0 && mode === 'custom' && (
        <div className="text-center py-16" style={{ color: '#475569' }}>
          Enter tickers above and click Scan to run a custom analysis.
        </div>
      )}
    </div>
  )
}
