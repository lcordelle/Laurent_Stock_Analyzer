import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { advancedApi } from '../services/api'
import { Loader2, Target, Shield, Zap, TrendingUp, TrendingDown, BarChart2, ChevronUp, ChevronDown, RefreshCw, BookmarkPlus, Check, Star } from 'lucide-react'
import { opportunitiesApi } from '../services/api'
import { fmt, scoreColor, changeColor } from '../lib/formatters'
import PageWrapper from '../components/layout/PageWrapper'
import { addToWatchlist } from '../lib/watchlist'

interface Theme {
  theme: string
  conviction: string
  thesis: string
  catalysts: string[]
  stocks: string[]
  timeframe: string
  risk: string
  opportunity_size: string
}

interface ScannedStock {
  ticker: string
  name?: string
  sector?: string
  price?: number
  vf_score: number
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
  roe?: number
  gross_margin?: number
  revenue_growth?: number
  market_cap?: number
  combined_score: number
  why_now: string
  conviction_tier: string
  score_drivers: string[]
  domain?: string
  has_recent_news?: boolean
  recent_news_count?: number
  analyst_target_age_days?: number
  volatility_annual?: number
  suggested_position_pct?: number
  signal_quality?: string
}

interface DomainStat {
  count: number
  avg_score: number
  buy_count: number
}

interface OpportunitiesData {
  themes: Theme[]
  top_picks: ScannedStock[]
  all_ideas: ScannedStock[]
  total_scanned: number
  passed_count: number
  buy_count: number
  hold_count: number
  sell_count: number
  avg_vf_score: number
  cached_at?: number
  domain_stats: Record<string, DomainStat>
}

function convictionColor(c: string) {
  if (c === 'HIGH') return '#00e676'
  if (c === 'MEDIUM') return '#ffab00'
  return '#94a3b8'
}

function convictionTierColor(tier: string): string {
  if (tier === 'STRONG BUY') return '#00e676'
  if (tier === 'BUY')         return '#69f0ae'
  if (tier === 'WATCH')       return '#ffab00'
  return '#ff1744'
}

function signalColor(s?: string) {
  if (!s) return '#94a3b8'
  if (s.includes('BUY')) return '#00e676'
  if (s.includes('SELL')) return '#ff1744'
  return '#ffab00'
}

function MomentumBar({ value }: { value?: number }) {
  if (value == null) return <span style={{ color: '#475569' }}>—</span>
  const color = value < 30 ? '#ff1744' : value > 70 ? '#00e676' : '#ffab00'
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 bg-white/10 rounded-full h-1.5 shrink-0">
        <div className="h-1.5 rounded-full" style={{ width: `${value}%`, backgroundColor: color }} />
      </div>
      <span className="text-xs tabular-nums" style={{ color }}>{value.toFixed(0)}%</span>
    </div>
  )
}

// ── Market Pulse strip ────────────────────────────────────────────────────────
function MarketPulse({ data }: { data: OpportunitiesData }) {
  const bullPct = Math.round((data.buy_count / data.total_scanned) * 100)
  const bearPct = Math.round((data.sell_count / data.total_scanned) * 100)
  const sentiment = bullPct > 50 ? 'Risk-On' : bullPct > 35 ? 'Neutral' : 'Risk-Off'
  const sentColor = bullPct > 50 ? '#00e676' : bullPct > 35 ? '#ffab00' : '#ff1744'

  return (
    <div
      className="rounded-xl border p-4 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
    >
      <div>
        <div className="text-xs mb-1" style={{ color: '#475569' }}>Universe Scanned</div>
        <div className="text-xl font-black" style={{ color: '#e2e8f0' }}>{data.total_scanned}</div>
        <div className="text-xs" style={{ color: '#475569' }}>stocks</div>
      </div>
      <div>
        <div className="text-xs mb-1" style={{ color: '#475569' }}>High-Quality Ideas</div>
        <div className="text-xl font-black" style={{ color: '#00d4ff' }}>{data.passed_count}</div>
        <div className="text-xs" style={{ color: '#475569' }}>VF score ≥ 40</div>
      </div>
      <div>
        <div className="text-xs mb-1" style={{ color: '#475569' }}>Avg VF Score</div>
        <div className="text-xl font-black" style={{ color: scoreColor(data.avg_vf_score) }}>{data.avg_vf_score}</div>
        <div className="text-xs" style={{ color: '#475569' }}>universe avg</div>
      </div>
      <div>
        <div className="text-xs mb-1" style={{ color: '#475569' }}>Buy Signals</div>
        <div className="text-xl font-black" style={{ color: '#00e676' }}>{data.buy_count}</div>
        <div className="text-xs" style={{ color: '#475569' }}>{bullPct}% of universe</div>
      </div>
      <div>
        <div className="text-xs mb-1" style={{ color: '#475569' }}>Sell Signals</div>
        <div className="text-xl font-black" style={{ color: '#ff1744' }}>{data.sell_count}</div>
        <div className="text-xs" style={{ color: '#475569' }}>{bearPct}% of universe</div>
      </div>
      <div>
        <div className="text-xs mb-1" style={{ color: '#475569' }}>Market Sentiment</div>
        <div className="text-lg font-black" style={{ color: sentColor }}>{sentiment}</div>
        <div className="text-xs" style={{ color: '#475569' }}>technical read</div>
      </div>
    </div>
  )
}

// ── Top 3 conviction pick card ────────────────────────────────────────────────
function ConvictionCard({ stock, rank }: { stock: ScannedStock; rank: number }) {
  const sig = stock.signal || ''
  const sigCol = signalColor(sig)
  const isBuy = sig.includes('BUY')

  const medalColors = ['#ffd700', '#c0c0c0', '#cd7f32', '#4ade80', '#60a5fa']
  const medalLabels = ['#1 Top Pick', '#2 Runner Up', '#3 Conviction', '#4 Opportunity', '#5 On Watch']

  return (
    <div
      className="rounded-2xl border p-5 flex flex-col gap-4"
      style={{
        backgroundColor: '#111827',
        borderColor: isBuy ? `${sigCol}30` : 'rgba(255,255,255,0.06)',
        borderLeftColor: medalColors[rank],
        borderLeftWidth: 3,
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold" style={{ color: medalColors[rank] }}>{medalLabels[rank]}</span>
          </div>
          <a href={`/analysis?ticker=${stock.ticker}`} className="flex items-center gap-2 hover:opacity-80">
            <span className="text-xl font-black font-mono" style={{ color: '#00d4ff' }}>{stock.ticker}</span>
          </a>
          <div className="text-xs mt-0.5 truncate max-w-[180px]" style={{ color: '#94a3b8' }}>{stock.name}</div>
        </div>
        <div className="text-right shrink-0">
          <div className="text-3xl font-black" style={{ color: scoreColor(stock.vf_score) }}>{stock.vf_score}</div>
          <div className="text-xs" style={{ color: '#475569' }}>VF Score</div>
        </div>
      </div>

      {/* Signal badge + conviction tier + confidence */}
      <div className="flex items-center gap-3">
        <span
          className="text-sm font-bold px-3 py-1 rounded-lg"
          style={{ backgroundColor: `${sigCol}20`, color: sigCol }}
        >
          {sig}
        </span>
        {stock.conviction_tier && (
          <span className="text-xs font-bold px-2 py-0.5 rounded"
            style={{ backgroundColor: `${convictionTierColor(stock.conviction_tier)}15`, color: convictionTierColor(stock.conviction_tier) }}>
            {stock.conviction_tier}
          </span>
        )}
        {stock.confidence != null && (
          <div className="flex items-center gap-2 flex-1">
            <div className="flex-1 bg-white/10 rounded-full h-2">
              <div className="h-2 rounded-full" style={{ width: `${stock.confidence}%`, backgroundColor: sigCol }} />
            </div>
            <span className="text-xs tabular-nums" style={{ color: '#94a3b8' }}>{stock.confidence}%</span>
          </div>
        )}
      </div>

      {/* Why now */}
      <div
        className="rounded-lg px-3 py-2 text-xs leading-relaxed"
        style={{ backgroundColor: '#0a0e1a', color: '#94a3b8', borderLeft: `2px solid ${sigCol}` }}
      >
        {stock.why_now}
      </div>

      {/* Score drivers */}
      {(stock.score_drivers ?? []).length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {stock.score_drivers.map((d, i) => (
            <span key={i} className="text-xs px-2 py-0.5 rounded-full"
              style={{ backgroundColor: '#00d4ff10', color: '#94a3b8', border: '1px solid rgba(0,212,255,0.12)' }}>
              {d}
            </span>
          ))}
        </div>
      )}

      {/* Qualification checks */}
      <div className="rounded-lg px-3 py-2.5 flex flex-col gap-1.5" style={{ backgroundColor: '#0a0e1a' }}>
        <p className="text-xs font-semibold uppercase tracking-wide mb-0.5" style={{ color: '#334155' }}>Due Diligence</p>

        <div className="flex items-center justify-between text-xs">
          <span style={{ color: '#475569' }}>Recent news (7d)</span>
          {stock.has_recent_news
            ? <span style={{ color: '#00e676' }}>✓ {stock.recent_news_count} article{stock.recent_news_count !== 1 ? 's' : ''} — check catalysts</span>
            : <span style={{ color: '#ffab00' }}>⚠ No recent news — verify catalyst</span>
          }
        </div>

        {stock.analyst_target_age_days != null && (
          <div className="flex items-center justify-between text-xs">
            <span style={{ color: '#475569' }}>Analyst target age</span>
            {stock.analyst_target_age_days > 90
              ? <span style={{ color: '#ff5252' }}>⚠ {stock.analyst_target_age_days}d old — may be stale</span>
              : <span style={{ color: '#00e676' }}>✓ {stock.analyst_target_age_days}d old — fresh</span>
            }
          </div>
        )}

        {stock.suggested_position_pct != null && (
          <div className="flex items-center justify-between text-xs">
            <span style={{ color: '#475569' }}>Max position size</span>
            <span style={{ color: '#94a3b8' }}>
              {stock.suggested_position_pct}% of portfolio
              {stock.volatility_annual != null && <span style={{ color: '#334155' }}> (vol {stock.volatility_annual.toFixed(0)}%/yr)</span>}
            </span>
          </div>
        )}
      </div>

      {/* Price + targets */}
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="rounded-lg p-2.5" style={{ backgroundColor: '#0a0e1a' }}>
          <div style={{ color: '#475569' }}>Current Price</div>
          <div className="font-bold text-sm mt-0.5" style={{ color: '#e2e8f0' }}>{fmt.price(stock.price)}</div>
        </div>
        <div className="rounded-lg p-2.5" style={{ backgroundColor: '#0a0e1a' }}>
          <div style={{ color: '#475569' }}>Analyst Target</div>
          <div className="font-bold text-sm mt-0.5" style={{ color: stock.analyst_upside && stock.analyst_upside > 0 ? '#00e676' : '#ff1744' }}>
            {stock.analyst_target ? fmt.price(stock.analyst_target) : '—'}
            {stock.analyst_upside != null && (
              <span className="text-xs ml-1">({stock.analyst_upside > 0 ? '+' : ''}{stock.analyst_upside}%)</span>
            )}
          </div>
        </div>
        <div className="rounded-lg p-2.5" style={{ backgroundColor: '#0a0e1a' }}>
          <div style={{ color: '#475569' }}>Stop Loss</div>
          <div className="font-bold text-sm mt-0.5" style={{ color: '#ff1744' }}>{fmt.price(stock.stop_loss)}</div>
        </div>
        <div className="rounded-lg p-2.5" style={{ backgroundColor: '#0a0e1a' }}>
          <div style={{ color: '#475569' }}>Target 1 / R:R</div>
          <div className="font-bold text-sm mt-0.5" style={{ color: '#00e676' }}>
            {fmt.price(stock.tp1)}
            {stock.risk_reward && <span className="text-xs ml-1 font-normal" style={{ color: '#94a3b8' }}>({stock.risk_reward}:1)</span>}
          </div>
        </div>
      </div>

      {/* Fundamentals strip */}
      <div className="grid grid-cols-4 gap-2 text-xs">
        {[
          { label: 'P/E', value: stock.pe_ratio ? stock.pe_ratio.toFixed(1) + 'x' : '—' },
          { label: 'ROE', value: stock.roe != null ? stock.roe.toFixed(1) + '%' : '—' },
          { label: 'Margin', value: stock.gross_margin != null ? stock.gross_margin.toFixed(1) + '%' : '—' },
          { label: 'Growth', value: stock.revenue_growth != null ? (stock.revenue_growth > 0 ? '+' : '') + stock.revenue_growth.toFixed(1) + '%' : '—' },
        ].map(({ label, value }) => (
          <div key={label} className="text-center rounded-lg py-1.5" style={{ backgroundColor: '#0a0e1a' }}>
            <div style={{ color: '#475569' }}>{label}</div>
            <div className="font-bold mt-0.5" style={{ color: '#e2e8f0' }}>{value}</div>
          </div>
        ))}
      </div>

      {/* 52-week momentum */}
      <div className="flex items-center justify-between text-xs">
        <span style={{ color: '#475569' }}>52-Week Position</span>
        <MomentumBar value={stock.week52_momentum} />
      </div>

      {/* TP ladder */}
      {(stock.tp1 || stock.tp2 || stock.tp3) && (
        <div className="flex gap-2 text-xs">
          {[['TP1', stock.tp1], ['TP2', stock.tp2], ['TP3', stock.tp3]].map(([label, val]) => val && (
            <div key={label as string} className="flex-1 text-center rounded py-1" style={{ backgroundColor: '#00e67610', color: '#00e676' }}>
              <div style={{ color: '#475569' }}>{label as string}</div>
              <div className="font-bold">{fmt.price(val as number)}</div>
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <a href={`/analysis?ticker=${stock.ticker}`}
          className="flex-1 text-center text-xs font-semibold py-2 rounded-xl"
          style={{ backgroundColor: '#00d4ff15', color: '#00d4ff' }}>
          Full Analysis →
        </a>
        <a href={`/analysis?ticker=${stock.ticker}#ai`}
          className="flex-1 text-center text-xs font-semibold py-2 rounded-xl"
          style={{ backgroundColor: '#7c3aed15', color: '#a78bfa', border: '1px solid rgba(124,58,237,0.12)' }}>
          AI Research (Claude) →
        </a>
      </div>
    </div>
  )
}

// ── Investment theme card ──────────────────────────────────────────────────────
function ThemeCard({ t }: { t: Theme }) {
  const [expanded, setExpanded] = useState(false)
  const convCol = convictionColor(t.conviction)

  return (
    <div
      className="rounded-xl border p-5 flex flex-col gap-3"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1.5">
            <span
              className="text-xs font-bold px-2 py-0.5 rounded"
              style={{ backgroundColor: `${convCol}15`, color: convCol }}
            >
              {t.conviction} CONVICTION
            </span>
            <span className="text-xs px-2 py-0.5 rounded" style={{ backgroundColor: '#00d4ff10', color: '#00d4ff' }}>
              {t.timeframe}
            </span>
          </div>
          <h3 className="text-sm font-bold" style={{ color: '#e2e8f0' }}>{t.theme}</h3>
        </div>
      </div>

      <p className="text-xs leading-relaxed" style={{ color: '#94a3b8' }}>{t.thesis}</p>

      <button
        onClick={() => setExpanded(e => !e)}
        className="flex items-center gap-1 text-xs font-medium"
        style={{ color: '#00d4ff' }}
      >
        {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        {expanded ? 'Hide' : 'Show'} catalysts
      </button>

      {expanded && (
        <div className="flex flex-col gap-1.5">
          {t.catalysts.map((c, i) => (
            <div key={i} className="flex gap-2 text-xs">
              <span style={{ color: '#00e676' }}>→</span>
              <span style={{ color: '#94a3b8' }}>{c}</span>
            </div>
          ))}
          <div className="text-xs mt-1 px-2 py-1.5 rounded" style={{ backgroundColor: '#00e67608', color: '#00e676' }}>
            {t.opportunity_size}
          </div>
        </div>
      )}

      <div className="flex flex-wrap gap-1.5">
        {t.stocks.map(s => (
          <a
            key={s}
            href={`/analysis?ticker=${s}`}
            className="text-xs font-mono font-semibold px-2 py-0.5 rounded hover:opacity-80"
            style={{ backgroundColor: '#0a0e1a', color: '#00d4ff', border: '1px solid rgba(0,212,255,0.2)' }}
          >
            {s}
          </a>
        ))}
      </div>

      <div className="flex items-start gap-1.5 text-xs">
        <Shield className="w-3.5 h-3.5 mt-0.5 shrink-0" style={{ color: '#ff1744' }} />
        <span style={{ color: '#94a3b8' }}><span style={{ color: '#ff1744' }}>Risk: </span>{t.risk}</span>
      </div>
    </div>
  )
}

// ── Domain breakdown bar list ─────────────────────────────────────────────────
function DomainBreakdown({ stats, activeDomain, onSelect }:
  { stats: Record<string, DomainStat>; activeDomain: string; onSelect: (d: string) => void }) {
  const entries = Object.entries(stats).sort((a, b) => b[1].avg_score - a[1].avg_score)
  const maxCount = Math.max(...entries.map(([, s]) => s.count), 1)
  return (
    <div className="rounded-xl border p-5 flex flex-col gap-2"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
      <p className="text-xs font-bold uppercase tracking-wide mb-1" style={{ color: '#94a3b8' }}>
        Domain Breakdown — click to filter
      </p>
      {entries.map(([domain, stat]) => {
        const isActive = activeDomain === domain
        const barPct   = Math.round((stat.count / maxCount) * 100)
        const avgColor = stat.avg_score >= 65 ? '#00e676' : stat.avg_score >= 50 ? '#ffab00' : '#94a3b8'
        return (
          <button key={domain} onClick={() => onSelect(isActive ? 'All' : domain)}
            className="flex items-center gap-3 w-full text-left rounded-lg px-3 py-1.5 transition-colors"
            style={{ backgroundColor: isActive ? '#1a2235' : 'transparent',
                     border: `1px solid ${isActive ? 'rgba(0,212,255,0.2)' : 'transparent'}` }}>
            <span className="text-xs font-semibold w-44 shrink-0 truncate"
              style={{ color: isActive ? '#00d4ff' : '#94a3b8' }}>{domain}</span>
            <div className="flex-1 bg-white/10 rounded-full h-1.5">
              <div className="h-1.5 rounded-full" style={{ width: `${barPct}%`, backgroundColor: avgColor }} />
            </div>
            <span className="text-xs font-bold px-2 py-0.5 rounded w-14 text-center shrink-0"
              style={{ backgroundColor: `${avgColor}15`, color: avgColor }}>{stat.avg_score.toFixed(1)}</span>
            <span className="text-xs shrink-0 w-24 text-right" style={{ color: '#475569' }}>
              {stat.buy_count} buys / {stat.count}
            </span>
          </button>
        )
      })}
    </div>
  )
}

// ── Filter bar ────────────────────────────────────────────────────────────────
function FilterBar({ activeDomain, setActiveDomain, activeSignal, setActiveSignal,
                     activeTier, setActiveTier, domains }:
  { activeDomain: string; setActiveDomain: (d: string) => void
    activeSignal: string;  setActiveSignal:  (s: string) => void
    activeTier: string;    setActiveTier:    (t: string) => void
    domains: string[] }) {
  function Pill({ label, active, color, onClick }:
    { label: string; active: boolean; color: string; onClick: () => void }) {
    return (
      <button onClick={onClick} className="text-xs font-semibold px-3 py-1 rounded-full transition-colors"
        style={{ backgroundColor: active ? `${color}25` : 'rgba(255,255,255,0.04)',
                 color: active ? color : '#475569',
                 border: `1px solid ${active ? color + '40' : 'transparent'}` }}>
        {label}
      </button>
    )
  }
  return (
    <div className="rounded-xl border p-4 flex flex-col gap-3"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
      <div className="flex flex-wrap gap-2 items-center">
        <span className="text-xs font-bold w-20 shrink-0" style={{ color: '#475569' }}>Domain</span>
        <Pill label="All" active={activeDomain === 'All'} color="#00d4ff" onClick={() => setActiveDomain('All')} />
        {domains.map(d => <Pill key={d} label={d} active={activeDomain === d} color="#00d4ff" onClick={() => setActiveDomain(d)} />)}
      </div>
      <div className="flex flex-wrap gap-2 items-center">
        <span className="text-xs font-bold w-20 shrink-0" style={{ color: '#475569' }}>Signal</span>
        {['All','BUY','HOLD'].map(s => <Pill key={s} label={s} active={activeSignal === s} color="#00e676" onClick={() => setActiveSignal(s)} />)}
      </div>
      <div className="flex flex-wrap gap-2 items-center">
        <span className="text-xs font-bold w-20 shrink-0" style={{ color: '#475569' }}>Conviction</span>
        {['All','STRONG BUY','BUY','WATCH'].map(t =>
          <Pill key={t} label={t} active={activeTier === t}
            color={convictionTierColor(t === 'All' ? 'WATCH' : t)} onClick={() => setActiveTier(t)} />)}
      </div>
    </div>
  )
}

// ── Full ideas table with sort ─────────────────────────────────────────────────
type SortKey = 'combined_score' | 'vf_score' | 'analyst_upside' | 'revenue_growth' | 'week52_momentum'

function IdeasTable({ ideas }: { ideas: ScannedStock[] }) {
  const [sortKey, setSortKey] = useState<SortKey>('combined_score')
  const [sortDir, setSortDir] = useState<'desc' | 'asc'>('desc')

  const sorted = [...ideas].sort((a, b) => {
    const av = (a[sortKey] ?? -999) as number
    const bv = (b[sortKey] ?? -999) as number
    return sortDir === 'desc' ? bv - av : av - bv
  })

  function toggleSort(key: SortKey) {
    if (sortKey === key) setDir(d => d === 'desc' ? 'asc' : 'desc')
    else { setSortKey(key); setSortDir('desc') }
  }

  // Helper that avoids TS error with functional update
  function setDir(fn: (d: 'desc' | 'asc') => 'desc' | 'asc') {
    setSortDir(prev => fn(prev))
  }

  function SortIcon({ k }: { k: SortKey }) {
    if (sortKey !== k) return null
    return sortDir === 'desc' ? <ChevronDown className="w-3 h-3 inline ml-0.5" /> : <ChevronUp className="w-3 h-3 inline ml-0.5" />
  }

  const TH = ({ label, k }: { label: string; k?: SortKey }) => (
    <th
      className="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wider whitespace-nowrap cursor-pointer select-none"
      style={{ color: k && sortKey === k ? '#00d4ff' : '#94a3b8' }}
      onClick={() => k && toggleSort(k)}
    >
      {label}{k && <SortIcon k={k} />}
    </th>
  )

  return (
    <div className="rounded-xl border overflow-hidden" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
      <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[1300px]">
          <thead>
            <tr style={{ backgroundColor: '#1a2235' }}>
              <TH label="Ticker" />
              <TH label="Name" />
              <TH label="Price" />
              <TH label="VF Score" k="vf_score" />
              <TH label="Combined" k="combined_score" />
              <TH label="Signal" />
              <TH label="Tier" />
              <TH label="Domain" />
              <TH label="Conf %" />
              <TH label="RSI" />
              <TH label="Trend" />
              <TH label="Analyst ↑" k="analyst_upside" />
              <TH label="Rev Growth" k="revenue_growth" />
              <TH label="ROE" />
              <TH label="Margin" />
              <TH label="52-Wk Pos" k="week52_momentum" />
              <TH label="SL" />
              <TH label="TP1" />
              <TH label="R:R" />
            </tr>
          </thead>
          <tbody>
            {sorted.map(s => {
              const sig = s.signal || ''
              const sigCol = signalColor(sig)
              return (
                <tr key={s.ticker} className="border-t hover:bg-white/[0.02]" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
                  <td className="px-3 py-3">
                    <a href={`/analysis?ticker=${s.ticker}`} className="font-bold font-mono text-xs px-2 py-0.5 rounded hover:opacity-80" style={{ color: '#00d4ff', backgroundColor: '#00d4ff15' }}>
                      {s.ticker}
                    </a>
                  </td>
                  <td className="px-3 py-3 text-xs max-w-[140px] truncate" style={{ color: '#94a3b8' }}>{s.name ?? '—'}</td>
                  <td className="px-3 py-3 text-xs tabular-nums font-semibold" style={{ color: '#e2e8f0' }}>{fmt.price(s.price)}</td>
                  <td className="px-3 py-3 text-xs font-black tabular-nums" style={{ color: scoreColor(s.vf_score) }}>{s.vf_score}</td>
                  <td className="px-3 py-3 text-xs tabular-nums" style={{ color: '#e2e8f0' }}>{s.combined_score.toFixed(1)}</td>
                  <td className="px-3 py-3">
                    <span className="text-xs font-bold px-2 py-0.5 rounded whitespace-nowrap" style={{ color: sigCol, backgroundColor: `${sigCol}15` }}>{sig || '—'}</span>
                  </td>
                  <td className="px-3 py-3">
                    <span className="text-xs font-bold px-2 py-0.5 rounded whitespace-nowrap"
                      style={{ color: convictionTierColor(s.conviction_tier ?? 'WATCH'), backgroundColor: `${convictionTierColor(s.conviction_tier ?? 'WATCH')}15` }}>
                      {s.conviction_tier ?? '—'}
                    </span>
                  </td>
                  <td className="px-3 py-3 text-xs truncate max-w-[120px]" style={{ color: '#475569' }}>{s.domain ?? '—'}</td>
                  <td className="px-3 py-3">
                    {s.confidence != null ? (
                      <div className="flex items-center gap-1.5">
                        <div className="w-12 bg-white/10 rounded-full h-1.5">
                          <div className="h-1.5 rounded-full" style={{ width: `${s.confidence}%`, backgroundColor: sigCol }} />
                        </div>
                        <span className="text-xs" style={{ color: '#94a3b8' }}>{s.confidence}%</span>
                      </div>
                    ) : '—'}
                  </td>
                  <td className="px-3 py-3 text-xs tabular-nums" style={{ color: (s.rsi ?? 50) < 40 ? '#00e676' : (s.rsi ?? 50) > 65 ? '#ff1744' : '#e2e8f0' }}>
                    {s.rsi != null ? s.rsi.toFixed(1) : '—'}
                  </td>
                  <td className="px-3 py-3 text-xs whitespace-nowrap" style={{ color: '#94a3b8' }}>{s.trend ?? '—'}</td>
                  <td className="px-3 py-3 text-xs tabular-nums font-semibold" style={{ color: s.analyst_upside != null ? changeColor(s.analyst_upside) : '#94a3b8' }}>
                    {s.analyst_upside != null ? (s.analyst_upside > 0 ? '+' : '') + s.analyst_upside.toFixed(1) + '%' : '—'}
                  </td>
                  <td className="px-3 py-3 text-xs tabular-nums" style={{ color: s.revenue_growth != null ? changeColor(s.revenue_growth) : '#94a3b8' }}>
                    {s.revenue_growth != null ? (s.revenue_growth > 0 ? '+' : '') + s.revenue_growth.toFixed(1) + '%' : '—'}
                  </td>
                  <td className="px-3 py-3 text-xs tabular-nums" style={{ color: '#e2e8f0' }}>
                    {s.roe != null ? s.roe.toFixed(1) + '%' : '—'}
                  </td>
                  <td className="px-3 py-3 text-xs tabular-nums" style={{ color: '#e2e8f0' }}>
                    {s.gross_margin != null ? s.gross_margin.toFixed(1) + '%' : '—'}
                  </td>
                  <td className="px-3 py-3"><MomentumBar value={s.week52_momentum} /></td>
                  <td className="px-3 py-3 text-xs tabular-nums" style={{ color: '#ff1744' }}>{fmt.price(s.stop_loss)}</td>
                  <td className="px-3 py-3 text-xs tabular-nums" style={{ color: '#00e676' }}>{fmt.price(s.tp1)}</td>
                  <td className="px-3 py-3 text-xs tabular-nums" style={{ color: '#94a3b8' }}>{s.risk_reward != null ? s.risk_reward.toFixed(1) + ':1' : '—'}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Golden Star helpers ───────────────────────────────────────────────────────
type GoldenTier = 'ACT_NOW' | 'HIGH_WATCH'

function goldTier(s: ScannedStock): GoldenTier {
  const isBuy = (s.signal ?? '').includes('BUY')
  if (isBuy && s.combined_score >= 68) return 'ACT_NOW'
  return 'HIGH_WATCH'
}

function HeroCard({ stock }: { stock: ScannedStock }) {
  const navigate = useNavigate()
  const [added, setAdded] = useState(false)
  const sigCol = signalColor(stock.signal)
  const upside = stock.analyst_upside
  return (
    <div
      className="rounded-2xl border p-6 flex flex-col gap-5"
      style={{
        background: 'linear-gradient(135deg, rgba(0,230,118,0.06) 0%, rgba(0,0,0,0) 60%)',
        borderColor: 'rgba(0,230,118,0.3)',
        borderLeftWidth: 4,
        borderLeftColor: '#00e676',
      }}
    >
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-xs font-black uppercase tracking-widest px-3 py-1 rounded-full"
          style={{ backgroundColor: '#00e67618', color: '#00e676', border: '1px solid rgba(0,230,118,0.3)' }}>
          ★ Best Setup Right Now
        </span>
        <span className="text-xs font-bold px-2 py-0.5 rounded-lg"
          style={{ backgroundColor: `${sigCol}20`, color: sigCol }}>{stock.signal}</span>
        {stock.signal_quality === 'PRIME' && (
          <span className="text-xs font-bold px-2 py-0.5 rounded-lg"
            style={{ backgroundColor: 'rgba(255,215,0,0.12)', color: '#ffd700' }}>PRIME</span>
        )}
      </div>

      <div className="flex items-start gap-6 flex-wrap">
        <div>
          <button onClick={() => navigate(`/analysis?ticker=${stock.ticker}`)}
            className="text-4xl font-black hover:underline" style={{ color: '#00d4ff' }}>
            {stock.ticker}
          </button>
          <div className="text-sm mt-0.5" style={{ color: '#94a3b8' }}>{stock.name}</div>
          <div className="text-xs mt-0.5" style={{ color: '#475569' }}>
            {stock.sector}{stock.domain ? ` · ${stock.domain}` : ''}
          </div>
        </div>
        <div className="flex gap-5">
          <div className="text-center">
            <div className="text-3xl font-black" style={{ color: scoreColor(stock.vf_score) }}>{stock.vf_score}</div>
            <div className="text-xs" style={{ color: '#475569' }}>VF Score</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-black" style={{ color: scoreColor(stock.combined_score) }}>{stock.combined_score.toFixed(0)}</div>
            <div className="text-xs" style={{ color: '#475569' }}>Combined</div>
          </div>
        </div>
        {stock.confidence != null && (
          <div className="flex flex-col gap-1.5 justify-center">
            <div className="text-xs font-semibold" style={{ color: '#475569' }}>Signal Confidence</div>
            <div className="flex items-center gap-2">
              <div className="w-32 bg-white/10 rounded-full h-2.5">
                <div className="h-2.5 rounded-full" style={{ width: `${stock.confidence}%`, backgroundColor: sigCol }} />
              </div>
              <span className="text-sm font-bold tabular-nums" style={{ color: sigCol }}>{stock.confidence}%</span>
            </div>
          </div>
        )}
      </div>

      <div
        className="rounded-xl px-4 py-3 text-sm leading-relaxed"
        style={{ backgroundColor: 'rgba(0,230,118,0.04)', color: '#94a3b8', borderLeft: '3px solid rgba(0,230,118,0.5)' }}
      >
        <span className="font-semibold text-xs uppercase tracking-wide mr-2" style={{ color: '#00e676' }}>WHY NOW </span>
        {stock.why_now}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Entry Price', value: fmt.price(stock.price),                color: '#e2e8f0', sub: null },
          { label: 'Stop Loss',   value: fmt.price(stock.stop_loss) || '—',     color: '#ff1744', sub: null },
          { label: 'Target 1',   value: fmt.price(stock.tp1) || '—',            color: '#00e676',
            sub: stock.risk_reward != null ? `${stock.risk_reward}:1 R:R` : null },
          { label: 'Analyst Tgt', value: stock.analyst_target ? fmt.price(stock.analyst_target) : '—',
            color: upside != null && upside > 0 ? '#00e676' : '#ff1744',
            sub: upside != null ? `${upside > 0 ? '+' : ''}${upside.toFixed(1)}% upside` : null },
        ].map(({ label, value, color, sub }) => (
          <div key={label} className="rounded-xl p-3 text-center" style={{ backgroundColor: '#0a0e1a' }}>
            <div className="text-xs mb-1" style={{ color: '#475569' }}>{label}</div>
            <div className="text-lg font-black" style={{ color }}>{value}</div>
            {sub && <div className="text-xs mt-0.5 font-semibold" style={{ color }}>{sub}</div>}
          </div>
        ))}
      </div>

      {(stock.tp1 || stock.tp2 || stock.tp3 || stock.roe != null) && (
        <div className="flex flex-wrap gap-4 items-center">
          {(stock.tp1 || stock.tp2 || stock.tp3) && (
            <div className="flex gap-2">
              {[['TP1', stock.tp1], ['TP2', stock.tp2], ['TP3', stock.tp3]].map(([label, val]) => val && (
                <div key={label as string} className="text-center rounded-lg px-3 py-1.5"
                  style={{ backgroundColor: '#00e67608', border: '1px solid rgba(0,230,118,0.12)' }}>
                  <div className="text-xs" style={{ color: '#334155' }}>{label as string}</div>
                  <div className="text-sm font-bold" style={{ color: '#00e676' }}>{fmt.price(val as number)}</div>
                </div>
              ))}
            </div>
          )}
          <div className="flex gap-4 flex-wrap ml-auto text-xs">
            {stock.roe != null && <span style={{ color: '#475569' }}>ROE <b style={{ color: stock.roe >= 20 ? '#00e676' : '#94a3b8' }}>{stock.roe.toFixed(1)}%</b></span>}
            {stock.gross_margin != null && <span style={{ color: '#475569' }}>Margin <b style={{ color: '#94a3b8' }}>{stock.gross_margin.toFixed(1)}%</b></span>}
            {stock.revenue_growth != null && <span style={{ color: '#475569' }}>Growth <b style={{ color: changeColor(stock.revenue_growth) }}>{stock.revenue_growth > 0 ? '+' : ''}{stock.revenue_growth.toFixed(1)}%</b></span>}
            {stock.pe_ratio != null && <span style={{ color: '#475569' }}>P/E <b style={{ color: '#94a3b8' }}>{stock.pe_ratio.toFixed(1)}x</b></span>}
          </div>
        </div>
      )}

      <div className="flex gap-3 flex-wrap">
        <button onClick={() => navigate(`/analysis?ticker=${stock.ticker}`)}
          className="flex-1 text-center text-sm font-bold py-2.5 rounded-xl hover:opacity-90 transition-opacity"
          style={{ backgroundColor: '#00e67618', color: '#00e676', border: '1px solid rgba(0,230,118,0.25)' }}>
          Full Analysis →
        </button>
        <button onClick={() => navigate(`/analysis?ticker=${stock.ticker}#ai`)}
          className="flex-1 text-center text-sm font-bold py-2.5 rounded-xl hover:opacity-90 transition-opacity"
          style={{ backgroundColor: '#7c3aed15', color: '#a78bfa', border: '1px solid rgba(124,58,237,0.12)' }}>
          AI Deep Research →
        </button>
        <button
          onClick={() => { addToWatchlist(stock.ticker); setAdded(true); setTimeout(() => setAdded(false), 2000) }}
          className="px-5 text-sm font-bold py-2.5 rounded-xl transition-all"
          style={{ backgroundColor: added ? '#00e67615' : '#1a2235', color: added ? '#00e676' : '#94a3b8',
                   border: `1px solid ${added ? 'rgba(0,230,118,0.3)' : 'rgba(255,255,255,0.06)'}` }}>
          {added ? '✓ Added' : '+ Watch'}
        </button>
      </div>
    </div>
  )
}

function ActionCard({ stock, rank }: { stock: ScannedStock; rank: number }) {
  const navigate = useNavigate()
  const sigCol = signalColor(stock.signal)
  const upside = stock.analyst_upside
  return (
    <div
      className="rounded-xl border p-4 flex flex-col gap-3 cursor-pointer transition-colors"
      onClick={() => navigate(`/analysis?ticker=${stock.ticker}`)}
      style={{ backgroundColor: '#111827', borderColor: `${sigCol}20`, borderLeftWidth: 2, borderLeftColor: sigCol }}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="flex items-center gap-1.5 mb-0.5">
            <span className="text-xs" style={{ color: '#334155' }}>#{rank}</span>
            <span className="text-xs font-bold px-2 py-0.5 rounded"
              style={{ backgroundColor: `${sigCol}15`, color: sigCol }}>{stock.signal}</span>
          </div>
          <div className="text-xl font-black font-mono" style={{ color: '#00d4ff' }}>{stock.ticker}</div>
          <div className="text-xs truncate max-w-[160px]" style={{ color: '#475569' }}>{stock.name}</div>
        </div>
        <div className="text-right shrink-0">
          <div className="text-2xl font-black" style={{ color: scoreColor(stock.combined_score) }}>{stock.combined_score.toFixed(0)}</div>
          <div className="text-xs" style={{ color: '#334155' }}>VF {stock.vf_score}</div>
        </div>
      </div>

      {stock.confidence != null && (
        <div className="flex items-center gap-2">
          <div className="flex-1 bg-white/10 rounded-full h-1.5">
            <div className="h-1.5 rounded-full" style={{ width: `${stock.confidence}%`, backgroundColor: sigCol }} />
          </div>
          <span className="text-xs tabular-nums shrink-0" style={{ color: '#475569' }}>{stock.confidence}%</span>
        </div>
      )}

      <div className="grid grid-cols-3 gap-2 text-xs">
        {[
          { l: 'Entry', v: fmt.price(stock.price),               c: '#e2e8f0' },
          { l: 'SL',    v: fmt.price(stock.stop_loss) || '—',    c: '#ff1744' },
          { l: 'TP1',   v: fmt.price(stock.tp1) || '—',          c: '#00e676' },
        ].map(({ l, v, c }) => (
          <div key={l} className="rounded-lg p-2 text-center" style={{ backgroundColor: '#0a0e1a' }}>
            <div style={{ color: '#334155' }}>{l}</div>
            <div className="font-bold mt-0.5" style={{ color: c }}>{v}</div>
          </div>
        ))}
      </div>

      {upside != null && (
        <div className="flex items-center justify-between text-xs">
          <span style={{ color: '#475569' }}>Analyst target</span>
          <span className="font-bold" style={{ color: upside > 0 ? '#00e676' : '#ff1744' }}>
            {stock.analyst_target ? fmt.price(stock.analyst_target) : '—'}
            <span className="ml-1">({upside > 0 ? '+' : ''}{upside.toFixed(1)}%)</span>
          </span>
        </div>
      )}

      {stock.risk_reward != null && (
        <div className="text-xs" style={{ color: '#334155' }}>R:R {stock.risk_reward}:1</div>
      )}

      <div className="text-xs leading-relaxed italic" style={{ color: '#475569' }}>{stock.why_now}</div>
    </div>
  )
}

function WatchCard({ stock }: { stock: ScannedStock }) {
  const navigate = useNavigate()
  const sigCol = signalColor(stock.signal)
  const upside = stock.analyst_upside
  return (
    <div
      className="rounded-xl border p-4 flex flex-col gap-2 cursor-pointer transition-colors"
      onClick={() => navigate(`/analysis?ticker=${stock.ticker}`)}
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
    >
      <div className="flex items-center justify-between gap-2">
        <div>
          <div className="text-base font-black font-mono" style={{ color: '#00d4ff' }}>{stock.ticker}</div>
          <div className="text-xs truncate max-w-[130px]" style={{ color: '#475569' }}>{stock.name}</div>
        </div>
        <div className="text-right">
          <div className="text-xl font-black" style={{ color: scoreColor(stock.vf_score) }}>{stock.vf_score}</div>
          <div className="text-xs" style={{ color: '#334155' }}>VF</div>
        </div>
      </div>
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-xs font-bold px-2 py-0.5 rounded"
          style={{ backgroundColor: `${sigCol}15`, color: sigCol }}>{stock.signal}</span>
        {upside != null && upside > 0 && (
          <span className="text-xs font-semibold" style={{ color: '#00e676' }}>↑{upside.toFixed(1)}% analyst</span>
        )}
      </div>
      <div className="text-xs leading-relaxed" style={{ color: '#475569' }}>
        {(stock.why_now ?? '').slice(0, 110)}{(stock.why_now ?? '').length > 110 ? '…' : ''}
      </div>
      <div className="flex items-center justify-between text-xs pt-0.5">
        <span style={{ color: '#334155' }}>{fmt.price(stock.price)}</span>
        {stock.roe != null && <span style={{ color: '#334155' }}>ROE {stock.roe.toFixed(0)}%</span>}
        <span className="font-semibold" style={{ color: '#00d4ff' }}>→</span>
      </div>
    </div>
  )
}

// ── Golden Star Opportunities tab ─────────────────────────────────────────────
function Top50View({ ideas, data, onRefresh }: { ideas: ScannedStock[]; data: OpportunitiesData; onRefresh: () => void }) {
  const candidates = [...ideas]
    .filter(s => (s.signal ?? '').includes('BUY') || (s.vf_score >= 75 && (s.analyst_upside ?? 0) >= 12))
    .sort((a, b) => b.combined_score - a.combined_score)
    .slice(0, 50)

  const actNow    = candidates.filter(s => goldTier(s) === 'ACT_NOW')
  const highWatch = candidates.filter(s => goldTier(s) === 'HIGH_WATCH')
  const hero      = actNow[0] ?? highWatch[0]
  const actNowRest    = actNow.filter(s => s !== hero)
  const highWatchRest = highWatch.filter(s => s !== hero)

  const bullPct   = Math.round((data.buy_count / data.total_scanned) * 100)
  const sentiment = bullPct > 50 ? 'Risk-On' : bullPct > 35 ? 'Neutral' : 'Risk-Off'
  const sentColor = bullPct > 50 ? '#00e676' : bullPct > 35 ? '#ffab00' : '#ff1744'

  if (candidates.length === 0) {
    const isEmpty = data.passed_count === 0
    return (
      <div className="flex flex-col items-center gap-4 py-16">
        <Star className="w-8 h-8" fill="none" style={{ color: '#334155' }} />
        <p className="text-sm font-semibold" style={{ color: '#475569' }}>
          {isEmpty ? 'Scan data not yet loaded' : 'No actionable setups in current scan'}
        </p>
        <p className="text-xs text-center max-w-md" style={{ color: '#334155' }}>
          {isEmpty
            ? 'The last scan returned no results — likely due to a data source timeout. Click Refresh to re-run the scan now.'
            : 'No BUY signals or high-conviction setups found. Market may be in a risk-off environment.'}
        </p>
        {isEmpty && (
          <button
            onClick={onRefresh}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold"
            style={{ backgroundColor: '#00d4ff15', color: '#00d4ff', border: '1px solid rgba(0,212,255,0.25)' }}
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh Scan Now
          </button>
        )}
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-8">
      {/* Context strip */}
      <div className="flex items-center gap-5 flex-wrap text-xs px-4 py-2.5 rounded-xl"
        style={{ backgroundColor: '#0d1424', border: '1px solid rgba(255,255,255,0.04)' }}>
        <div className="flex items-center gap-1.5">
          <Star className="w-3 h-3" fill="#ffd700" style={{ color: '#ffd700' }} />
          <span className="font-bold" style={{ color: '#ffd700' }}>{candidates.length} actionable</span>
          <span style={{ color: '#334155' }}>of {data.total_scanned} scanned</span>
        </div>
        <span style={{ color: '#1e293b' }}>|</span>
        <div className="flex items-center gap-1.5">
          <span style={{ color: '#475569' }}>Market:</span>
          <span className="font-bold" style={{ color: sentColor }}>{sentiment}</span>
          <span style={{ color: '#334155' }}>· {bullPct}% buy signals</span>
        </div>
        <span style={{ color: '#1e293b' }}>|</span>
        <span className="font-bold" style={{ color: '#00e676' }}>{actNow.length} Act Now</span>
        <span className="font-bold" style={{ color: '#ffab00' }}>{highWatch.length} High Watch</span>
      </div>

      {/* Hero — single best pick */}
      {hero && <HeroCard stock={hero} />}

      {/* Act Now grid */}
      {actNowRest.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Zap className="w-4 h-4" style={{ color: '#00e676' }} />
            <h2 className="text-sm font-bold uppercase tracking-wide" style={{ color: '#e2e8f0' }}>Act Now</h2>
            <span className="text-xs px-2 py-0.5 rounded font-semibold"
              style={{ backgroundColor: '#00e67610', color: '#00e676' }}>{actNowRest.length} setups</span>
            <span className="text-xs" style={{ color: '#334155' }}>confirmed BUY · combined score ≥ 68</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
            {actNowRest.map((s, i) => <ActionCard key={s.ticker} stock={s} rank={i + 2} />)}
          </div>
        </div>
      )}

      {/* High Conviction Watch */}
      {highWatchRest.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-4 h-4" style={{ color: '#ffab00' }} />
            <h2 className="text-sm font-bold uppercase tracking-wide" style={{ color: '#e2e8f0' }}>High Conviction Watch</h2>
            <span className="text-xs px-2 py-0.5 rounded font-semibold"
              style={{ backgroundColor: '#ffab0010', color: '#ffab00' }}>{highWatchRest.length} picks</span>
            <span className="text-xs" style={{ color: '#334155' }}>strong fundamentals · building entry</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {highWatchRest.map(s => <WatchCard key={s.ticker} stock={s} />)}
          </div>
        </div>
      )}
    </div>
  )
}

// ── Page ─────────────────────────────────────────────────────────────────────
export default function Opportunities() {
  const { data, isLoading, isError, refetch, isFetching } = useQuery<OpportunitiesData>({
    queryKey: ['opportunities'],
    queryFn: () => opportunitiesApi.get(),
    staleTime: 2 * 60_000,
    retry: 5,
    retryDelay: (attempt) => Math.min(5000 * (attempt + 1), 30_000),
  })

  const { data: regime } = useQuery({
    queryKey: ['market-regime'],
    queryFn: advancedApi.marketBreadth,
    staleTime: 5 * 60_000,
  })

  const [activeMainTab, setActiveMainTab] = useState<'scan' | 'top50'>('scan')
  const [activeDomain, setActiveDomain] = useState<string>('All')
  const [activeSignal, setActiveSignal]  = useState<string>('All')
  const [activeTier, setActiveTier]      = useState<string>('All')
  const [addedTop5, setAddedTop5] = useState(false)

  const filteredIdeas = (data?.all_ideas ?? []).filter(s => {
    if (activeDomain !== 'All' && s.domain !== activeDomain) return false
    if (activeSignal !== 'All' && !s.signal?.includes(activeSignal)) return false
    if (activeTier !== 'All' && s.conviction_tier !== activeTier) return false
    return true
  })
  const allDomains = Object.keys(data?.domain_stats ?? {}).sort()

  const lastScanned = data?.cached_at
    ? (() => {
        const mins = Math.floor((Date.now() / 1000 - data.cached_at) / 60)
        return mins < 1 ? 'just now' : `${mins}m ago`
      })()
    : null

  const handleRefresh = async () => {
    await opportunitiesApi.refresh()
    refetch()
  }

  return (
    <PageWrapper>
      <div className="flex flex-col gap-8">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Zap className="w-5 h-5" style={{ color: '#ffab00' }} />
              <h1 className="text-2xl font-black" style={{ color: '#e2e8f0' }}>Global Market Intelligence</h1>
            </div>
            <p className="text-sm" style={{ color: '#475569' }}>
              ~500 stocks across 20 domains — live VF scoring, technical signals, analyst targets, and top conviction picks
              {lastScanned && <span className="ml-3" style={{ color: '#334155' }}>· Scanned {lastScanned}</span>}
            </p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={isFetching}
            className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-opacity disabled:opacity-40"
            style={{ backgroundColor: '#1a2235', border: '1px solid rgba(255,255,255,0.06)', color: '#94a3b8' }}
          >
            <RefreshCw className={`w-3 h-3 ${isFetching ? 'animate-spin' : ''}`} />
            {isFetching ? 'Scanning…' : 'Refresh'}
          </button>
        </div>

        {/* Market Regime Warning */}
        {regime?.regime && regime.regime !== 'Unknown' && (
          <div
            className="flex items-center justify-between px-4 py-3 rounded-xl text-sm"
            style={{
              backgroundColor: regime.color + '12',
              border: `1px solid ${regime.color}35`,
            }}
          >
            <div className="flex items-center gap-3">
              <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: regime.color }} />
              <span className="font-semibold" style={{ color: regime.color }}>{regime.regime}</span>
              <span style={{ color: '#94a3b8' }}>{regime.description}</span>
              {regime.vix != null && (
                <span className="text-xs px-2 py-0.5 rounded font-mono"
                  style={{ backgroundColor: 'rgba(255,255,255,0.04)', color: '#475569' }}>
                  VIX {regime.vix}
                </span>
              )}
            </div>
            {regime.spy_change != null && (
              <span className="text-xs font-semibold tabular-nums"
                style={{ color: regime.spy_change >= 0 ? '#00e676' : '#ff1744' }}>
                SPY {regime.spy_change >= 0 ? '+' : ''}{regime.spy_change.toFixed(2)}%
              </span>
            )}
          </div>
        )}

        {/* Main tab bar */}
        <div className="flex gap-1 p-1 rounded-xl w-fit" style={{ backgroundColor: '#0d1424', border: '1px solid rgba(255,255,255,0.06)' }}>
          {([
            { key: 'scan', label: 'Market Scan' },
            { key: 'top50', label: '★ Top 50' },
          ] as const).map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveMainTab(tab.key)}
              className="px-4 py-1.5 rounded-lg text-xs font-semibold transition-all"
              style={{
                backgroundColor: activeMainTab === tab.key ? '#1e3a5f' : 'transparent',
                color: activeMainTab === tab.key ? (tab.key === 'top50' ? '#ffd700' : '#00d4ff') : '#475569',
                border: activeMainTab === tab.key ? '1px solid rgba(255,255,255,0.1)' : '1px solid transparent',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {isLoading && (
          <div className="flex flex-col items-center gap-4 py-20">
            <Loader2 className="w-8 h-8 animate-spin" style={{ color: '#00d4ff' }} />
            <div className="text-center">
              <div className="text-sm font-semibold mb-1" style={{ color: '#e2e8f0' }}>Scanning Global Markets…</div>
              <div className="text-xs" style={{ color: '#475569' }}>Analysing ~500 stocks across 20 domains. First load may take 90-120s.</div>
            </div>
          </div>
        )}

        {isError && (
          <div className="rounded-xl border p-5" style={{ backgroundColor: 'rgba(255,23,68,0.05)', borderColor: 'rgba(255,23,68,0.2)' }}>
            <p className="text-sm font-semibold mb-1" style={{ color: '#ff1744' }}>Market scan unavailable</p>
            <p className="text-xs mb-3" style={{ color: '#94a3b8' }}>
              The background scan may still be warming up after a server restart. This typically takes 60–120s.
            </p>
            <button
              onClick={() => refetch()}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold"
              style={{ backgroundColor: '#ff174420', border: '1px solid rgba(255,23,68,0.3)', color: '#ff1744' }}
            >
              <RefreshCw className="w-3.5 h-3.5" /> Retry Now
            </button>
          </div>
        )}

        {data && data.all_ideas.length === 0 && !isLoading && (
          <div className="rounded-xl border p-6 flex flex-col items-center gap-3 text-center" style={{ backgroundColor: 'rgba(0,212,255,0.05)', borderColor: 'rgba(0,212,255,0.15)' }}>
            <Loader2 className="w-6 h-6 animate-spin" style={{ color: '#00d4ff' }} />
            <div>
              <p className="text-sm font-semibold mb-1" style={{ color: '#e2e8f0' }}>Market scan is rebuilding</p>
              <p className="text-xs" style={{ color: '#94a3b8' }}>
                The data source is temporarily rate-limited. The scan will auto-complete within 15–30 minutes.<br />
                You can also click Refresh to try immediately.
              </p>
            </div>
          </div>
        )}

        {data && data.all_ideas.length > 0 && activeMainTab === 'scan' && (
          <>
            {/* Market Pulse */}
            <MarketPulse data={data} />

            {/* Filter bar */}
            <FilterBar
              activeDomain={activeDomain} setActiveDomain={setActiveDomain}
              activeSignal={activeSignal}  setActiveSignal={setActiveSignal}
              activeTier={activeTier}      setActiveTier={setActiveTier}
              domains={allDomains}
            />

            {/* Top 5 Conviction Picks */}
            {data.top_picks.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-4 flex-wrap">
                  <Target className="w-4 h-4" style={{ color: '#ffd700' }} />
                  <h2 className="text-sm font-bold uppercase tracking-wide" style={{ color: '#e2e8f0' }}>
                    Top Conviction Picks
                  </h2>
                  <span className="text-xs px-2 py-0.5 rounded" style={{ backgroundColor: '#ffd70015', color: '#ffd700' }}>
                    AI-ranked by combined VF + technical score
                  </span>
                  <button
                    onClick={() => {
                      data.top_picks.slice(0, 5).forEach(s => addToWatchlist(s.ticker))
                      setAddedTop5(true)
                      setTimeout(() => setAddedTop5(false), 3000)
                    }}
                    className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
                    style={{ backgroundColor: addedTop5 ? '#00e67615' : '#1a2235', color: addedTop5 ? '#00e676' : '#94a3b8', border: `1px solid ${addedTop5 ? 'rgba(0,230,118,0.3)' : 'rgba(255,255,255,0.06)'}` }}>
                    {addedTop5 ? <Check className="w-3 h-3" /> : <BookmarkPlus className="w-3 h-3" />}
                    {addedTop5 ? 'Added to Watchlist' : 'Add Top 5 to Watchlist'}
                  </button>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-5">
                  {data.top_picks.map((s, i) => (
                    <ConvictionCard key={s.ticker} stock={s} rank={i} />
                  ))}
                </div>
              </div>
            )}

            {/* Domain breakdown */}
            {data.domain_stats && Object.keys(data.domain_stats).length > 0 && (
              <DomainBreakdown
                stats={data.domain_stats}
                activeDomain={activeDomain}
                onSelect={setActiveDomain}
              />
            )}

            {/* Investment Themes */}
            <div>
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="w-4 h-4" style={{ color: '#00d4ff' }} />
                <h2 className="text-sm font-bold uppercase tracking-wide" style={{ color: '#e2e8f0' }}>
                  {data.themes.length} Major Investment Themes
                </h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
                {data.themes.map((t: Theme) => (
                  <ThemeCard key={t.theme} t={t} />
                ))}
              </div>
            </div>

            {/* Full ideas table */}
            {data.all_ideas.length > 0 && (
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <BarChart2 className="w-4 h-4" style={{ color: '#00e676' }} />
                  <h2 className="text-sm font-bold uppercase tracking-wide" style={{ color: '#e2e8f0' }}>
                    All Qualified Opportunities
                  </h2>
                  <span className="text-xs" style={{ color: '#475569' }}>
                    {filteredIdeas.length} of {data.all_ideas.length} opportunities (VF ≥ 40) — click column headers to sort
                  </span>
                </div>
                <IdeasTable ideas={filteredIdeas} />
              </div>
            )}
          </>
        )}

        {data && activeMainTab === 'top50' && (
          <Top50View ideas={data.all_ideas} data={data} onRefresh={handleRefresh} />
        )}
      </div>
    </PageWrapper>
  )
}
