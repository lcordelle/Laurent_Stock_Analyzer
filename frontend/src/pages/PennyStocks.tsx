import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Loader2, RefreshCw, AlertTriangle, TrendingUp, BookmarkPlus, Check } from 'lucide-react'
import { pennyStocksApi } from '../services/api'
import { fmt, scoreColor } from '../lib/formatters'
import PageWrapper from '../components/layout/PageWrapper'
import { addToWatchlist } from '../lib/watchlist'

interface PennyStockItem {
  ticker: string
  name?: string
  penny_category?: string
  sector?: string
  price?: number
  market_cap?: number
  vf_score?: number
  signal?: string
  confidence?: number
  rsi?: number
  rsi_signal?: string
  macd_signal?: string
  trend?: string
  stop_loss?: number
  tp1?: number
  tp2?: number
  tp3?: number
  risk_reward?: number
  analyst_target?: number
  analyst_upside?: number
  week52_momentum?: number
  pe_ratio?: number
  revenue_growth?: number
  combined_score?: number
  why_now?: string
}

interface PennyStocksResponse {
  stocks: PennyStockItem[]
  total_scanned: number
  total_qualified: number
  cached_at?: number
}

function signalColor(signal?: string): string {
  if (!signal) return '#ffab00'
  if (signal.includes('BUY')) return '#00e676'
  if (signal.includes('SELL')) return '#ff1744'
  return '#ffab00'
}

function rsiColor(rsi?: number): string {
  if (rsi == null) return '#475569'
  if (rsi < 30) return '#00e676'
  if (rsi > 70) return '#ff1744'
  return '#ffab00'
}

function cacheAge(ts?: number): string {
  if (!ts) return ''
  const mins = Math.floor((Date.now() / 1000 - ts) / 60)
  if (mins < 1) return 'just now'
  return `${mins}m ago`
}


type SortKey = 'combined_score' | 'vf_score' | 'price' | 'confidence' | 'rsi' | 'analyst_upside'

export default function PennyStocks() {
  const [refreshKey, setRefreshKey] = useState(0)
  const [refreshing, setRefreshing] = useState(false)
  const [sortKey, setSortKey] = useState<SortKey>('combined_score')
  const [sortAsc, setSortAsc] = useState(false)
  const [filterCat, setFilterCat] = useState<string>('All')
  const [addedTop10, setAddedTop10] = useState(false)

  const { data, isLoading, isError } = useQuery<PennyStocksResponse>({
    queryKey: ['penny-stocks', refreshKey],
    queryFn: () => pennyStocksApi.get(),
    staleTime: 25 * 60_000,
    retry: 1,
  })

  async function handleRefresh() {
    setRefreshing(true)
    try { await pennyStocksApi.refresh() } catch (_) {}
    setRefreshKey(k => k + 1)
    setRefreshing(false)
  }

  function toggleSort(key: SortKey) {
    if (sortKey === key) setSortAsc(a => !a)
    else { setSortKey(key); setSortAsc(false) }
  }

  const categories = ['All', ...Array.from(new Set((data?.stocks ?? []).map(s => s.penny_category ?? 'Other')))]

  const stocks = [...(data?.stocks ?? [])]
    .filter(s => filterCat === 'All' || s.penny_category === filterCat)
    .sort((a, b) => {
      const av = (a[sortKey] as number) ?? 0
      const bv = (b[sortKey] as number) ?? 0
      return sortAsc ? av - bv : bv - av
    })

  function SortTh({ col, label }: { col: SortKey; label: string }) {
    const active = sortKey === col
    return (
      <th
        onClick={() => toggleSort(col)}
        className="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wider cursor-pointer whitespace-nowrap select-none"
        style={{ color: active ? '#00d4ff' : '#94a3b8' }}
      >
        {label}{active ? (sortAsc ? ' ↑' : ' ↓') : ''}
      </th>
    )
  }

  return (
    <PageWrapper>
      <div className="flex flex-col gap-5">

        {/* Header */}
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold flex items-center gap-2" style={{ color: '#e2e8f0' }}>
              <TrendingUp className="w-5 h-5" style={{ color: '#ffab00' }} />
              Penny Stock Buy List
            </h1>
            <p className="text-sm mt-0.5" style={{ color: '#94a3b8' }}>
              Top 30 qualified BUY signals under $5 — scanned from {data?.total_scanned ?? '…'} candidates
            </p>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            {data?.cached_at && (
              <span className="text-xs" style={{ color: '#475569' }}>Updated {cacheAge(data.cached_at)}</span>
            )}
            {stocks.length > 0 && (
              <button
                onClick={() => {
                  stocks.slice(0, 10).forEach(s => addToWatchlist(s.ticker))
                  setAddedTop10(true)
                  setTimeout(() => setAddedTop10(false), 3000)
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
                style={{ backgroundColor: addedTop10 ? '#00e67615' : '#1a2235', color: addedTop10 ? '#00e676' : '#94a3b8', border: `1px solid ${addedTop10 ? 'rgba(0,230,118,0.3)' : 'rgba(255,255,255,0.06)'}` }}>
                {addedTop10 ? <Check className="w-3 h-3" /> : <BookmarkPlus className="w-3 h-3" />}
                {addedTop10 ? 'Added to Watchlist' : 'Add Top 10 to Watchlist'}
              </button>
            )}
            <button
              onClick={handleRefresh}
              disabled={refreshing || isLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold disabled:opacity-40"
              style={{ backgroundColor: '#1a2235', color: '#00d4ff', border: '1px solid rgba(0,212,255,0.2)' }}
            >
              <RefreshCw className={`w-3 h-3 ${refreshing ? 'animate-spin' : ''}`} />
              {refreshing ? 'Scanning…' : 'Refresh'}
            </button>
          </div>
        </div>

        {/* Risk warning */}
        <div
          className="rounded-xl border p-4 flex items-start gap-3"
          style={{ backgroundColor: 'rgba(255,171,0,0.06)', borderColor: 'rgba(255,171,0,0.25)' }}
        >
          <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" style={{ color: '#ffab00' }} />
          <p className="text-xs leading-relaxed" style={{ color: '#94a3b8' }}>
            <span className="font-semibold" style={{ color: '#ffab00' }}>High Risk — </span>
            Penny stocks carry significant price volatility, liquidity risk, and higher probability of loss. These signals are for informational purposes only and are not financial advice. Position size appropriately and always use the stop-loss levels shown.
          </p>
        </div>

        {/* Stats strip */}
        {data && (
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'Scanned', value: String(data.total_scanned) },
              { label: 'Qualified Buys', value: String(data.total_qualified) },
              { label: 'Showing', value: String(stocks.length) },
            ].map(({ label, value }) => (
              <div key={label} className="rounded-xl p-3 border text-center" style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
                <div className="text-xs" style={{ color: '#475569' }}>{label}</div>
                <div className="text-lg font-bold" style={{ color: '#e2e8f0' }}>{value}</div>
              </div>
            ))}
          </div>
        )}

        {isLoading && (
          <div className="rounded-xl border p-16 flex flex-col items-center gap-3" style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
            <Loader2 className="w-8 h-8 animate-spin" style={{ color: '#ffab00' }} />
            <p className="text-sm" style={{ color: '#94a3b8' }}>Scanning {(data as PennyStocksResponse | undefined)?.total_scanned ?? 150}+ penny stocks for buy signals…</p>
            <p className="text-xs" style={{ color: '#475569' }}>This takes 2–3 minutes on first load</p>
          </div>
        )}

        {isError && (
          <div className="rounded-xl border p-5" style={{ backgroundColor: 'rgba(255,23,68,0.05)', borderColor: 'rgba(255,23,68,0.2)' }}>
            <p className="text-sm" style={{ color: '#ff1744' }}>Scan failed. Check backend and retry.</p>
          </div>
        )}

        {data && stocks.length === 0 && !isLoading && (
          <div className="rounded-xl border p-12 text-center" style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
            <p className="text-sm" style={{ color: '#475569' }}>No qualifying buy signals found in current market conditions.</p>
          </div>
        )}

        {/* Category filter */}
        {data && data.stocks.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {categories.map(cat => (
              <button
                key={cat}
                onClick={() => setFilterCat(cat)}
                className="px-3 py-1 rounded-full text-xs font-semibold transition-colors"
                style={{
                  backgroundColor: filterCat === cat ? '#ffab00' : '#1a2235',
                  color: filterCat === cat ? '#0a0e1a' : '#94a3b8',
                  border: '1px solid rgba(255,255,255,0.06)',
                }}
              >
                {cat}
              </button>
            ))}
          </div>
        )}

        {/* Table */}
        {stocks.length > 0 && (
          <div className="rounded-xl border overflow-hidden" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
            <div className="overflow-x-auto">
              <table className="w-full text-sm min-w-[1100px]">
                <thead>
                  <tr style={{ backgroundColor: '#1a2235' }}>
                    <th className="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: '#94a3b8' }}>#</th>
                    <th className="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: '#94a3b8' }}>Ticker</th>
                    <th className="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: '#94a3b8' }}>Category</th>
                    <SortTh col="price" label="Price" />
                    <SortTh col="vf_score" label="VF Score" />
                    <SortTh col="combined_score" label="Score" />
                    <SortTh col="confidence" label="Confidence" />
                    <SortTh col="rsi" label="RSI" />
                    <th className="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wider whitespace-nowrap" style={{ color: '#94a3b8' }}>Signal</th>
                    <th className="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wider whitespace-nowrap" style={{ color: '#94a3b8' }}>Stop Loss</th>
                    <th className="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wider whitespace-nowrap" style={{ color: '#94a3b8' }}>TP1</th>
                    <SortTh col="analyst_upside" label="Analyst %" />
                    <th className="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: '#94a3b8' }}>Why Buy</th>
                  </tr>
                </thead>
                <tbody>
                  {stocks.map((s, i) => {
                    const sc = signalColor(s.signal)
                    const rc = rsiColor(s.rsi)
                    const upside = s.tp1 && s.price ? ((s.tp1 - s.price) / s.price * 100) : null
                    return (
                      <tr
                        key={s.ticker}
                        className="border-t hover:bg-white/[0.02] transition-colors"
                        style={{ borderColor: 'rgba(255,255,255,0.04)' }}
                      >
                        <td className="px-3 py-3 text-xs tabular-nums" style={{ color: '#475569' }}>{i + 1}</td>
                        <td className="px-3 py-3">
                          <a
                            href={`/analysis?ticker=${s.ticker}`}
                            className="font-bold font-mono text-xs px-2 py-0.5 rounded hover:opacity-80"
                            style={{ color: '#ffab00', backgroundColor: 'rgba(255,171,0,0.12)' }}
                          >
                            {s.ticker}
                          </a>
                        </td>
                        <td className="px-3 py-3 text-xs" style={{ color: '#94a3b8' }}>{s.penny_category ?? s.sector ?? '—'}</td>
                        <td className="px-3 py-3 text-xs font-bold tabular-nums" style={{ color: '#ffab00' }}>{fmt.price(s.price)}</td>
                        <td className="px-3 py-3 text-xs font-bold" style={{ color: scoreColor(s.vf_score ?? 0) }}>{s.vf_score ?? '—'}</td>
                        <td className="px-3 py-3 text-xs font-bold" style={{ color: '#00d4ff' }}>{s.combined_score?.toFixed(1) ?? '—'}</td>
                        <td className="px-3 py-3">
                          {s.confidence != null ? (
                            <div className="flex items-center gap-2">
                              <div className="w-14 h-1.5 rounded-full" style={{ backgroundColor: '#1a2235' }}>
                                <div className="h-1.5 rounded-full" style={{ width: `${s.confidence}%`, backgroundColor: sc }} />
                              </div>
                              <span className="text-xs tabular-nums" style={{ color: '#94a3b8' }}>{s.confidence}%</span>
                            </div>
                          ) : '—'}
                        </td>
                        <td className="px-3 py-3 text-xs tabular-nums font-semibold" style={{ color: rc }}>
                          {s.rsi?.toFixed(1) ?? '—'}
                          {s.rsi_signal && <span className="ml-1 font-normal text-xs" style={{ color: '#475569' }}>{s.rsi_signal}</span>}
                        </td>
                        <td className="px-3 py-3">
                          {s.signal ? (
                            <span className="text-xs font-bold px-2 py-0.5 rounded whitespace-nowrap" style={{ color: sc, backgroundColor: `${sc}18` }}>
                              {s.signal}
                            </span>
                          ) : '—'}
                        </td>
                        <td className="px-3 py-3 text-xs tabular-nums font-semibold" style={{ color: '#ff1744' }}>{fmt.price(s.stop_loss)}</td>
                        <td className="px-3 py-3 text-xs tabular-nums font-semibold" style={{ color: '#00e676' }}>
                          {fmt.price(s.tp1)}
                          {upside != null && (
                            <span className="ml-1 font-normal" style={{ color: '#475569' }}>({upside.toFixed(0)}%)</span>
                          )}
                        </td>
                        <td className="px-3 py-3 text-xs tabular-nums" style={{ color: s.analyst_upside != null && s.analyst_upside > 0 ? '#00e676' : '#ff1744' }}>
                          {s.analyst_upside != null ? `${s.analyst_upside > 0 ? '+' : ''}${s.analyst_upside.toFixed(0)}%` : '—'}
                        </td>
                        <td className="px-3 py-3 text-xs max-w-[200px]" style={{ color: '#94a3b8' }}>{s.why_now ?? '—'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </PageWrapper>
  )
}
