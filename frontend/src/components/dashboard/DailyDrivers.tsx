import { useQuery, useQueryClient } from '@tanstack/react-query'
import { marketPulseApi } from '../../services/api'
import { useNavigate } from 'react-router-dom'
import { useState } from 'react'

interface MarketSummary {
  bias: 'UP' | 'DOWN' | 'HOLD'
  outlook: 'bullish' | 'bearish' | 'mixed' | 'neutral'
  confidence: 'HIGH' | 'MEDIUM' | 'LOW'
  narrative: string
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
  generated_at: string   // ISO UTC timestamp
  cache_ttl_min: number
}

const TYPE_LABELS: Record<string, string> = {
  earnings: 'Earnings', macro: 'Macro', fed: 'Fed', rates: 'Rates',
  geopolitical: 'Geopolitical', technical: 'Technical', sentiment: 'Sentiment',
}

const DIR_COLOR: Record<string, string> = {
  bullish: '#00e676', bearish: '#ff1744', neutral: '#ffab00',
  UP: '#00e676', DOWN: '#ff1744', HOLD: '#ffab00', mixed: '#ffab00',
}

const RANK_COLORS = ['#ffd700', '#c0c0c0', '#cd7f32']

const BIAS_ICON: Record<string, string> = { UP: '▲', DOWN: '▼', HOLD: '◆' }
const BIAS_LABEL: Record<string, string> = { UP: 'Market likely UP today', DOWN: 'Market likely DOWN today', HOLD: 'Mixed signals — hold cautious' }

function DriverSkeleton() {
  return (
    <div className="rounded-xl border p-4 flex flex-col gap-3 animate-pulse"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
      <div className="h-3 w-16 rounded" style={{ backgroundColor: 'rgba(255,255,255,0.06)' }} />
      <div className="h-4 w-full rounded" style={{ backgroundColor: 'rgba(255,255,255,0.06)' }} />
      <div className="h-3 w-5/6 rounded" style={{ backgroundColor: 'rgba(255,255,255,0.04)' }} />
    </div>
  )
}

function SummarySkeleton() {
  return (
    <div className="rounded-xl border p-5 mb-3 animate-pulse"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
      <div className="flex items-center gap-4">
        <div className="h-10 w-10 rounded-lg" style={{ backgroundColor: 'rgba(255,255,255,0.06)' }} />
        <div className="flex-1 flex flex-col gap-2">
          <div className="h-4 w-48 rounded" style={{ backgroundColor: 'rgba(255,255,255,0.06)' }} />
          <div className="h-3 w-full rounded" style={{ backgroundColor: 'rgba(255,255,255,0.04)' }} />
          <div className="h-3 w-4/5 rounded" style={{ backgroundColor: 'rgba(255,255,255,0.04)' }} />
        </div>
      </div>
    </div>
  )
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
      className="rounded-xl border p-5 mb-3"
      style={{
        backgroundColor: '#0d1520',
        borderColor: `${color}40`,
        background: `linear-gradient(135deg, ${color}10 0%, #0d1520 50%)`,
      }}
    >
      <div className="flex items-start gap-4">
        {/* Bias badge */}
        <div
          className="flex-shrink-0 w-14 h-14 rounded-xl flex flex-col items-center justify-center"
          style={{ backgroundColor: `${color}18`, border: `1.5px solid ${color}50` }}
        >
          <span className="text-xl font-black leading-none" style={{ color }}>{icon}</span>
          <span className="text-xs font-black mt-0.5" style={{ color }}>{summary.bias}</span>
        </div>

        {/* Text */}
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
              <span className="text-xs" style={{ color: '#334155' }}>
                {age} · auto-refresh every {cache_ttl_min}min
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
        </div>
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
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full"
            style={{ backgroundColor: 'rgba(255,255,255,0.06)', color: '#94a3b8' }}>
            {typeLabel}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          {driver.impact === 'HIGH' && (
            <span className="text-xs font-bold px-1.5 py-0.5 rounded"
              style={{ backgroundColor: 'rgba(255,171,0,0.12)', color: '#ffab00' }}>
              HIGH
            </span>
          )}
          <span className="text-xs font-bold px-2 py-0.5 rounded"
            style={{ backgroundColor: `${dirColor}15`, color: dirColor }}>
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
    staleTime: 18 * 60 * 1000,  // slightly under 20min TTL so refetch fires before cache expires
    retry: 2,
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
        <SummarySkeleton />
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <DriverSkeleton /><DriverSkeleton /><DriverSkeleton />
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
      </div>
    )
  }

  return (
    <div>
      {sectionHeader}
      {data.summary && (
        <SummaryCard
          summary={data.summary}
          generated_at={data.generated_at}
          cache_ttl_min={data.cache_ttl_min}
          onRefresh={handleForceRefresh}
          refreshing={refreshing}
        />
      )}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {data.drivers.map(d => <DriverCard key={d.rank} driver={d} />)}
      </div>
    </div>
  )
}
