import { useQuery } from '@tanstack/react-query'
import { marketPulseApi } from '../../services/api'
import { useNavigate } from 'react-router-dom'

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
  drivers: DailyDriver[]
  as_of: string
}

const TYPE_LABELS: Record<string, string> = {
  earnings: 'Earnings',
  macro: 'Macro',
  fed: 'Fed',
  rates: 'Rates',
  geopolitical: 'Geopolitical',
  technical: 'Technical',
  sentiment: 'Sentiment',
}

const DIRECTION_COLORS = {
  bullish: '#00e676',
  bearish: '#ff1744',
  neutral: '#ffab00',
}

const DIRECTION_LABELS = {
  bullish: '▲ Bullish',
  bearish: '▼ Bearish',
  neutral: '◆ Neutral',
}

const RANK_LABELS = ['#1', '#2', '#3']
const RANK_COLORS = ['#ffd700', '#c0c0c0', '#cd7f32']

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

function DriverCard({ driver }: { driver: DailyDriver }) {
  const navigate = useNavigate()
  const dirColor = DIRECTION_COLORS[driver.direction] ?? '#ffab00'
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
      {/* Header row */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-base font-black tabular-nums" style={{ color: rankColor }}>
            {RANK_LABELS[driver.rank - 1]}
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
            <span className="text-xs font-bold px-1.5 py-0.5 rounded"
              style={{ backgroundColor: 'rgba(255,171,0,0.12)', color: '#ffab00' }}>
              HIGH
            </span>
          )}
          <span className="text-xs font-bold px-2 py-0.5 rounded"
            style={{ backgroundColor: `${dirColor}15`, color: dirColor }}>
            {DIRECTION_LABELS[driver.direction]}
          </span>
        </div>
      </div>

      {/* Title */}
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

      {/* Why */}
      <p className="text-xs leading-relaxed" style={{ color: '#64748b' }}>
        {driver.why}
      </p>
    </div>
  )
}

export default function DailyDrivers() {
  const { data, isLoading } = useQuery<DailyDriversResponse>({
    queryKey: ['daily-drivers'],
    queryFn: marketPulseApi.dailyDrivers,
    staleTime: 25 * 60 * 1000,
    retry: 1,
  })

  if (isLoading) {
    return (
      <div>
        <div className="flex items-center gap-2 mb-3">
          <span className="text-sm font-black" style={{ color: '#ffd700' }}>⚡</span>
          <h2 className="text-sm font-bold uppercase tracking-wide" style={{ color: '#e2e8f0' }}>
            Today's Top 3 Market Drivers
          </h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <DriverSkeleton /><DriverSkeleton /><DriverSkeleton />
        </div>
      </div>
    )
  }

  if (!data?.drivers?.length) return null

  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <span className="text-sm font-black" style={{ color: '#ffd700' }}>⚡</span>
        <h2 className="text-sm font-bold uppercase tracking-wide" style={{ color: '#e2e8f0' }}>
          Today's Top 3 Market Drivers
        </h2>
        <span className="text-xs ml-auto" style={{ color: '#334155' }}>
          {data.as_of} · refreshes every 30min
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {data.drivers.map(d => <DriverCard key={d.rank} driver={d} />)}
      </div>
    </div>
  )
}
