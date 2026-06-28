import { useState, useCallback, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Bookmark, X, RefreshCw, TrendingUp, TrendingDown, Info } from 'lucide-react'
import { watchlistApi } from '../services/api'
import { fmt, scoreColor, changeColor } from '../lib/formatters'
import PageWrapper from '../components/layout/PageWrapper'
import {
  getWatchlist, addToWatchlist, removeFromWatchlist,
  getPortfolio, removeFromPortfolio, seedPortfolioIfEmpty,
  type PortfolioEntry,
} from '../lib/watchlist'

// Re-export so other pages can import from here (backwards compat)
export { addToWatchlist, removeFromWatchlist, getWatchlist, isInWatchlist } from '../lib/watchlist'

// ── Types ─────────────────────────────────────────────────────────────────────

interface ScannedStock {
  ticker: string
  name?: string
  price?: number
  vf_score: number
  signal?: string
  confidence?: number
  rsi?: number
  rsi_signal?: string
  stop_loss?: number
  tp1?: number
  combined_score: number
  why_now: string
  analyst_upside?: number
  week52_momentum?: number
}

interface WatchlistSignalsResponse {
  signals: ScannedStock[]
  failed: string[]
}

type Tab = 'watching' | 'portfolio'

// ── Helpers ───────────────────────────────────────────────────────────────────

function signalColor(s?: string) {
  if (!s) return '#94a3b8'
  if (s.includes('BUY')) return '#00e676'
  if (s.includes('SELL')) return '#ff1744'
  return '#ffab00'
}

function horizonLabel(s: ScannedStock): { label: string; color: string } {
  const technical = s.rsi_signal === 'Oversold' || s.rsi_signal === 'Overbought'
  const fundamental = s.vf_score >= 65
  if (technical && fundamental) return { label: 'Multi-horizon', color: '#ffd700' }
  if (technical) return { label: 'Short-term', color: '#00d4ff' }
  return { label: 'Long-term', color: '#a855f7' }
}

// ── Sub-components ────────────────────────────────────────────────────────────

function MomentumBar({ value }: { value?: number }) {
  if (value == null) return <span style={{ color: '#475569' }}>—</span>
  const color = value < 30 ? '#ff1744' : value > 70 ? '#00e676' : '#ffab00'
  return (
    <div className="flex items-center gap-1.5">
      <div className="w-14 rounded-full h-1.5 shrink-0" style={{ backgroundColor: 'rgba(255,255,255,0.1)' }}>
        <div className="h-1.5 rounded-full" style={{ width: `${value}%`, backgroundColor: color }} />
      </div>
      <span className="text-xs tabular-nums" style={{ color }}>{value.toFixed(0)}%</span>
    </div>
  )
}

function ConfidenceBar({ value, sig }: { value?: number; sig?: string }) {
  if (value == null) return <span style={{ color: '#475569' }}>—</span>
  const col = signalColor(sig)
  return (
    <div className="flex items-center gap-1.5">
      <div className="w-14 rounded-full h-1.5 shrink-0" style={{ backgroundColor: 'rgba(255,255,255,0.1)' }}>
        <div className="h-1.5 rounded-full" style={{ width: `${value}%`, backgroundColor: col }} />
      </div>
      <span className="text-xs tabular-nums" style={{ color: '#94a3b8' }}>{value}%</span>
    </div>
  )
}

function SkeletonRow({ cols }: { cols: number }) {
  return (
    <tr className="border-t" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
      {Array.from({ length: cols }).map((_, i) => (
        <td key={i} className="px-3 py-3">
          <div className="h-3 rounded" style={{
            backgroundColor: 'rgba(255,255,255,0.07)',
            width: i === 1 ? '120px' : i === 0 ? '60px' : '50px',
            animation: 'pulse 1.5s ease-in-out infinite',
          }} />
        </td>
      ))}
    </tr>
  )
}

function SignalExplainer({ onDismiss }: { onDismiss: () => void }) {
  return (
    <div className="rounded-xl border p-3 flex gap-3 items-start"
      style={{ backgroundColor: '#0d1521', borderColor: 'rgba(0,212,255,0.15)' }}>
      <Info className="w-4 h-4 mt-0.5 shrink-0" style={{ color: '#00d4ff' }} />
      <div className="flex-1 flex flex-col gap-1.5">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-2 py-0.5 rounded" style={{ backgroundColor: '#00d4ff15', color: '#00d4ff' }}>Short-term</span>
          <span className="text-xs" style={{ color: '#94a3b8' }}>Days to weeks — driven by RSI momentum and MACD crossover. Acts on price action, suits active traders.</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-2 py-0.5 rounded" style={{ backgroundColor: '#a855f715', color: '#a855f7' }}>Long-term</span>
          <span className="text-xs" style={{ color: '#94a3b8' }}>Weeks to months — driven by VF fundamental score (≥65) and analyst consensus. Suits investors building positions.</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-2 py-0.5 rounded" style={{ backgroundColor: '#ffd70015', color: '#ffd700' }}>Multi-horizon</span>
          <span className="text-xs" style={{ color: '#94a3b8' }}>Both signals aligned — strongest conviction. Technical entry with fundamental backing.</span>
        </div>
      </div>
      <button onClick={onDismiss} className="shrink-0" style={{ color: '#334155' }}><X className="w-3.5 h-3.5" /></button>
    </div>
  )
}

// ── Stock table ───────────────────────────────────────────────────────────────

interface StockTableProps {
  tickers: string[]
  signalMap: Map<string, ScannedStock>
  isLoading: boolean
  showShares?: boolean
  sharesMap?: Map<string, number>
  onRemove: (ticker: string) => void
}

function StockTable({ tickers, signalMap, isLoading, showShares, sharesMap, onRemove }: StockTableProps) {
  const navigate = useNavigate()
  const cols = showShares ? 14 : 13

  const headers = [
    'Ticker', 'Name', ...(showShares ? ['Shares'] : []), 'Price', 'VF Score',
    'Signal', 'Confidence', 'RSI', 'RSI Signal', 'Stop Loss', 'TP1',
    'Upside %', '52W Momentum', 'Horizon', '',
  ]

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm" style={{ minWidth: showShares ? '1350px' : '1300px' }} data-testid="watchlist-table">
        <thead>
          <tr style={{ backgroundColor: '#1a2235' }}>
            {headers.map(h => (
              <th key={h} className="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wider whitespace-nowrap" style={{ color: '#94a3b8' }}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {isLoading
            ? Array.from({ length: tickers.length || 3 }).map((_, i) => <SkeletonRow key={i} cols={cols} />)
            : tickers.map(ticker => {
                const s = signalMap.get(ticker)
                const sig = s?.signal
                const sigCol = signalColor(sig)
                const rsiColor = s?.rsi != null
                  ? (s.rsi < 40 ? '#00e676' : s.rsi > 65 ? '#ff1744' : '#e2e8f0')
                  : '#94a3b8'
                const horizon = s ? horizonLabel(s) : null
                const shares = sharesMap?.get(ticker)

                return (
                  <tr key={ticker} className="border-t hover:bg-white/[0.02]"
                    style={{ borderColor: 'rgba(255,255,255,0.04)' }}
                    data-testid={`watchlist-row-${ticker}`}>

                    <td className="px-3 py-3">
                      <button onClick={() => navigate(`/analysis?ticker=${ticker}`)}
                        className="font-bold font-mono text-xs px-2 py-0.5 rounded hover:opacity-80 transition-opacity"
                        style={{ color: '#00d4ff', backgroundColor: '#00d4ff15' }}>
                        {ticker}
                      </button>
                    </td>

                    <td className="px-3 py-3 text-xs max-w-[140px] truncate" style={{ color: '#94a3b8' }}>
                      {s?.name ?? (isLoading ? '—' : <span style={{ color: '#334155' }}>No data</span>)}
                    </td>

                    {showShares && (
                      <td className="px-3 py-3 text-xs tabular-nums font-semibold" style={{ color: '#64748b' }}>
                        {shares != null ? shares.toLocaleString(undefined, { maximumFractionDigits: 4 }) : '—'}
                      </td>
                    )}

                    <td className="px-3 py-3 text-xs tabular-nums font-semibold" style={{ color: '#e2e8f0' }}>
                      {s ? fmt.price(s.price) : '—'}
                    </td>

                    <td className="px-3 py-3 text-xs font-black tabular-nums" style={{ color: s ? scoreColor(s.vf_score) : '#475569' }}>
                      {s ? s.vf_score : '—'}
                    </td>

                    <td className="px-3 py-3">
                      {sig
                        ? <span className="text-xs font-bold px-2 py-0.5 rounded whitespace-nowrap"
                            style={{ color: sigCol, backgroundColor: `${sigCol}15` }}>{sig}</span>
                        : <span style={{ color: '#475569' }}>—</span>}
                    </td>

                    <td className="px-3 py-3"><ConfidenceBar value={s?.confidence} sig={s?.signal} /></td>

                    <td className="px-3 py-3 text-xs tabular-nums" style={{ color: rsiColor }}>
                      {s?.rsi != null ? s.rsi.toFixed(1) : '—'}
                    </td>

                    <td className="px-3 py-3 text-xs whitespace-nowrap" style={{ color: '#94a3b8' }}>
                      {s?.rsi_signal ?? '—'}
                    </td>

                    <td className="px-3 py-3 text-xs tabular-nums" style={{ color: '#ff1744' }}>
                      {s ? fmt.price(s.stop_loss) : '—'}
                    </td>

                    <td className="px-3 py-3 text-xs tabular-nums" style={{ color: '#00e676' }}>
                      {s ? fmt.price(s.tp1) : '—'}
                    </td>

                    <td className="px-3 py-3 text-xs tabular-nums font-semibold"
                      style={{ color: s?.analyst_upside != null ? changeColor(s.analyst_upside) : '#475569' }}>
                      {s?.analyst_upside != null
                        ? (s.analyst_upside > 0 ? '+' : '') + s.analyst_upside.toFixed(1) + '%'
                        : '—'}
                    </td>

                    <td className="px-3 py-3"><MomentumBar value={s?.week52_momentum} /></td>

                    <td className="px-3 py-3">
                      {horizon
                        ? <span className="text-xs font-semibold px-2 py-0.5 rounded whitespace-nowrap"
                            style={{ color: horizon.color, backgroundColor: `${horizon.color}15` }}>
                            {horizon.label}
                          </span>
                        : <span style={{ color: '#334155' }}>—</span>}
                    </td>

                    <td className="px-3 py-3">
                      <button onClick={() => onRemove(ticker)}
                        className="flex items-center justify-center w-6 h-6 rounded hover:bg-red-500/10"
                        style={{ color: '#475569' }} aria-label={`Remove ${ticker}`}
                        data-testid={`remove-${ticker}`}>
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                )
              })}
        </tbody>
      </table>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function Watchlist() {
  // Seed portfolio on first visit
  seedPortfolioIfEmpty()

  const [activeTab, setActiveTab] = useState<Tab>('watching')
  const [showExplainer, setShowExplainer] = useState(true)

  // Watching tab state
  const [tickers, setTickers] = useState<string[]>(() => getWatchlist())
  const [input, setInput] = useState('')
  const [inputError, setInputError] = useState('')
  const [refreshTrigger, setRefreshTrigger] = useState(0)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  // Portfolio tab state
  const [portfolio, setPortfolioState] = useState<PortfolioEntry[]>(() => getPortfolio())
  const [pfRefreshTrigger, setPfRefreshTrigger] = useState(0)

  const pfTickers = portfolio.map(e => e.ticker)

  const { data, isLoading, isFetching, isError } = useQuery<WatchlistSignalsResponse>({
    queryKey: ['watchlist-signals', tickers, refreshTrigger],
    queryFn: () => watchlistApi.signals(tickers),
    enabled: tickers.length > 0,
    staleTime: 2 * 60_000,
  })

  useEffect(() => {
    if (data) setLastUpdated(new Date())
  }, [data])

  const { data: pfData, isLoading: pfLoading, isFetching: pfFetching } = useQuery<WatchlistSignalsResponse>({
    queryKey: ['portfolio-signals', pfTickers, pfRefreshTrigger],
    queryFn: () => watchlistApi.signals(pfTickers),
    enabled: pfTickers.length > 0 && activeTab === 'portfolio',
    staleTime: 5 * 60_000,
  })

  const signalMap = new Map<string, ScannedStock>((data?.signals ?? []).map(s => [s.ticker, s]))
  const pfSignalMap = new Map<string, ScannedStock>((pfData?.signals ?? []).map(s => [s.ticker, s]))
  const sharesMap = new Map<string, number>(portfolio.map(e => [e.ticker, e.shares]))

  const lastUpdatedLabel = lastUpdated
    ? (() => {
        const mins = Math.floor((Date.now() - lastUpdated.getTime()) / 60_000)
        return mins < 1 ? 'just now' : `${mins}m ago`
      })()
    : null

  const handleAdd = useCallback(() => {
    const ticker = input.trim().toUpperCase()
    if (!ticker) return
    if (!/^[A-Z]{1,10}$/.test(ticker)) {
      setInputError('Ticker must be letters only (e.g. AAPL)')
      return
    }
    if (tickers.includes(ticker)) {
      setInputError(`${ticker} is already in your watchlist`)
      return
    }
    addToWatchlist(ticker)
    setTickers(prev => [...prev, ticker])
    setInput('')
    setInputError('')
  }, [input, tickers])

  const handleRemoveWatching = useCallback((ticker: string) => {
    removeFromWatchlist(ticker)
    setTickers(prev => prev.filter(t => t !== ticker))
  }, [])

  const handleRemovePortfolio = useCallback((ticker: string) => {
    removeFromPortfolio(ticker)
    setPortfolioState(prev => prev.filter(e => e.ticker !== ticker))
  }, [])

  const handleRefresh = useCallback(() => setRefreshTrigger(n => n + 1), [])
  const handlePfRefresh = useCallback(() => setPfRefreshTrigger(n => n + 1), [])

  const isSpinning = isLoading || isFetching
  const pfSpinning = pfLoading || pfFetching

  const activeTickers = activeTab === 'watching' ? tickers : pfTickers
  const activeSpinning = activeTab === 'watching' ? isSpinning : pfSpinning
  const activeRefresh = activeTab === 'watching' ? handleRefresh : handlePfRefresh

  return (
    <PageWrapper>
      <div className="flex flex-col gap-5">

        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Bookmark className="w-5 h-5" style={{ color: '#00d4ff' }} />
              <h1 className="text-2xl font-black" style={{ color: '#e2e8f0' }}>My Watchlist</h1>
            </div>
            <p className="text-sm" style={{ color: '#475569' }}>
              Track your stocks — signals update on demand
              {lastUpdatedLabel && activeTab === 'watching' && (
                <span className="ml-3" style={{ color: '#334155' }}>· Last updated: {lastUpdatedLabel}</span>
              )}
            </p>
          </div>
          {activeTickers.length > 0 && (
            <button onClick={activeRefresh} disabled={activeSpinning}
              className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-opacity disabled:opacity-40"
              style={{ backgroundColor: '#1a2235', border: '1px solid rgba(255,255,255,0.06)', color: '#94a3b8' }}
              data-testid="refresh-signals-btn">
              <RefreshCw className={`w-3 h-3 ${activeSpinning ? 'animate-spin' : ''}`} />
              {activeSpinning ? 'Loading…' : 'Refresh Signals'}
            </button>
          )}
        </div>

        {/* Signal explainer */}
        {showExplainer && <SignalExplainer onDismiss={() => setShowExplainer(false)} />}

        {/* Tabs */}
        <div className="flex items-center gap-1 border-b" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
          {(['watching', 'portfolio'] as Tab[]).map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)}
              className="px-4 py-2 text-sm font-semibold capitalize transition-colors border-b-2 -mb-px"
              style={{
                borderColor: activeTab === tab ? '#00d4ff' : 'transparent',
                color: activeTab === tab ? '#00d4ff' : '#475569',
              }}>
              {tab === 'watching' ? `Watching (${tickers.length})` : `Portfolio (${portfolio.length})`}
            </button>
          ))}
        </div>

        {/* Watching tab — add form */}
        {activeTab === 'watching' && (
          <div className="rounded-xl border p-4 flex flex-col gap-2"
            style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
            <div className="flex gap-2">
              <input type="text" value={input}
                onChange={e => { setInput(e.target.value.toUpperCase()); setInputError('') }}
                onKeyDown={e => e.key === 'Enter' && handleAdd()}
                placeholder="Enter ticker (e.g. AAPL, MSFT, NVDA)"
                className="flex-1 rounded-lg px-3 py-2 text-sm font-mono outline-none"
                style={{
                  backgroundColor: '#0a0e1a',
                  border: `1px solid ${inputError ? '#ff1744' : 'rgba(255,255,255,0.1)'}`,
                  color: '#e2e8f0',
                }}
                data-testid="watchlist-ticker-input" aria-label="Ticker symbol to add" />
              <button onClick={handleAdd}
                className="px-4 py-2 rounded-lg text-sm font-semibold hover:opacity-80"
                style={{ backgroundColor: '#00d4ff', color: '#0a0e1a' }}
                data-testid="watchlist-add-btn">
                Add
              </button>
            </div>
            {inputError && <p className="text-xs" style={{ color: '#ff1744' }} role="alert">{inputError}</p>}
          </div>
        )}

        {/* Error state */}
        {isError && activeTab === 'watching' && (
          <div className="rounded-xl border p-4"
            style={{ backgroundColor: 'rgba(255,23,68,0.05)', borderColor: 'rgba(255,23,68,0.2)' }}>
            <p className="text-sm" style={{ color: '#ff1744' }}>Unable to load signals. Check backend connection.</p>
          </div>
        )}

        {/* Failed tickers */}
        {activeTab === 'watching' && data?.failed && data.failed.length > 0 && (
          <div className="rounded-xl border p-3 flex flex-wrap gap-2 items-center"
            style={{ backgroundColor: 'rgba(255,171,0,0.05)', borderColor: 'rgba(255,171,0,0.2)' }}>
            <span className="text-xs font-semibold" style={{ color: '#ffab00' }}>Could not fetch signals for:</span>
            {data.failed.map(t => (
              <span key={t} className="text-xs font-mono px-2 py-0.5 rounded"
                style={{ backgroundColor: 'rgba(255,171,0,0.1)', color: '#ffab00' }}>{t}</span>
            ))}
          </div>
        )}

        {/* Portfolio failed tickers */}
        {activeTab === 'portfolio' && pfData?.failed && pfData.failed.length > 0 && (
          <div className="rounded-xl border p-3 flex flex-wrap gap-2 items-center"
            style={{ backgroundColor: 'rgba(255,171,0,0.05)', borderColor: 'rgba(255,171,0,0.2)' }}>
            <span className="text-xs font-semibold" style={{ color: '#ffab00' }}>Could not fetch signals for:</span>
            {pfData.failed.map(t => (
              <span key={t} className="text-xs font-mono px-2 py-0.5 rounded"
                style={{ backgroundColor: 'rgba(255,171,0,0.1)', color: '#ffab00' }}>{t}</span>
            ))}
          </div>
        )}

        {/* Empty state */}
        {activeTab === 'watching' && tickers.length === 0 && (
          <div className="flex flex-col items-center gap-3 py-20">
            <Bookmark className="w-10 h-10" style={{ color: '#1e2d40' }} />
            <p className="text-sm" style={{ color: '#475569' }}>Add tickers above to start tracking</p>
          </div>
        )}

        {/* Table */}
        {activeTickers.length > 0 && (
          <div className="rounded-xl border overflow-hidden" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
            {activeTab === 'watching' ? (
              <StockTable
                tickers={tickers}
                signalMap={signalMap}
                isLoading={isLoading}
                onRemove={handleRemoveWatching}
              />
            ) : (
              <StockTable
                tickers={pfTickers}
                signalMap={pfSignalMap}
                isLoading={pfLoading}
                showShares
                sharesMap={sharesMap}
                onRemove={handleRemovePortfolio}
              />
            )}

            {/* Summary footer */}
            {!activeSpinning && activeTickers.length > 0 && (
              <div className="flex items-center gap-4 px-4 py-2.5 text-xs"
                style={{ backgroundColor: '#0d1521', borderTop: '1px solid rgba(255,255,255,0.04)', color: '#334155' }}>
                <span>{activeTickers.length} ticker{activeTickers.length !== 1 ? 's' : ''} tracked</span>
                {(() => {
                  const activeData = activeTab === 'watching' ? data : pfData
                  return activeData ? (
                    <>
                      <span style={{ color: '#00e676' }}>
                        <TrendingUp className="w-3 h-3 inline mr-1" />
                        {activeData.signals.filter(s => s.signal?.includes('BUY')).length} BUY
                      </span>
                      <span style={{ color: '#ff1744' }}>
                        <TrendingDown className="w-3 h-3 inline mr-1" />
                        {activeData.signals.filter(s => s.signal?.includes('SELL')).length} SELL
                      </span>
                      <span style={{ color: '#ffab00' }}>
                        {activeData.signals.filter(s => s.signal?.includes('HOLD')).length} HOLD
                      </span>
                    </>
                  ) : null
                })()}
              </div>
            )}
          </div>
        )}
      </div>
    </PageWrapper>
  )
}
