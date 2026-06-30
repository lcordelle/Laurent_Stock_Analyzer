import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  ScatterChart, Scatter, XAxis, YAxis, ZAxis, ReferenceLine,
  Tooltip as RTooltip, ResponsiveContainer, Cell,
} from 'recharts'
import { radarApi } from '../services/api'
import type { RadarStock, RadarHorizon, RadarResponse } from '../lib/types'
import { fmt } from '../lib/formatters'
import { ACTION_COLOR, BAND_COLOR, GRADE_COLOR, BAND_GLOSS } from '../components/stocks/DecisionParts'

// ── Shared helpers ──────────────────────────────────────────────────────────────

const ARANK: Record<string, number> = {
  'STRONG BUY': 5, BUY: 4, ACCUMULATE: 3, WATCH: 2, SPECULATIVE: 1, AVOID: 0,
}

type Horizon = 'day' | 'swing' | 'long'
const HZ_LABEL: Record<Horizon, string> = { day: 'Day', swing: 'Swing', long: 'Long' }

const aColor = (action?: string) => ACTION_COLOR[action ?? ''] ?? '#64748b'
const bColor = (band?: string | null) => BAND_COLOR[band ?? ''] ?? '#64748b'
const gColor = (grade?: string | null) => GRADE_COLOR[grade ?? ''] ?? '#64748b'

function sortByConviction(list: RadarStock[], hz: string) {
  return [...list].sort((a, b) => {
    const ha = a.horizons[hz], hb = b.horizons[hz]
    const ra = ARANK[ha?.action ?? ''] ?? -1, rb = ARANK[hb?.action ?? ''] ?? -1
    if (ra !== rb) return rb - ra
    const qa = a.quality_score ?? -1, qb = b.quality_score ?? -1
    if (qa !== qb) return qb - qa
    return (hb?.percentile ?? -1) - (ha?.percentile ?? -1)
  })
}

// ── Context chips (shared by card + row) ─────────────────────────────────────────

function ContextChips({ stock, hd }: { stock: RadarStock; hd: RadarHorizon }) {
  const urgentCatalyst = stock.catalyst_days != null && stock.catalyst_days <= 7
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs">
      {stock.catalyst_event && (
        <span style={{ color: urgentCatalyst ? '#ff1744' : '#ffab00' }}>⏱ {stock.catalyst_event}</span>
      )}
      {stock.analyst_upside != null && (
        <span style={{ color: stock.analyst_upside >= 0 ? '#00e676' : '#ff1744' }}>
          {stock.analyst_upside >= 0 ? '+' : ''}{stock.analyst_upside.toFixed(0)}% analyst
        </span>
      )}
      {stock.fair_value_gap_pct != null && (
        <span style={{ color: stock.fair_value_gap_pct <= 0 ? '#00e676' : '#ff9800' }}>
          {stock.fair_value_gap_pct > 0 ? '+' : ''}{stock.fair_value_gap_pct.toFixed(0)}% vs fair
        </span>
      )}
      {hd.size_cap_pct != null && hd.size_cap_pct > 0 && (
        <span style={{ color: '#475569' }}>size ≤{hd.size_cap_pct.toFixed(0)}%</span>
      )}
    </div>
  )
}

// ── Entry-timing line (band + gloss + percentile + window) ───────────────────────

function EntryLine({ hd }: { hd: RadarHorizon }) {
  return (
    <div className="flex items-center gap-2 text-xs flex-wrap">
      <span className="font-bold" style={{ color: bColor(hd.band) }}>{hd.band ?? '—'}</span>
      {hd.band && <span style={{ color: '#475569' }}>— {BAND_GLOSS[hd.band] ?? ''}</span>}
      {hd.percentile != null && (
        <span className="tabular-nums" style={{ color: '#475569' }}>· {hd.percentile.toFixed(0)} pct</span>
      )}
      {hd.horizon_days != null && <span style={{ color: '#334155' }}>· {hd.horizon_days}d</span>}
    </div>
  )
}

// ── ACT NOW card ──────────────────────────────────────────────────────────────

function ActNowCard({ stock, hd, onNavigate }: { stock: RadarStock; hd: RadarHorizon; onNavigate: () => void }) {
  const ac = aColor(hd.action)
  return (
    <div
      onClick={onNavigate}
      className="rounded-xl border p-4 flex flex-col gap-3 cursor-pointer transition-all hover:scale-[1.01]"
      style={{ backgroundColor: '#111827', borderColor: `${ac}40`, background: `linear-gradient(135deg, ${ac}08, #111827 70%)` }}
    >
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xl font-black" style={{ color: '#e2e8f0' }}>{stock.ticker}</div>
          {stock.name && <div className="text-xs truncate max-w-[140px]" style={{ color: '#475569' }}>{stock.name}</div>}
        </div>
        <div className="flex flex-col items-end gap-1">
          <span className="text-xs font-bold px-2 py-0.5 rounded"
            style={{ backgroundColor: `${ac}18`, color: ac, border: `1px solid ${ac}30` }}>
            {hd.action}
          </span>
          {stock.quality_grade && (
            <span className="text-xs font-black tabular-nums" style={{ color: gColor(stock.quality_grade) }}>
              {stock.quality_grade} · {stock.quality_score}
            </span>
          )}
        </div>
      </div>

      <div className="rounded-lg px-3 py-1.5" style={{ backgroundColor: `${bColor(hd.band)}12`, border: `1px solid ${bColor(hd.band)}30` }}>
        <EntryLine hd={hd} />
      </div>

      <div className="flex items-center justify-between text-xs">
        <span className="font-bold tabular-nums" style={{ color: '#e2e8f0' }}>
          {stock.price != null ? fmt.price(stock.price) : '—'}
        </span>
      </div>

      <ContextChips stock={stock} hd={hd} />

      <div className="text-xs leading-relaxed" style={{ color: '#94a3b8' }}>{hd.read}</div>

      <div className="text-xs font-semibold mt-auto" style={{ color: '#00d4ff' }}>Full analysis →</div>
    </div>
  )
}

// ── Watch / Rest row ────────────────────────────────────────────────────────────

function WatchRow({ stock, hd, onNavigate }: { stock: RadarStock; hd: RadarHorizon; onNavigate: () => void }) {
  const ac = aColor(hd.action)
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

      {stock.quality_grade && (
        <span className="text-xs font-black tabular-nums w-12 shrink-0" style={{ color: gColor(stock.quality_grade) }}>
          {stock.quality_grade} {stock.quality_score}
        </span>
      )}

      <span className="text-xs font-bold px-2 py-0.5 rounded shrink-0"
        style={{ backgroundColor: `${ac}15`, color: ac, border: `1px solid ${ac}25` }}>
        {hd.action}
      </span>

      <div className="shrink-0 w-44"><EntryLine hd={hd} /></div>

      <div className="hidden lg:block flex-1 min-w-0">
        <div className="text-xs truncate" style={{ color: '#64748b' }}>{hd.read}</div>
      </div>

      <div className="ml-auto shrink-0"><ContextChips stock={stock} hd={hd} /></div>
    </div>
  )
}

// ── Quadrant tooltip ─────────────────────────────────────────────────────────────

function QuadrantTip({ active, payload }: any) {
  if (!active || !payload?.length) return null
  const p = payload[0].payload as { ticker: string; grade: string | null; action: string; band: string | null; read: string }
  return (
    <div className="rounded-lg border p-2.5 text-xs max-w-[240px]"
      style={{ backgroundColor: '#0a0e1a', borderColor: 'rgba(255,255,255,0.12)', color: '#e2e8f0' }}>
      <div className="flex items-center justify-between gap-3">
        <span className="font-black">{p.ticker}</span>
        {p.grade && <span className="font-bold" style={{ color: gColor(p.grade) }}>{p.grade}</span>}
      </div>
      <div className="font-bold mt-0.5" style={{ color: aColor(p.action) }}>{p.action}</div>
      {p.band && <div style={{ color: bColor(p.band) }}>{p.band} — {BAND_GLOSS[p.band] ?? ''}</div>}
      <div className="mt-1 leading-snug" style={{ color: '#94a3b8' }}>{p.read}</div>
      <div className="mt-1" style={{ color: '#334155' }}>click for full analysis →</div>
    </div>
  )
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
        style={{ backgroundColor: '#0a0e1a', borderColor: 'rgba(255,255,255,0.1)', color: '#e2e8f0' }}
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
  const [horizon, setHorizon] = useState<Horizon>('swing')

  const { data, isLoading, refetch } = useQuery<RadarResponse>({
    queryKey: ['radar', mode],
    queryFn: () => radarApi.getUniverse(),
    staleTime: 5 * 60 * 1000,
    refetchInterval: (query) => {
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
    onSuccess: (result) => { queryClient.setQueryData(['radar', 'universe'], result) },
  })

  const resp = mode === 'custom'
    ? (queryClient.getQueryData(['radar', 'custom']) as RadarResponse | undefined)
    : data
  const stocks = resp?.stocks ?? []

  // Default the horizon to whatever the server marks as default (when data arrives / mode changes).
  useEffect(() => {
    const d = stocks[0]?.default_horizon
    if (d === 'day' || d === 'swing' || d === 'long') setHorizon(d)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resp?.cached_at, mode])

  const hd = (s: RadarStock): RadarHorizon | undefined =>
    s.horizons[horizon] ?? s.horizons['swing'] ?? Object.values(s.horizons)[0]

  const filtered = filterDomain === 'All' ? stocks : stocks.filter(s => s.domain === filterDomain)

  const actNow = sortByConviction(filtered.filter(s => hd(s)?.urgency === 'ACT_NOW'), horizon)
  const watch  = sortByConviction(filtered.filter(s => hd(s)?.urgency === 'WATCH'), horizon)
  const rest   = sortByConviction(filtered.filter(s => hd(s)?.urgency === 'REST'), horizon)

  const domains = ['All', ...Array.from(new Set(stocks.map(s => s.domain).filter(Boolean) as string[]))]
  const isWarming = mode === 'universe' && !isLoading && stocks.length === 0
  const cacheAge = data?.cached_at ? Math.round((Date.now() / 1000 - data.cached_at) / 60) : null
  const regime = resp?.regime

  // Quadrant plot data (only calibrated stocks; uncalibrated go to a note below)
  const plot = filtered
    .map(s => {
      const h = hd(s)
      if (!h || h.percentile == null || s.quality_score == null) return null
      return { ticker: s.ticker, x: h.percentile, y: s.quality_score, action: h.action,
               grade: s.quality_grade ?? null, band: h.band, read: h.read }
    })
    .filter(Boolean) as { ticker: string; x: number; y: number; action: string; grade: string | null; band: string | null; read: string }[]
  const uncalibrated = filtered.filter(s => { const h = hd(s); return h && (h.percentile == null || s.quality_score == null) })

  return (
    <div className="min-h-screen p-4 md:p-6" style={{ backgroundColor: '#0a0e1a', color: '#e2e8f0' }}>

      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight" style={{ color: '#e2e8f0' }}>RADAR</h1>
          <div className="text-xs mt-0.5" style={{ color: '#475569' }}>
            {isWarming ? 'Scanning universe...'
              : `${stocks.length} stocks · ${actNow.length} actionable${cacheAge != null ? ` · refreshed ${cacheAge}m ago` : ''}`}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex rounded-lg border overflow-hidden" style={{ borderColor: 'rgba(255,255,255,0.1)' }}>
            {(['universe', 'custom'] as const).map((m, i) => (
              <button key={m} onClick={() => setMode(m)} className="px-4 py-1.5 text-sm font-medium transition-colors"
                style={{ backgroundColor: mode === m ? '#00d4ff18' : 'transparent', color: mode === m ? '#00d4ff' : '#64748b',
                         borderRight: i === 0 ? '1px solid rgba(255,255,255,0.1)' : undefined }}>
                {m === 'universe' ? '⚡ Universe' : '📋 My List'}
              </button>
            ))}
          </div>
          <button onClick={() => refreshMutation.mutate()} disabled={refreshMutation.isPending}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-opacity disabled:opacity-40"
            style={{ backgroundColor: 'rgba(255,255,255,0.05)', color: '#64748b' }}>
            {refreshMutation.isPending ? 'Scanning…' : '↺ Refresh'}
          </button>
        </div>
      </div>

      {/* Horizon toggle + regime banner */}
      {stocks.length > 0 && (
        <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
          <div className="flex rounded-lg border overflow-hidden" style={{ borderColor: 'rgba(255,255,255,0.1)' }}>
            {(['day', 'swing', 'long'] as const).map((h, i) => (
              <button key={h} onClick={() => setHorizon(h)} className="px-4 py-1.5 text-sm font-medium transition-colors"
                style={{ backgroundColor: horizon === h ? '#00d4ff18' : 'transparent', color: horizon === h ? '#00d4ff' : '#64748b',
                         borderRight: i < 2 ? '1px solid rgba(255,255,255,0.1)' : undefined }}>
                {HZ_LABEL[h]}
              </button>
            ))}
          </div>
          {regime && (
            <div className="text-xs" style={{ color: '#64748b' }}>
              Market mood: <span className="font-bold" style={{ color: '#e2e8f0' }}>{regime.label}</span>
              {regime.vix != null && <> · VIX {regime.vix.toFixed(0)}</>}
              {regime.multiplier !== 1 && <> · entries ×{regime.multiplier.toFixed(2)}</>}
            </div>
          )}
        </div>
      )}

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
            <button key={d} onClick={() => setFilterDomain(d)} className="px-2.5 py-1 rounded-full text-xs font-medium transition-colors"
              style={{ backgroundColor: filterDomain === d ? '#00d4ff18' : 'rgba(255,255,255,0.04)',
                       border: `1px solid ${filterDomain === d ? '#00d4ff40' : 'rgba(255,255,255,0.08)'}`,
                       color: filterDomain === d ? '#00d4ff' : '#94a3b8' }}>
              {d}
            </button>
          ))}
        </div>
      )}

      {isWarming && <WarmingBanner onRefetch={refetch} />}

      {isLoading && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-48 rounded-xl animate-pulse" style={{ backgroundColor: 'rgba(255,255,255,0.04)' }} />
          ))}
        </div>
      )}

      {/* ── Quadrant hero ─────────────────────────────────────────────────────── */}
      {plot.length > 0 && (
        <div className="rounded-xl border p-4 mb-6" style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
          <div className="flex items-center justify-between mb-2">
            <div className="text-xs uppercase tracking-widest" style={{ color: '#475569' }}>Quality × Entry-timing</div>
            <div className="text-xs" style={{ color: '#334155' }}>{HZ_LABEL[horizon]} horizon</div>
          </div>
          <ResponsiveContainer width="100%" height={360}>
            <ScatterChart margin={{ top: 10, right: 24, bottom: 24, left: 4 }}>
              <XAxis type="number" dataKey="x" domain={[0, 100]} tick={{ fill: '#475569', fontSize: 11 }}
                label={{ value: 'Entry timing (percentile) →', position: 'insideBottom', offset: -10, fill: '#475569', fontSize: 11 }} />
              <YAxis type="number" dataKey="y" domain={[0, 100]} tick={{ fill: '#475569', fontSize: 11 }}
                label={{ value: 'Quality →', angle: -90, position: 'insideLeft', fill: '#475569', fontSize: 11 }} />
              <ZAxis range={[70, 70]} />
              <ReferenceLine x={80} stroke="rgba(255,255,255,0.12)" strokeDasharray="3 3" />
              <ReferenceLine y={65} stroke="rgba(255,255,255,0.12)" strokeDasharray="3 3" />
              <RTooltip cursor={{ strokeDasharray: '3 3' }} content={<QuadrantTip />} />
              <Scatter data={plot} onClick={(d: any) => { const t = d?.ticker ?? d?.payload?.ticker; if (t) navigate(`/analysis?ticker=${t}`) }}>
                {plot.map((p, i) => (
                  <Cell key={i} fill={aColor(p.action)} fillOpacity={p.action === 'AVOID' || p.action === 'SPECULATIVE' ? 0.35 : 0.9} />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
          <div className="text-xs mt-1" style={{ color: '#334155' }}>
            Top-right = high quality + strong entry. Click a dot for full analysis.
            {uncalibrated.length > 0 && <> · {uncalibrated.length} uncalibrated (no history) hidden from plot.</>}
          </div>
        </div>
      )}

      {/* ── ACT NOW zone ──────────────────────────────────────────────────────── */}
      {actNow.length > 0 && (
        <section className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#00e676' }} />
            <h2 className="text-sm font-black uppercase tracking-widest" style={{ color: '#00e676' }}>ACT NOW</h2>
            <span className="text-xs px-2 py-0.5 rounded-full font-bold" style={{ backgroundColor: '#00e67620', color: '#00e676' }}>
              {actNow.length} stock{actNow.length !== 1 ? 's' : ''} — buy signal, entry live
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {actNow.map(s => <ActNowCard key={s.ticker} stock={s} hd={hd(s)!} onNavigate={() => navigate(`/analysis?ticker=${s.ticker}`)} />)}
          </div>
        </section>
      )}

      {/* ── WATCH zone ────────────────────────────────────────────────────────── */}
      {watch.length > 0 && (
        <section className="mb-8">
          <div className="flex items-center gap-3 mb-3">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#ffab00' }} />
            <h2 className="text-sm font-black uppercase tracking-widest" style={{ color: '#ffab00' }}>WATCH</h2>
            <span className="text-xs px-2 py-0.5 rounded-full font-bold" style={{ backgroundColor: '#ffab0020', color: '#ffab00' }}>
              {watch.length} stocks — accumulate / waiting for entry
            </span>
          </div>
          <div className="flex flex-col gap-1.5">
            {watch.map(s => <WatchRow key={s.ticker} stock={s} hd={hd(s)!} onNavigate={() => navigate(`/analysis?ticker=${s.ticker}`)} />)}
          </div>
        </section>
      )}

      {/* ── REST zone (collapsed) ─────────────────────────────────────────────── */}
      {rest.length > 0 && (
        <section>
          <button onClick={() => setShowRest(r => !r)} className="flex items-center gap-3 mb-3 group">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: '#334155' }} />
            <h2 className="text-sm font-black uppercase tracking-widest" style={{ color: '#475569' }}>REST</h2>
            <span className="text-xs px-2 py-0.5 rounded-full" style={{ backgroundColor: 'rgba(255,255,255,0.05)', color: '#475569' }}>
              {rest.length} stocks — avoid / no entry signal
            </span>
            <span className="text-xs" style={{ color: '#334155' }}>{showRest ? '▲ collapse' : '▼ expand'}</span>
          </button>
          {showRest && (
            <div className="flex flex-col gap-1.5">
              {rest.map(s => <WatchRow key={s.ticker} stock={s} hd={hd(s)!} onNavigate={() => navigate(`/analysis?ticker=${s.ticker}`)} />)}
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
