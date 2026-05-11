import { useQuery } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { gradesApi } from '../../services/api'
import type { FactorGradesResponse, GradeItem } from '../../lib/types'

const GRADE_COLORS: Record<string, string> = {
  'A+': '#15803d', 'A': '#16a34a', 'A-': '#22c55e',
  'B+': '#65a30d', 'B': '#84cc16', 'B-': '#a3e635',
  'C+': '#ca8a04', 'C': '#d97706', 'C-': '#f59e0b',
  'D+': '#ea580c', 'D': '#dc2626', 'D-': '#b91c1c',
  'F': '#7f1d1d', 'N/A': '#475569',
}

const FACTORS: { key: keyof FactorGradesResponse['grades']; label: string }[] = [
  { key: 'value', label: 'Value' },
  { key: 'growth', label: 'Growth' },
  { key: 'profitability', label: 'Profit.' },
  { key: 'momentum', label: 'Momentum' },
  { key: 'eps_revisions', label: 'EPS Rev.' },
]

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
      {item.percentile != null && (
        <span className="text-xs" style={{ color: '#475569' }}>{item.percentile.toFixed(0)}th</span>
      )}
    </div>
  )
}

interface Props {
  ticker: string
  sector: string
}

export default function FactorGrades({ ticker, sector }: Props) {
  const { data, isLoading, isError } = useQuery<FactorGradesResponse>({
    queryKey: ['factor-grades', ticker, sector],
    queryFn: () => gradesApi.factors(ticker, sector),
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
          Factor Grades
        </h3>
        {data && (
          <span className="text-xs" style={{ color: '#475569' }}>
            vs {data.n_peers} peers · {data.sector}
          </span>
        )}
      </div>

      {isLoading && (
        <div className="flex items-center gap-2 py-4" style={{ color: '#475569' }}>
          <Loader2 size={14} className="animate-spin" />
          <span className="text-xs">Computing sector-relative grades…</span>
        </div>
      )}

      {isError && (
        <p className="text-xs py-2" style={{ color: '#475569' }}>Grades unavailable</p>
      )}

      {data && (
        <div className="flex justify-around">
          {FACTORS.map(({ key, label }) => (
            <GradePill key={key} item={data.grades[key]} label={label} />
          ))}
        </div>
      )}
    </div>
  )
}
