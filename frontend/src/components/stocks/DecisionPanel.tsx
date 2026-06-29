import { useState } from 'react'
import type { Decision } from '../../lib/types'
import { computeSizing } from '../../lib/sizing'

interface Props {
  decision: Decision
  entry: number | null
  stop: number | null
  currentPrice: number | null
}

const GRADE_COLOR: Record<string, string> = { A: '#00e676', B: '#84cc16', C: '#ffab00', D: '#ff7043', F: '#ff1744' }
const BAND_COLOR: Record<string, string> = { Prime: '#00e676', Strong: '#84cc16', Fair: '#ffab00', Weak: '#ff7043' }
const DIR_COLOR: Record<string, string> = { Long: '#00e676', Short: '#ff1744', 'Stand aside': '#ffab00' }
const ACTION_COLOR: Record<string, string> = { 'STRONG BUY': '#00e676', BUY: '#00e676', ACCUMULATE: '#84cc16', WATCH: '#ffab00', SPECULATIVE: '#ff7043', AVOID: '#ff1744' }

function num(v: string, fallback: number): number {
  const n = parseFloat(v.replace(/[^0-9.]/g, '')); return isNaN(n) ? fallback : n
}

export default function DecisionPanel({ decision, entry, stop, currentPrice }: Props) {
  const [equity, setEquity] = useState<number>(() => num(localStorage.getItem('decision.accountSize') ?? '', 100000))
  const [maxRisk, setMaxRisk] = useState<number>(() => num(localStorage.getItem('decision.maxRiskPct') ?? '', 1))
  const saveEquity = (v: number) => { setEquity(v); localStorage.setItem('decision.accountSize', String(v)) }
  const saveRisk = (v: number) => { setMaxRisk(v); localStorage.setItem('decision.maxRiskPct', String(v)) }

  const { quality, setup, read, action } = decision
  const gColor = GRADE_COLOR[quality.grade ?? ''] ?? '#94a3b8'
  const bColor = BAND_COLOR[setup.band ?? ''] ?? '#94a3b8'
  const dColor = DIR_COLOR[setup.direction] ?? '#94a3b8'
  const eff = entry ?? currentPrice
  const sizing = computeSizing({ equity, maxRiskPct: maxRisk, conviction: setup.score, entry: eff, stop })
  const usd = (n: number) => `$${Math.round(n).toLocaleString()}`

  return (
    <div className="rounded-xl border p-5 flex flex-col gap-4" style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
      <div className="flex items-start gap-3 flex-wrap">
        <span className="text-2xl font-black px-3 py-1 rounded-lg" style={{ backgroundColor: (ACTION_COLOR[action] ?? '#94a3b8') + '22', color: ACTION_COLOR[action] ?? '#94a3b8' }}>{action}</span>
        <span className="text-sm flex-1" style={{ color: '#cbd5e1', minWidth: '12rem' }}>{read}</span>
      </div>

      {/* Two axes */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Quality */}
        <div className="flex flex-col gap-1 px-4 py-3 rounded-xl" style={{ backgroundColor: '#0a0e1a' }}>
          <span className="text-xs uppercase tracking-wide" style={{ color: '#475569' }}>Quality (company)</span>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black" style={{ color: gColor }}>{quality.grade ?? '—'}</span>
            <span className="text-sm tabular-nums" style={{ color: '#94a3b8' }}>{quality.score ?? '—'}/100</span>
          </div>
        </div>
        {/* Setup */}
        <div className="flex flex-col gap-1 px-4 py-3 rounded-xl" style={{ backgroundColor: '#0a0e1a' }}>
          <span className="text-xs uppercase tracking-wide" style={{ color: '#475569' }}>Setup (entry timing)</span>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black" style={{ color: bColor }}>{setup.band ?? '—'}</span>
            <span className="text-sm font-bold px-2 py-0.5 rounded" style={{ backgroundColor: dColor + '22', color: dColor }}>{setup.direction}</span>
          </div>
          {setup.percentile != null && (
            <div className="flex items-center gap-2 mt-1">
              <div className="flex-1 h-1.5 rounded-full" style={{ backgroundColor: 'rgba(255,255,255,0.06)' }}>
                <div className="h-1.5 rounded-full" style={{ width: `${setup.percentile}%`, backgroundColor: bColor }} />
              </div>
              <span className="text-xs tabular-nums" style={{ color: '#475569' }}>{Math.round(setup.percentile)}th pct</span>
            </div>
          )}
          {setup.hit_rate != null && (
            <span className="text-xs mt-0.5" style={{ color: '#94a3b8' }}>
              {setup.hit_rate}% up · {(setup.avg_forward_return ?? 0) >= 0 ? '+' : ''}{setup.avg_forward_return}%/{setup.horizon_days}d
              <span style={{ color: '#475569' }}> (n={setup.n}{setup.low_sample ? ', small' : ''}, {setup.as_of})</span>
            </span>
          )}
        </div>
      </div>

      {/* Setup drivers */}
      <div className="flex flex-col gap-1.5">
        <span className="text-xs uppercase tracking-wide" style={{ color: '#475569' }}>Setup drivers</span>
        {setup.factors.map(f => {
          const c = f.contribution ?? 0; const pos = c >= 0
          return (
            <div key={f.label} className="flex items-center gap-2 text-xs">
              <span className="w-24 shrink-0" style={{ color: '#94a3b8' }}>{f.label}</span>
              <div className="flex-1 h-2 rounded-full relative" style={{ backgroundColor: 'rgba(255,255,255,0.05)' }}>
                <div className="absolute top-0 h-2 rounded-full" style={{ left: '50%', width: `${Math.min(Math.abs(c) * 200, 50)}%`, transform: pos ? 'none' : 'translateX(-100%)', backgroundColor: f.subscore == null ? '#475569' : pos ? '#00e676' : '#ff1744' }} />
              </div>
              <span className="w-40 shrink-0 text-right truncate" style={{ color: '#475569' }}>{f.subscore == null ? 'n/a' : f.detail}</span>
            </div>
          )
        })}
        <div className="flex items-center gap-2 text-xs mt-1">
          <span className="w-24 shrink-0" style={{ color: '#94a3b8' }}>Regime</span>
          <span style={{ color: '#cbd5e1' }}>{setup.regime.label}{setup.regime.vix != null ? ` · VIX ${setup.regime.vix}` : ''} · ×{setup.regime.multiplier}</span>
        </div>
        {setup.expected_value_r != null && (
          <div className="flex items-center gap-2 text-xs">
            <span className="w-24 shrink-0" style={{ color: '#94a3b8' }}>Expected value</span>
            <span style={{ color: setup.expected_value_r >= 0 ? '#00e676' : '#ff1744' }}>{setup.expected_value_r >= 0 ? '+' : ''}{setup.expected_value_r}R</span>
          </div>
        )}
        <span className="text-xs mt-1" style={{ color: '#334155' }}>Setup ex-fundamentals · percentile vs S&P 100 history · overlapping windows</span>
      </div>

      {/* Sizing */}
      <div className="border-t pt-3 mt-1" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
        <div className="flex items-center gap-3 flex-wrap mb-2">
          <label className="text-xs flex items-center gap-1" style={{ color: '#475569' }}>Account $
            <input type="text" defaultValue={String(equity)} onBlur={e => saveEquity(num(e.target.value, equity))} className="w-28 px-2 py-1 rounded text-xs tabular-nums" style={{ backgroundColor: '#0a0e1a', color: '#e2e8f0', border: '1px solid rgba(255,255,255,0.08)' }} />
          </label>
          <label className="text-xs flex items-center gap-1" style={{ color: '#475569' }}>Max risk %
            <input type="text" defaultValue={String(maxRisk)} onBlur={e => saveRisk(num(e.target.value, maxRisk))} className="w-16 px-2 py-1 rounded text-xs tabular-nums" style={{ backgroundColor: '#0a0e1a', color: '#e2e8f0', border: '1px solid rgba(255,255,255,0.08)' }} />
          </label>
        </div>
        {sizing.ok ? (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <SizeStat label="Shares" value={sizing.shares.toLocaleString()} />
            <SizeStat label="Position" value={usd(sizing.positionDollars)} sub={`${sizing.pctOfEquity.toFixed(1)}% of acct`} />
            <SizeStat label="At risk" value={usd(sizing.riskDollars)} sub={`${sizing.riskPct.toFixed(2)}% risk`} />
            <SizeStat label="Setup-scaled" value={`${(setup.score * 10).toFixed(0)}% of max`} sub={sizing.capped ? 'capped' : ''} />
          </div>
        ) : (<div className="text-xs" style={{ color: '#ffab00' }}>{sizing.reason}</div>)}
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
