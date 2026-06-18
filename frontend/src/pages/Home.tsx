import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Search, BarChart2, Filter, Zap, Target,
  TrendingUp, TrendingDown, Briefcase, FileText, Clock, Activity
} from 'lucide-react'
import { marketPulseApi, opportunitiesApi } from '../services/api'
import { fmt, scoreColor, changeColor } from '../lib/formatters'
import PageWrapper from '../components/layout/PageWrapper'
import DailyDrivers from '../components/dashboard/DailyDrivers'

// ── Recently-analyzed ticker persistence ─────────────────────────────────────
const RECENT_KEY = 'vf_recent_tickers'
export function addRecentTicker(ticker: string) {
  try {
    const raw = localStorage.getItem(RECENT_KEY)
    const list: string[] = raw ? JSON.parse(raw) : []
    const updated = [ticker, ...list.filter(t => t !== ticker)].slice(0, 8)
    localStorage.setItem(RECENT_KEY, JSON.stringify(updated))
  } catch { /* ignore */ }
}
function getRecentTickers(): string[] {
  try {
    const raw = localStorage.getItem(RECENT_KEY)
    return raw ? JSON.parse(raw) : []
  } catch { return [] }
}

// ── Types ─────────────────────────────────────────────────────────────────────
interface IndexQuote { label: string; price?: number; change_pct?: number; up: boolean }
interface SectorPerf { sector: string; change_pct?: number; up: boolean }
interface MarketPulse { indices: IndexQuote[]; sectors: SectorPerf[]; market_breadth?: string }

interface ScannedStock {
  ticker: string; name?: string; price?: number
  vf_score: number; signal?: string; confidence?: number
  analyst_upside?: number; tp1?: number; stop_loss?: number
  why_now: string; combined_score: number
}
interface OpportunitiesData {
  top_picks: ScannedStock[]; total_scanned: number; passed_count: number
  buy_count: number; hold_count: number; sell_count: number; avg_vf_score: number
}

// ── Sub-components ────────────────────────────────────────────────────────────
function IndexTicker({ q }: { q: IndexQuote }) {
  return (
    <div className="flex items-center gap-3 shrink-0">
      <span className="text-xs" style={{ color: '#475569' }}>{q.label}</span>
      <span className="text-sm font-semibold tabular-nums" style={{ color: '#e2e8f0' }}>
        {q.price != null ? (q.price > 1000 ? q.price.toLocaleString('en-US', { maximumFractionDigits: 0 }) : fmt.price(q.price)) : '—'}
      </span>
      {q.change_pct != null && (
        <span className="text-xs font-semibold flex items-center gap-0.5" style={{ color: changeColor(q.change_pct) }}>
          {q.up ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
          {q.change_pct > 0 ? '+' : ''}{q.change_pct.toFixed(2)}%
        </span>
      )}
    </div>
  )
}

function SentimentPanel({ data }: { data: OpportunitiesData }) {
  const bullPct = Math.round((data.buy_count / Math.max(data.total_scanned, 1)) * 100)
  const sentiment = bullPct > 50 ? 'Risk-On' : bullPct > 35 ? 'Neutral' : 'Risk-Off'
  const sentColor = bullPct > 50 ? '#00e676' : bullPct > 35 ? '#ffab00' : '#ff1744'

  const pills = [
    { label: 'Sentiment', value: sentiment, color: sentColor },
    { label: 'Stocks Scanned', value: String(data.total_scanned), color: '#00d4ff' },
    { label: 'High-Quality', value: String(data.passed_count), color: '#e2e8f0' },
    { label: 'Avg VF Score', value: String(data.avg_vf_score), color: scoreColor(data.avg_vf_score) },
    { label: 'Buy Signals', value: String(data.buy_count), color: '#00e676' },
    { label: 'Sell Signals', value: String(data.sell_count), color: '#ff1744' },
  ]

  return (
    <div
      className="rounded-xl border p-4 grid grid-cols-3 sm:grid-cols-6 gap-3"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
    >
      {pills.map(p => (
        <div key={p.label} className="text-center">
          <div className="text-xs mb-1" style={{ color: '#475569' }}>{p.label}</div>
          <div className="text-lg font-black" style={{ color: p.color }}>{p.value}</div>
        </div>
      ))}
    </div>
  )
}

function SectorGrid({ sectors }: { sectors: SectorPerf[] }) {
  const sorted = [...sectors].sort((a, b) => (b.change_pct ?? -99) - (a.change_pct ?? -99))
  return (
    <div className="rounded-xl border overflow-hidden" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
      <div className="px-4 py-2.5 border-b flex items-center gap-2" style={{ backgroundColor: '#1a2235', borderColor: 'rgba(255,255,255,0.06)' }}>
        <Activity className="w-3.5 h-3.5" style={{ color: '#00d4ff' }} />
        <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: '#94a3b8' }}>Sector Performance</span>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-0">
        {sorted.map((s, i) => (
          <div
            key={s.sector}
            className="flex items-center justify-between px-3 py-2.5 border-r border-b"
            style={{ borderColor: 'rgba(255,255,255,0.04)', backgroundColor: i === 0 ? '#00e67606' : i === sorted.length - 1 ? '#ff174406' : 'transparent' }}
          >
            <span className="text-xs" style={{ color: '#94a3b8' }}>{s.sector}</span>
            <span className="text-xs font-semibold tabular-nums" style={{ color: s.change_pct != null ? changeColor(s.change_pct) : '#475569' }}>
              {s.change_pct != null ? (s.change_pct > 0 ? '+' : '') + s.change_pct.toFixed(2) + '%' : '—'}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function TopPickMini({ stock, rank }: { stock: ScannedStock; rank: number }) {
  const navigate = useNavigate()
  const sig = stock.signal || ''
  const sigCol = sig.includes('BUY') ? '#00e676' : sig.includes('SELL') ? '#ff1744' : '#ffab00'
  const medals = ['🥇', '🥈', '🥉']

  return (
    <button
      onClick={() => navigate(`/analysis?ticker=${stock.ticker}`)}
      className="rounded-xl border p-4 text-left flex flex-col gap-3 hover:border-white/10 transition-all w-full"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs">{medals[rank]}</span>
          <span className="font-black font-mono text-sm" style={{ color: '#00d4ff' }}>{stock.ticker}</span>
        </div>
        <span className="text-xl font-black" style={{ color: scoreColor(stock.vf_score) }}>{stock.vf_score}</span>
      </div>
      <div className="text-xs truncate" style={{ color: '#475569' }}>{stock.name}</div>
      <div className="flex items-center gap-2">
        <span className="text-xs font-bold px-2 py-0.5 rounded" style={{ color: sigCol, backgroundColor: `${sigCol}15` }}>
          {sig}
        </span>
        {stock.confidence != null && (
          <span className="text-xs" style={{ color: '#475569' }}>{stock.confidence}%</span>
        )}
      </div>
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span style={{ color: '#475569' }}>Price </span>
          <span className="font-semibold" style={{ color: '#e2e8f0' }}>{fmt.price(stock.price)}</span>
        </div>
        <div>
          <span style={{ color: '#475569' }}>Upside </span>
          <span className="font-semibold" style={{ color: '#00e676' }}>
            {stock.analyst_upside != null ? (stock.analyst_upside > 0 ? '+' : '') + stock.analyst_upside.toFixed(1) + '%' : '—'}
          </span>
        </div>
        <div>
          <span style={{ color: '#475569' }}>SL </span>
          <span className="font-semibold" style={{ color: '#ff1744' }}>{fmt.price(stock.stop_loss)}</span>
        </div>
        <div>
          <span style={{ color: '#475569' }}>TP1 </span>
          <span className="font-semibold" style={{ color: '#00e676' }}>{fmt.price(stock.tp1)}</span>
        </div>
      </div>
      <p className="text-xs leading-relaxed" style={{ color: '#475569' }}>{stock.why_now}</p>
    </button>
  )
}

const NAV_SHORTCUTS = [
  { icon: BarChart2, label: 'Deep Analysis', sub: 'Single stock deep dive', to: '/analysis', color: '#00d4ff' },
  { icon: Zap,       label: 'Radar',         sub: 'Live market intelligence', to: '/radar', color: '#ffd700' },
  { icon: Briefcase, label: 'Portfolio',     sub: 'Holdings analysis + signals', to: '/portfolio', color: '#a78bfa' },
  { icon: FileText,  label: 'Reports',       sub: 'Generate PDF reports', to: '/reports', color: '#94a3b8' },
]

// ── Main dashboard ─────────────────────────────────────────────────────────────
export default function Home() {
  const [ticker, setTicker] = useState('')
  const navigate = useNavigate()
  const recent = getRecentTickers()

  const { data: pulse } = useQuery<MarketPulse>({
    queryKey: ['market-pulse'],
    queryFn: () => marketPulseApi.get(),
    staleTime: 2 * 60_000,
    refetchInterval: 2 * 60_000,
    retry: 1,
  })

  const { data: opps } = useQuery<OpportunitiesData>({
    queryKey: ['opportunities'],
    queryFn: () => opportunitiesApi.get(),
    staleTime: 10 * 60_000,
    retry: 1,
  })

  const handleSearch = (e: FormEvent) => {
    e.preventDefault()
    const t = ticker.trim().toUpperCase()
    if (t) navigate(`/analysis?ticker=${t}`)
  }

  return (
    <PageWrapper>
      <div className="flex flex-col gap-6">

        {/* Header + search */}
        <div className="flex flex-col gap-4 pt-4">
          <div>
            <h1 className="text-2xl font-black" style={{ color: '#e2e8f0' }}>Market Dashboard</h1>
            <p className="text-sm mt-0.5" style={{ color: '#475569' }}>
              Live market intelligence · VF scoring · Trading signals
              {pulse?.market_breadth && (
                <span className="ml-3 px-2 py-0.5 rounded text-xs font-semibold" style={{ backgroundColor: '#00d4ff10', color: '#00d4ff' }}>
                  {pulse.market_breadth}
                </span>
              )}
            </p>
          </div>

          <form onSubmit={handleSearch} className="flex gap-2 max-w-2xl">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: '#475569' }} />
              <input
                type="text"
                value={ticker}
                onChange={e => setTicker(e.target.value)}
                placeholder="Search ticker or company name…"
                className="w-full pl-9 pr-4 py-2.5 rounded-xl text-sm outline-none"
                style={{ backgroundColor: '#111827', border: '1px solid rgba(255,255,255,0.08)', color: '#e2e8f0' }}
                data-testid="ticker-search"
              />
            </div>
            <button
              type="submit"
              className="px-5 py-2.5 rounded-xl text-sm font-semibold"
              style={{ background: 'linear-gradient(135deg, #00d4ff, #0088cc)', color: '#0a0e1a' }}
              data-testid="search-btn"
            >
              Analyze
            </button>
          </form>

          {recent.length > 0 && (
            <div className="flex items-center gap-2 flex-wrap">
              <Clock className="w-3.5 h-3.5 shrink-0" style={{ color: '#475569' }} />
              <span className="text-xs" style={{ color: '#475569' }}>Recent:</span>
              {recent.map(t => (
                <button
                  key={t}
                  onClick={() => navigate(`/analysis?ticker=${t}`)}
                  className="text-xs font-mono font-semibold px-2 py-0.5 rounded hover:opacity-80"
                  style={{ backgroundColor: '#111827', color: '#00d4ff', border: '1px solid rgba(0,212,255,0.2)' }}
                >
                  {t}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Live index strip */}
        {pulse?.indices && pulse.indices.length > 0 && (
          <div
            className="rounded-xl border p-4 overflow-x-auto"
            style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
          >
            <div className="flex items-center gap-6 min-w-max">
              <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: '#475569' }}>Markets</span>
              {pulse.indices.map(q => (
                <IndexTicker key={q.label} q={q} />
              ))}
            </div>
          </div>
        )}

        {/* Top 3 daily market drivers — AI-ranked */}
        <DailyDrivers />

        {/* Market sentiment from opportunities scan */}
        {opps && <SentimentPanel data={opps} />}

        {/* Sector performance */}
        {pulse?.sectors && pulse.sectors.length > 0 && (
          <SectorGrid sectors={pulse.sectors} />
        )}

        {/* Top conviction picks */}
        {opps && opps.top_picks.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Target className="w-4 h-4" style={{ color: '#ffd700' }} />
              <h2 className="text-sm font-bold uppercase tracking-wide" style={{ color: '#e2e8f0' }}>
                Top Conviction Picks
              </h2>
              <a href="/opportunities" className="text-xs ml-auto" style={{ color: '#00d4ff' }}>
                View all {opps.passed_count} ideas →
              </a>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {opps.top_picks.slice(0, 3).map((s, i) => (
                <TopPickMini key={s.ticker} stock={s} rank={i} />
              ))}
            </div>
          </div>
        )}

        {/* Navigation shortcuts */}
        <div>
          <h2 className="text-xs font-semibold uppercase tracking-wide mb-3" style={{ color: '#475569' }}>
            Quick Access
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {NAV_SHORTCUTS.map(({ icon: Icon, label, sub, to, color }) => (
              <button
                key={to + label}
                onClick={() => navigate(to)}
                className="rounded-xl border p-4 text-left hover:border-white/10 transition-all group"
                style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
              >
                <div
                  className="w-8 h-8 rounded-lg flex items-center justify-center mb-3"
                  style={{ backgroundColor: `${color}20` }}
                >
                  <Icon className="w-4 h-4" style={{ color }} />
                </div>
                <div className="text-xs font-semibold mb-0.5" style={{ color: '#e2e8f0' }}>{label}</div>
                <div className="text-xs" style={{ color: '#475569' }}>{sub}</div>
              </button>
            ))}
          </div>
        </div>

      </div>
    </PageWrapper>
  )
}
