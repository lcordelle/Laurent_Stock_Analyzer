import { useState } from 'react'
import type { Decision, Calibration } from '../../lib/types'
import { computeSizing } from '../../lib/sizing'

interface Props {
  decision: Decision
  calibration?: Calibration
  entry: number | null
  stop: number | null
  currentPrice: number | null
}

const DIR_COLOR: Record<string, string> = {
  'Long': '#00e676', 'Short': '#ff1744', 'Stand aside': '#ffab00',
}

function num(v: string, fallback: number): number {
  const n = parseFloat(v.replace(/[^0-9.]/g, ''))
  return isNaN(n) ? fallback : n
}

export default function DecisionPanel({ decision, calibration, entry, stop, currentPrice }: Props) {
  const [equity, setEquity] = useState<number>(() => num(localStorage.getItem('decision.accountSize') ?? '', 100000))
  const [maxRisk, setMaxRisk] = useState<number>(() => num(localStorage.getItem('decision.maxRiskPct') ?? '', 1))

  const saveEquity = (v: number) => { setEquity(v); localStorage.setItem('decision.accountSize', String(v)) }
  const saveRisk = (v: number) => { setMaxRisk(v); localStorage.setItem('decision.maxRiskPct', String(v)) }

  const eff = entry ?? currentPrice
  const sizing = computeSizing({ equity, maxRiskPct: maxRisk, conviction: decision.conviction, entry: eff, stop })
  const dirColor = DIR_COLOR[decision.direction] ?? '#94a3b8'
  const usd = (n: number) => `$${Math.round(n).toLocaleString()}`

  return (
    <div className="rounded-xl border p-5 flex flex-col gap-4"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: '#475569' }}>Decision</span>
          <span className="text-sm font-black px-3 py-1 rounded-lg"
            style={{ backgroundColor: dirColor + '22', color: dirColor }}>{decision.direction}</span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-black tabular-nums" style={{ color: dirColor }}>{decision.conviction.toFixed(1)}</span>
          <span className="text-xs" style={{ color: '#475569' }}>/ 10 conviction</span>
        </div>
      </div>

      <div className="text-xs" style={{ color: '#94a3b8' }}>{decision.rationale}</div>

      {/* Factor breakdown */}
      <div className="flex flex-col gap-1.5">
        {decision.factors.map(f => {
          const c = f.contribution ?? 0
          const pos = c >= 0
          return (
            <div key={f.label} className="flex items-center gap-2 text-xs">
              <span className="w-24 shrink-0" style={{ color: '#94a3b8' }}>{f.label}</span>
              <div className="flex-1 h-2 rounded-full relative" style={{ backgroundColor: 'rgba(255,255,255,0.05)' }}>
                <div className="absolute top-0 h-2 rounded-full"
                  style={{ left: '50%', width: `${Math.min(Math.abs(c) * 200, 50)}%`,
                    transform: pos ? 'none' : 'translateX(-100%)',
                    backgroundColor: f.subscore == null ? '#475569' : pos ? '#00e676' : '#ff1744' }} />
              </div>
              <span className="w-40 shrink-0 text-right truncate" style={{ color: '#475569' }}>
                {f.subscore == null ? 'n/a' : f.detail}
              </span>
            </div>
          )
        })}
        <div className="flex items-center gap-2 text-xs mt-1">
          <span className="w-24 shrink-0" style={{ color: '#94a3b8' }}>Regime</span>
          <span style={{ color: '#cbd5e1' }}>
            {decision.regime.label}{decision.regime.vix != null ? ` · VIX ${decision.regime.vix}` : ''} · ×{decision.regime.multiplier}
          </span>
        </div>
        {decision.expected_value_r != null && (
          <div className="flex items-center gap-2 text-xs">
            <span className="w-24 shrink-0" style={{ color: '#94a3b8' }}>Expected value</span>
            <span style={{ color: decision.expected_value_r >= 0 ? '#00e676' : '#ff1744' }}>
              {decision.expected_value_r >= 0 ? '+' : ''}{decision.expected_value_r}R
            </span>
          </div>
        )}
        {calibration?.available && calibration.hit_rate != null && (
          <div className="flex items-start gap-2 text-xs mt-1">
            <span className="w-24 shrink-0" style={{ color: '#94a3b8' }}>Track record</span>
            <span style={{ color: '#cbd5e1' }}>
              Timing signal here (proxy {calibration.proxy_conviction}/10):{' '}
              <span style={{ color: calibration.low_sample ? '#94a3b8' : (calibration.hit_rate ?? 0) >= 50 ? '#00e676' : '#ff1744', fontWeight: 700 }}>
                {calibration.hit_rate}% up
              </span>{' '}over {calibration.horizon_days}d, avg{' '}
              <span style={{ color: (calibration.avg_forward_return ?? 0) >= 0 ? '#00e676' : '#ff1744' }}>
                {(calibration.avg_forward_return ?? 0) >= 0 ? '+' : ''}{calibration.avg_forward_return}%
              </span>{' '}
              <span style={{ color: '#475569' }}>(n={calibration.n}, as-of {calibration.as_of})</span>
              {calibration.low_sample && <span style={{ color: '#ffab00' }}> · small sample, low confidence</span>}
              <span className="block" style={{ color: '#334155' }}>Ex-fundamentals · S&P 100 · overlapping windows</span>
            </span>
          </div>
        )}
        {calibration && !calibration.available && (
          <div className="flex items-center gap-2 text-xs mt-1">
            <span className="w-24 shrink-0" style={{ color: '#94a3b8' }}>Track record</span>
            <span style={{ color: '#475569' }}>{calibration.note}</span>
          </div>
        )}
      </div>

      {/* Position sizing */}
      <div className="border-t pt-3 mt-1" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
        <div className="flex items-center gap-3 flex-wrap mb-2">
          <label className="text-xs flex items-center gap-1" style={{ color: '#475569' }}>
            Account $
            <input type="text" defaultValue={String(equity)} onBlur={e => saveEquity(num(e.target.value, equity))}
              className="w-28 px-2 py-1 rounded text-xs tabular-nums"
              style={{ backgroundColor: '#0a0e1a', color: '#e2e8f0', border: '1px solid rgba(255,255,255,0.08)' }} />
          </label>
          <label className="text-xs flex items-center gap-1" style={{ color: '#475569' }}>
            Max risk %
            <input type="text" defaultValue={String(maxRisk)} onBlur={e => saveRisk(num(e.target.value, maxRisk))}
              className="w-16 px-2 py-1 rounded text-xs tabular-nums"
              style={{ backgroundColor: '#0a0e1a', color: '#e2e8f0', border: '1px solid rgba(255,255,255,0.08)' }} />
          </label>
        </div>
        {sizing.ok ? (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <SizeStat label="Shares" value={sizing.shares.toLocaleString()} />
            <SizeStat label="Position" value={usd(sizing.positionDollars)} sub={`${sizing.pctOfEquity.toFixed(1)}% of acct`} />
            <SizeStat label="At risk" value={usd(sizing.riskDollars)} sub={`${sizing.riskPct.toFixed(2)}% risk`} />
            <SizeStat label="Conv-scaled" value={`${(decision.conviction * 10).toFixed(0)}% of max`} sub={sizing.capped ? 'capped (no leverage)' : ''} />
          </div>
        ) : (
          <div className="text-xs" style={{ color: '#ffab00' }}>{sizing.reason}</div>
        )}
      </div>
    </div>
  )
}

function SizeStat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="flex flex-col px-3 py-2 rounded-lg" style={{ backgroundColor: '#0a0e1a' }}>
      <span className="text-xs uppercase tracking-wide" style={{ color: '#475569' }}>{label}</span>
      <span className="text-sm font-bold tabular-nums" style={{ color: '#e2e8f0' }}>{value}</span>
      {sub ? <span className="text-xs" style={{ color: '#475569' }}>{sub}</span> : null}
    </div>
  )
}
