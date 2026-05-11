import { useQuery } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ReferenceLine, ResponsiveContainer, Cell } from 'recharts'
import { gradesApi } from '../../services/api'
import type { EarningsAnalysisResponse } from '../../lib/types'

interface Props {
  ticker: string
}

export default function EarningsPanel({ ticker }: Props) {
  const { data, isLoading, isError } = useQuery<EarningsAnalysisResponse>({
    queryKey: ['earnings', ticker],
    queryFn: () => gradesApi.earnings(ticker),
    enabled: !!ticker,
    staleTime: 30 * 60_000,
    retry: 1,
  })

  return (
    <div
      className="rounded-xl border p-5 flex flex-col gap-4"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
    >
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color: '#94a3b8' }}>
          EPS Surprise History
        </h3>
        {data?.beat_rate_4q != null && (
          <span className="text-xs font-semibold px-2 py-0.5 rounded" style={{ backgroundColor: '#00d4ff15', color: '#00d4ff' }}>
            Beat rate {data.beat_rate_4q.toFixed(0)}% (4Q)
          </span>
        )}
      </div>

      {isLoading && (
        <div className="flex items-center gap-2 py-4" style={{ color: '#475569' }}>
          <Loader2 size={14} className="animate-spin" />
          <span className="text-xs">Loading earnings data…</span>
        </div>
      )}

      {isError && (
        <p className="text-xs py-2" style={{ color: '#475569' }}>Earnings data unavailable</p>
      )}

      {data && !data.data_available && (
        <p className="text-xs py-2" style={{ color: '#475569' }}>No earnings history available</p>
      )}

      {data?.data_available && data.eps_history.length > 0 && (() => {
        const chartData = data.eps_history
          .filter(e => e.surprise_pct != null)
          .slice(0, 8)
          .reverse()
          .map(e => ({
            quarter: e.date.slice(0, 7),
            surprise: e.surprise_pct ?? 0,
            beat: e.beat,
            actual: e.eps_actual,
            estimate: e.eps_estimate,
          }))

        const hasChart = chartData.length > 0

        return (
          <>
            {hasChart && (
              <ResponsiveContainer width="100%" height={160}>
                <BarChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                  <XAxis dataKey="quarter" tick={{ fontSize: 10, fill: '#475569' }} />
                  <YAxis tick={{ fontSize: 10, fill: '#475569' }} tickFormatter={v => `${v > 0 ? '+' : ''}${v.toFixed(0)}%`} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0a0e1a', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, fontSize: 11 }}
                    formatter={(value: unknown) => { const n = Number(value); return [`${n > 0 ? '+' : ''}${n.toFixed(1)}%`, 'EPS Surprise'] }}
                  />
                  <ReferenceLine y={0} stroke="rgba(255,255,255,0.1)" />
                  <Bar dataKey="surprise" radius={[3, 3, 0, 0]}>
                    {chartData.map((entry, i) => (
                      <Cell key={i} fill={entry.beat ? '#00e676' : '#ff1744'} fillOpacity={0.85} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}

            <div className="grid grid-cols-2 gap-2">
              {data.eps_history.slice(0, 4).map((e, i) => (
                <div
                  key={i}
                  className="rounded-lg p-2.5 text-xs"
                  style={{
                    backgroundColor: '#0a0e1a',
                    border: `1px solid ${e.beat ? '#00e67620' : e.beat === false ? '#ff174420' : 'rgba(255,255,255,0.04)'}`,
                  }}
                >
                  <div className="flex justify-between mb-1">
                    <span style={{ color: '#64748b' }}>{e.date.slice(0, 7)}</span>
                    {e.beat != null && (
                      <span className="font-semibold" style={{ color: e.beat ? '#00e676' : '#ff1744' }}>
                        {e.beat ? '✓ Beat' : '✗ Miss'}
                      </span>
                    )}
                  </div>
                  {e.eps_actual != null && (
                    <div className="flex justify-between">
                      <span style={{ color: '#475569' }}>Actual</span>
                      <span className="font-mono" style={{ color: '#e2e8f0' }}>${e.eps_actual.toFixed(2)}</span>
                    </div>
                  )}
                  {e.eps_estimate != null && (
                    <div className="flex justify-between">
                      <span style={{ color: '#475569' }}>Est.</span>
                      <span className="font-mono" style={{ color: '#64748b' }}>${e.eps_estimate.toFixed(2)}</span>
                    </div>
                  )}
                  {e.surprise_pct != null && (
                    <div className="flex justify-between">
                      <span style={{ color: '#475569' }}>Surprise</span>
                      <span className="font-semibold font-mono" style={{ color: e.surprise_pct >= 0 ? '#00e676' : '#ff1744' }}>
                        {e.surprise_pct > 0 ? '+' : ''}{e.surprise_pct.toFixed(1)}%
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {data.next_earnings_date && (
              <p className="text-xs" style={{ color: '#475569' }}>
                Next earnings: <span style={{ color: '#00d4ff' }}>{data.next_earnings_date}</span>
              </p>
            )}
          </>
        )
      })()}
    </div>
  )
}
