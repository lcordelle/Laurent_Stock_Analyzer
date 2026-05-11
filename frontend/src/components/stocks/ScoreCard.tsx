import type { ScoreBreakdown } from '../../lib/types'
import { scoreColor } from '../../lib/formatters'

const COMPONENT_MAX: Record<string, number> = {
  'Gross Margin': 25,
  'ROE': 20,
  'FCF Margin': 20,
  'Valuation': 20,
  'Growth': 15,
}

const RECOMMENDATION_LABELS: [number, string][] = [
  [75, 'Strong Buy'],
  [60, 'Buy'],
  [45, 'Hold'],
  [30, 'Reduce'],
  [0, 'Sell'],
]

function getRecommendation(score: number): string {
  for (const [threshold, label] of RECOMMENDATION_LABELS) {
    if (score >= threshold) return label
  }
  return 'Sell'
}

const REC_COLORS: Record<string, string> = {
  'Strong Buy': '#00e676',
  'Buy': '#00e676',
  'Hold': '#ffab00',
  'Reduce': '#ff1744',
  'Sell': '#ff1744',
}

interface ScoreCardProps {
  score: ScoreBreakdown
}

export default function ScoreCard({ score }: ScoreCardProps) {
  const total = score.total
  const color = scoreColor(total)
  const recommendation = getRecommendation(total)

  return (
    <div
      className="rounded-xl border p-5 flex flex-col gap-4"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
      data-testid="score-card"
    >
      <div className="flex items-center justify-between">
        <span className="text-sm font-semibold uppercase tracking-wide" style={{ color: '#94a3b8' }}>
          VF Score
        </span>
        <span
          className="text-xs font-bold px-2 py-0.5 rounded"
          style={{ color: REC_COLORS[recommendation] ?? '#94a3b8', backgroundColor: `${REC_COLORS[recommendation] ?? '#94a3b8'}20` }}
        >
          {recommendation}
        </span>
      </div>

      <div className="flex items-end gap-2">
        <span className="text-5xl font-bold tabular-nums" style={{ color }}>
          {Math.round(total)}
        </span>
        <span className="text-lg mb-1" style={{ color: '#475569' }}>/100</span>
      </div>

      <div className="flex flex-col gap-3">
        {Object.entries(score.components).map(([key, val]) => {
          const max = COMPONENT_MAX[key] ?? 20
          const pct = Math.min(100, (val / max) * 100)
          return (
            <div key={key} className="flex flex-col gap-1">
              <div className="flex justify-between text-xs" style={{ color: '#94a3b8' }}>
                <span>{key}</span>
                <span>{val.toFixed(1)} / {max}</span>
              </div>
              <div className="h-1.5 rounded-full" style={{ backgroundColor: '#1a2235' }}>
                <div
                  className="h-1.5 rounded-full transition-all"
                  style={{ width: `${pct}%`, backgroundColor: scoreColor(pct) }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
