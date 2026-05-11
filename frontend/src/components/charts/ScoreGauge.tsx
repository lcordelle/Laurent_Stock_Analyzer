import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer } from 'recharts'
import { scoreColor } from '../../lib/formatters'

interface ScoreGaugeProps {
  score: number
}

export default function ScoreGauge({ score }: ScoreGaugeProps) {
  const color = scoreColor(score)
  const data = [{ value: score, fill: color }]

  return (
    <div
      className="rounded-xl border p-5 flex flex-col items-center justify-center"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
      data-testid="score-gauge"
      role="img"
      aria-label={`Score gauge: ${Math.round(score)} out of 100`}
    >
      <h3 className="text-sm font-semibold uppercase tracking-wide mb-4 self-start" style={{ color: '#94a3b8' }}>
        Score Gauge
      </h3>
      <div style={{ width: '100%', height: 200, position: 'relative' }}>
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%"
            cy="50%"
            innerRadius="60%"
            outerRadius="90%"
            barSize={14}
            data={data}
            startAngle={180}
            endAngle={0}
          >
            <PolarAngleAxis
              type="number"
              domain={[0, 100]}
              angleAxisId={0}
              tick={false}
            />
            <RadialBar
              background={{ fill: '#1a2235' }}
              dataKey="value"
              angleAxisId={0}
              cornerRadius={7}
            />
          </RadialBarChart>
        </ResponsiveContainer>
        <div
          style={{
            position: 'absolute',
            bottom: '10%',
            left: 0,
            right: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <span className="text-4xl font-bold tabular-nums" style={{ color }}>
            {Math.round(score)}
          </span>
          <span className="text-xs mt-0.5" style={{ color: '#475569' }}>/ 100</span>
        </div>
      </div>
    </div>
  )
}
