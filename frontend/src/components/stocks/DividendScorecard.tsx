import { useQuery } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { gradesApi } from '../../services/api'
import type { DividendScorecardResponse, GradeItem } from '../../lib/types'

const GRADE_COLORS: Record<string, string> = {
  'A+': '#15803d', 'A': '#16a34a', 'A-': '#22c55e',
  'B+': '#65a30d', 'B': '#84cc16', 'B-': '#a3e635',
  'C+': '#ca8a04', 'C': '#d97706', 'C-': '#f59e0b',
  'D+': '#ea580c', 'D': '#dc2626', 'D-': '#b91c1c',
  'F': '#7f1d1d', 'N/A': '#475569',
}

function GradePill({ item, label }: { item: GradeItem; label: string }) {
  const color = GRADE_COLORS[item.grade] ?? GRADE_COLORS['N/A']
  return (
    <div className="flex flex-col items-center gap-1.5" title={item.tooltip ?? ''}>
      <div
        className="w-12 h-12 rounded-full flex items-center justify-center font-black text-sm"
        style={{ backgroundColor: `${color}25`, border: `2px solid ${color}`, color }}
      >
        {item.grade}
      </div>
      <span className="text-xs text-center" style={{ color: '#94a3b8' }}>{label}</span>
    </div>
  )
}

interface Props {
  ticker: string
  sector: string
}

export default function DividendScorecard({ ticker, sector }: Props) {
  const { data, isLoading, isError } = useQuery<DividendScorecardResponse>({
    queryKey: ['dividend-scorecard', ticker, sector],
    queryFn: () => gradesApi.dividend(ticker, sector),
    enabled: !!ticker,
    staleTime: 60 * 60_000,
    retry: 1,
  })

  return (
    <div
      className="rounded-xl border p-5"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color: '#94a3b8' }}>
          Dividend Scorecard
        </h3>
        {data?.current_yield && (
          <span className="text-xs font-semibold" style={{ color: '#00d4ff' }}>
            {(data.current_yield * 100).toFixed(2)}% yield
          </span>
        )}
      </div>

      {isLoading && (
        <div className="flex items-center gap-2 py-4" style={{ color: '#475569' }}>
          <Loader2 size={14} className="animate-spin" />
          <span className="text-xs">Loading dividend data…</span>
        </div>
      )}

      {isError && (
        <p className="text-xs py-2" style={{ color: '#475569' }}>Dividend data unavailable</p>
      )}

      {data && !data.pays_dividend && (
        <div className="flex items-center gap-3 py-2">
          <div
            className="w-12 h-12 rounded-full flex items-center justify-center font-bold text-xs"
            style={{ backgroundColor: '#47556920', border: '2px solid #475569', color: '#475569' }}
          >
            N/A
          </div>
          <p className="text-xs" style={{ color: '#475569' }}>Does not pay a dividend</p>
        </div>
      )}

      {data?.pays_dividend && data.grades && (
        <div className="flex justify-around">
          <GradePill item={data.grades.safety} label="Safety" />
          <GradePill item={data.grades.growth} label="Growth" />
          <GradePill item={data.grades.yield_grade} label="Yield" />
          <GradePill item={data.grades.consistency} label="Consist." />
        </div>
      )}
    </div>
  )
}
