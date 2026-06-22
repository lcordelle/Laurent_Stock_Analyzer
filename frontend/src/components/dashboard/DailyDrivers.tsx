import { useQuery, useQueryClient } from '@tanstack/react-query'
import { marketPulseApi, newsApi } from '../../services/api'
import type { NewsItem } from '../../services/api'
import { useNavigate } from 'react-router-dom'
import { useState } from 'react'

interface MarketSummary {
  bias: 'UP' | 'DOWN' | 'HOLD'
  outlook: 'bullish' | 'bearish' | 'mixed' | 'neutral'
  confidence: 'HIGH' | 'MEDIUM' | 'LOW'
  narrative: string
  trading_guidance?: string
  key_risk?: string
}

interface DailyDriver {
  rank: number
  type: string
  title: string
  direction: 'bullish' | 'bearish' | 'neutral'
  impact: 'HIGH' | 'MEDIUM'
  why: string
  ticker?: string | null
}

interface DailyDriversResponse {
  summary?: MarketSummary | null
  drivers: DailyDriver[]
  as_of: string
  generated_at: string
  cache_ttl_min: number
}

const TYPE_LABELS: Record<string, string> = {
  earnings: 'Earnings', macro: 'Macro', fed: 'Fed', rates: 'Rates',
  geopolitical: 'Geo', technical: 'Technical', sentiment: 'Sentiment',
}
const DIR_COLOR: Record<string, string> = {
  bullish: '#00e676', bearish: '#ff1744', neutral: '#ffab00',
  UP: '#00e676', DOWN: '#ff1744', HOLD: '#ffab00', mixed: '#ffab00',
}
const RANK_COLORS = ['#ffd700', '#c0c0c0', '#cd7f32']
const BIAS_ICON: Record<string, string> = { UP: '▲', DOWN: '▼', HOLD: '◆' }
const BIAS_LABEL: Record<string, string> = {
  UP: 'Market likely UP today',
  DOWN: 'Market likely DOWN today',
  HOLD: 'Mixed signals — hold cautious',
}
const SENT_COLOR: Record<string, string> = {
  positive: '#00e676', negative: '#ff1744', neutral: '#ffab00',
}

function formatAge(isoUtc: string): string {
  const generated = new Date(isoUtc)
  const now = new Date()
  const diffMin = Math.floor((now.getTime() - generated.getTime()) / 60000)
  const localTime = generated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  if (diffMin < 1) return `Updated just now (${localTime})`
  if (diffMin === 1) return `Updated 1 min ago (${localTime})`
  return `Updated ${diffMin} min ago (${localTime})`
}

function formatNewsAge(publishedAt: string): string {
  if (!publishedAt) return ''
  let date: Date
  const ts = Number(publishedAt)
  if (!isNaN(ts) && ts > 1_000_000_000) {
    date = new Date(ts * 1000)
  } else {
    date = new Date(publishedAt)
  }
  if (isNaN(date.getTime())) return ''
  const mins = Math.floor((Date.now() - date.getTime()) / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

function Skeleton({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return (
    <div
      className={`animate-pulse rounded ${className ?? ''}`}
      style={{ backgroundColor: 'rgba(255,255,255,0.06)', ...style }}
    />
  )
}

function SummaryCard({ summary, generated_at, cache_ttl_min, onRefresh, refreshing }: {
  summary: MarketSummary
  generated_at: string
  cache_ttl_min: number
  onRefresh: () => void
  refreshing: boolean
}) {
  const color = DIR_COLOR[summary.bias] ?? '#ffab00'
  const icon = BIAS_ICON[summary.bias] ?? '◆'
  const label = BIAS_LABEL[summary.bias] ?? summary.bias
  const age = formatAge(generated_at)

  return (
    <div
      className="rounded-xl border p-4"
      style={{
        backgroundColor: '#0d1520',
        borderColor: `${color}40`,
        background: `linear-gradient(135deg, ${color}10 0%, #0d1520 60%)`,
      }}
    >
      <div className="flex items-start gap-3">
        <div
          className="flex-shrink-0 w-14 h-14 rounded-xl flex flex-col items-center justify-center"
          style={{ backgroundColor: `${color}18`, border: `1.5px solid ${color}50` }}
        >
          <span className="text-xl font-black leading-none" style={{ color }}>{icon}</span>
          <span className="text-xs font-black mt-0.5" style={{ color }}>{summary.bias}</span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1.5">
            <span className="text-sm font-black" style={{ color }}>{label}</span>
            <span className="text-xs font-bold px-2 py-0.5 rounded-full"
              style={{ backgroundColor: `${color}15`, color }}>
              {summary.outlook.charAt(0).toUpperCase() + summary.outlook.slice(1)}
            </span>
            <span className="text-xs font-semibold px-2 py-0.5 rounded-full"
              style={{ backgroundColor: 'rgba(255,255,255,0.05)', color: '#64748b' }}>
              {summary.confidence} confidence
            </span>
            <div className="ml-auto flex items-center gap-2">
              <span className="text-xs hidden sm:inline" style={{ color: '#334155' }}>
                {age} · auto-refresh {cache_ttl_min}min
              </span>
              <button
                onClick={onRefresh}
                disabled={refreshing}
                className="text-xs font-semibold px-2 py-1 rounded-lg transition-opacity disabled:opacity-40"
                style={{ backgroundColor: 'rgba(0,212,255,0.08)', color: '#00d4ff' }}
                title="Force refresh with latest market data"
              >
                {refreshing ? '↻ …' : '↻ Now'}
              </button>
            </div>
          </div>

          <p className="text-xs leading-relaxed" style={{ color: '#94a3b8' }}>
            {summary.narrative}
          </p>

          {summary.trading_guidance && (
            <div className="mt-2 pt-2 border-t" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
              <span className="text-xs font-bold uppercase tracking-wide" style={{ color: '#00d4ff' }}>
                Trading Guidance
              </span>
              <p className="text-xs leading-relaxed mt-1" style={{ color: '#94a3b8' }}>
                {summary.trading_guidance}
              </p>
            </div>
          )}

          {summary.key_risk && (
            <div className="mt-2 flex items-start gap-1.5">
              <span className="text-xs font-black shrink-0" style={{ color: '#ff1744' }}>⚠</span>
              <p className="text-xs leading-relaxed" style={{ color: '#64748b' }}>
                <span className="font-semibold" style={{ color: '#ff1744' }}>Key risk: </span>
                {summary.key_risk}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function parsePublishedAt(raw: string): number {
  if (!raw) return 0
  const ts = Number(raw)
  if (!isNaN(ts) && ts > 1_000_000_000) return ts * 1000
  const d = new Date(raw)
  return isNaN(d.getTime()) ? 0 : d.getTime()
}

function BreakingNewsPanel({ items, cachedAt }: { items?: NewsItem[]; cachedAt?: number }) {
  if (!items || items.length === 0) return null
  // (empty-after-filter check happens after sorted is computed below)

  const cutoff = Date.now() - 48 * 60 * 60 * 1000
  const recent = items.filter(item => {
    const ms = parsePublishedAt(item.published_at)
    return ms === 0 || ms >= cutoff  // keep unparseable dates
  })

  const sorted = [...recent].sort((a, b) => {
    // Market movers first within the same recency bucket, then sort by time
    const tsDiff = parsePublishedAt(b.published_at) - parsePublishedAt(a.published_at)
    if (Math.abs(tsDiff) < 30 * 60 * 1000) {
      // within 30 min window — surface market movers first
      if (a.market_mover && !b.market_mover) return -1
      if (!a.market_mover && b.market_mover) return 1
    }
    return tsDiff
  }).slice(0, 10)

  if (sorted.length === 0) return (
    <div className="rounded-xl border p-4 text-center" style={{ backgroundColor: '#0d1117', borderColor: 'rgba(255,255,255,0.06)' }}>
      <p className="text-xs" style={{ color: '#475569' }}>No news in the last 48 hours — feeds refreshing</p>
    </div>
  )

  const cacheAge = cachedAt
    ? Math.floor((Date.now() - cachedAt * 1000) / 60000)
    : null

  return (
    <div
      className="rounded-xl border overflow-hidden"
      style={{ backgroundColor: '#0d1117', borderColor: 'rgba(255,255,255,0.06)' }}
    >
      <div
        className="px-4 py-2.5 flex items-center justify-between border-b"
        style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
      >
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: '#ff1744' }} />
          <span className="text-xs font-bold uppercase tracking-wide" style={{ color: '#e2e8f0' }}>
            Breaking News
          </span>
        </div>
        {cacheAge !== null && (
          <span className="text-xs" style={{ color: '#334155' }}>
            {cacheAge < 1 ? 'live' : `${cacheAge}m ago`}
          </span>
        )}
      </div>

      <div className="divide-y" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
        {sorted.map((item, i) => {
          const sentColor = SENT_COLOR[item.sentiment] ?? '#ffab00'
          const age = formatNewsAge(item.published_at)
          return (
            <a
              key={i}
              href={item.url || '#'}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-start gap-2.5 px-4 py-2.5 hover:bg-white/[0.02] transition-colors block"
              style={{ textDecoration: 'none' }}
            >
              <span
                className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0"
                style={{ backgroundColor: sentColor }}
              />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium leading-snug" style={{ color: item.market_mover ? '#e2e8f0' : '#94a3b8' }}>
                  {item.title}
                  {item.market_mover && (
                    <span className="ml-1 text-xs" style={{ color: '#ffd700' }}>★</span>
                  )}
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <span
                    className="text-xs px-1.5 py-0.5 rounded"
                    style={{ backgroundColor: 'rgba(255,255,255,0.04)', color: '#475569' }}
                  >
                    {item.source}
                  </span>
                  {age && (
                    <span className="text-xs" style={{ color: '#334155' }}>{age}</span>
                  )}
                </div>
              </div>
            </a>
          )
        })}
      </div>
    </div>
  )
}

function DriverCard({ driver }: { driver: DailyDriver }) {
  const navigate = useNavigate()
  const dirColor = DIR_COLOR[driver.direction] ?? '#ffab00'
  const rankColor = RANK_COLORS[driver.rank - 1] ?? '#94a3b8'
  const typeLabel = TYPE_LABELS[driver.type] ?? driver.type

  return (
    <div
      className="rounded-xl border p-4 flex flex-col gap-2.5"
      style={{
        backgroundColor: '#111827',
        borderColor: `${dirColor}30`,
        background: `linear-gradient(135deg, ${dirColor}08, #111827 55%)`,
      }}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-base font-black tabular-nums" style={{ color: rankColor }}>
            #{driver.rank}
          </span>
          <span
            className="text-xs font-semibold px-2 py-0.5 rounded-full"
            style={{ backgroundColor: 'rgba(255,255,255,0.06)', color: '#94a3b8' }}
          >
            {typeLabel}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          {driver.impact === 'HIGH' && (
            <span
              className="text-xs font-bold px-1.5 py-0.5 rounded"
              style={{ backgroundColor: 'rgba(255,171,0,0.12)', color: '#ffab00' }}
            >
              HIGH
            </span>
          )}
          <span
            className="text-xs font-bold px-2 py-0.5 rounded"
            style={{ backgroundColor: `${dirColor}15`, color: dirColor }}
          >
            {driver.direction === 'bullish' ? '▲ Bullish' : driver.direction === 'bearish' ? '▼ Bearish' : '◆ Neutral'}
          </span>
        </div>
      </div>

      <div className="text-sm font-bold leading-snug" style={{ color: '#e2e8f0' }}>
        {driver.title}
        {driver.ticker && (
          <button
            onClick={() => navigate(`/analysis?ticker=${driver.ticker}`)}
            className="ml-2 text-xs font-mono font-semibold hover:opacity-80 transition-opacity"
            style={{ color: '#00d4ff' }}
          >
            {driver.ticker} →
          </button>
        )}
      </div>

      <p className="text-xs leading-relaxed" style={{ color: '#64748b' }}>
        {driver.why}
      </p>
    </div>
  )
}

export default function DailyDrivers() {
  const queryClient = useQueryClient()
  const [refreshing, setRefreshing] = useState(false)

  const { data, isLoading, isError, refetch } = useQuery<DailyDriversResponse>({
    queryKey: ['daily-drivers'],
    queryFn: marketPulseApi.dailyDrivers,
    staleTime: 14 * 60_000,
    retry: 2,
  })

  const { data: newsData } = useQuery<{ items: NewsItem[]; cached_at: number }>({
    queryKey: ['news-market'],
    queryFn: newsApi.market,
    staleTime: 60_000,
    refetchInterval: 90_000,
  })

  const handleForceRefresh = async () => {
    setRefreshing(true)
    try {
      const fresh = await marketPulseApi.refreshDrivers()
      queryClient.setQueryData(['daily-drivers'], fresh)
    } catch {
      refetch()
    } finally {
      setRefreshing(false)
    }
  }

  const sectionHeader = (
    <div className="flex items-center gap-2 mb-3">
      <span className="text-sm font-black" style={{ color: '#ffd700' }}>⚡</span>
      <h2 className="text-sm font-bold uppercase tracking-wide" style={{ color: '#e2e8f0' }}>
        Today's Market Intelligence
      </h2>
    </div>
  )

  if (isLoading) {
    return (
      <div>
        {sectionHeader}
        <div className="flex flex-col gap-3">
          <Skeleton style={{ height: 120 }} />
          <Skeleton style={{ height: 200 }} />
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <Skeleton style={{ height: 100 }} />
            <Skeleton style={{ height: 100 }} />
            <Skeleton style={{ height: 100 }} />
          </div>
        </div>
      </div>
    )
  }

  if (isError || !data?.drivers?.length) {
    return (
      <div>
        {sectionHeader}
        <div
          className="rounded-xl border p-4 flex items-center justify-between"
          style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
        >
          <span className="text-xs" style={{ color: '#475569' }}>
            Market intelligence unavailable — AI analysis will retry shortly
          </span>
          <button
            onClick={() => handleForceRefresh()}
            disabled={refreshing}
            className="text-xs font-semibold px-3 py-1.5 rounded-lg disabled:opacity-40"
            style={{ backgroundColor: 'rgba(0,212,255,0.1)', color: '#00d4ff' }}
          >
            {refreshing ? 'Refreshing…' : 'Retry'}
          </button>
        </div>
        {newsData && (
          <div className="mt-3">
            <BreakingNewsPanel items={newsData.items} cachedAt={newsData.cached_at} />
          </div>
        )}
      </div>
    )
  }

  return (
    <div>
      {sectionHeader}

      {data.summary && (
        <div className="mb-3">
          <SummaryCard
            summary={data.summary}
            generated_at={data.generated_at}
            cache_ttl_min={data.cache_ttl_min}
            onRefresh={handleForceRefresh}
            refreshing={refreshing}
          />
        </div>
      )}

      {newsData && (
        <div className="mb-3">
          <BreakingNewsPanel items={newsData.items} cachedAt={newsData.cached_at} />
        </div>
      )}

      <div>
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: '#475569' }}>
            AI-Ranked Drivers
          </span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {data.drivers.map(d => <DriverCard key={d.rank} driver={d} />)}
        </div>
      </div>
    </div>
  )
}
