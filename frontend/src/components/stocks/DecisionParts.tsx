import { useState } from 'react'
import type { Decision, HorizonDecision, Setup } from '../../lib/types'
import { computeSizing } from '../../lib/sizing'

export const GRADE_COLOR: Record<string, string> = { A: '#00e676', B: '#84cc16', C: '#ffab00', D: '#ff7043', F: '#ff1744' }
export const BAND_COLOR: Record<string, string> = { Prime: '#00e676', Strong: '#84cc16', Fair: '#ffab00', Weak: '#ff7043' }
export const DIR_COLOR: Record<string, string> = { Long: '#00e676', Short: '#ff1744', 'Stand aside': '#ffab00' }
export const ACTION_COLOR: Record<string, string> = { 'STRONG BUY': '#00e676', BUY: '#00e676', ACCUMULATE: '#84cc16', WATCH: '#ffab00', SPECULATIVE: '#ff7043', AVOID: '#ff1744' }
export const BAND_GLOSS: Record<string, string> = { Weak: 'poor entry right now', Fair: 'below-average timing', Strong: 'good entry', Prime: 'excellent entry' }

function num(v: string, fallback: number): number {
  const n = parseFloat(v.replace(/[^0-9.]/g, '')); return isNaN(n) ? fallback : n
}

// ── Compact full-width verdict bar: action · quality · setup · read ──────────
const HORIZON_LABELS: Record<string, string> = { day: 'Day', swing: 'Swing', long: 'Long' }
const HORIZON_ORDER = ['day', 'swing', 'long']

export function DecisionBar({ decision, horizon, setHorizon, hd }:
  { decision: Decision; horizon: string; setHorizon: (h: string) => void; hd: HorizonDecision }) {
  const { quality } = decision
  const { action, read, setup } = hd
  const aColor = ACTION_COLOR[action] ?? '#94a3b8'
  const gColor = GRADE_COLOR[quality.grade ?? ''] ?? '#94a3b8'
  const bColor = BAND_COLOR[setup.band ?? ''] ?? '#94a3b8'
  const dColor = DIR_COLOR[setup.direction] ?? '#94a3b8'
  return (
    <div className="rounded-xl border p-3 flex flex-col gap-2"
      style={{ backgroundColor: '#111827', borderColor: aColor + '33' }}>
      <div className="flex items-center gap-4 flex-wrap">
        <span className="text-2xl font-black px-3 py-1 rounded-lg shrink-0"
          style={{ backgroundColor: aColor + '22', color: aColor }}>{action}</span>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs uppercase tracking-wide" style={{ color: '#475569' }}>Quality</span>
          <span className="text-lg font-black" style={{ color: gColor }}>{quality.grade ?? '—'}</span>
          <span className="text-xs tabular-nums" style={{ color: '#94a3b8' }}>{quality.score ?? '—'}</span>
        </div>
        <div className="flex items-center gap-2 shrink-0 flex-wrap">
          <span className="text-xs uppercase tracking-wide cursor-help" style={{ color: '#475569' }}
            title="Entry timing — is now a good moment to buy? Scored from price action only: trend, momentum, and price vs its fair-value channel, adjusted for the market mood, then ranked against ~120k historical setups. Excludes company quality (that's the Quality axis).">Entry timing ⓘ</span>
          <span className="text-lg font-black" style={{ color: bColor }}>{setup.band ?? '—'}</span>
          {setup.band && <span className="text-xs" style={{ color: '#475569' }}>— {BAND_GLOSS[setup.band] ?? ''}</span>}
          <span className="text-xs font-bold px-1.5 py-0.5 rounded" style={{ backgroundColor: dColor + '22', color: dColor }}>{setup.direction}</span>
          {setup.percentile != null && <span className="text-xs tabular-nums" style={{ color: '#475569' }}>{Math.round(setup.percentile)}th pct · {setup.horizon_days}d</span>}
        </div>
        <div className="ml-auto flex rounded-lg overflow-hidden shrink-0" style={{ border: '1px solid rgba(255,255,255,0.08)' }}>
          {HORIZON_ORDER.filter(h => decision.horizons[h]).map(h => (
            <button key={h} onClick={() => setHorizon(h)} className="px-2.5 py-1 text-xs font-semibold transition-colors"
              style={{ backgroundColor: horizon === h ? '#00d4ff' : 'transparent', color: horizon === h ? '#0a0e1a' : '#94a3b8' }}>
              {HORIZON_LABELS[h] ?? h}
            </button>
          ))}
        </div>
      </div>
      <div className="flex items-start gap-2 text-sm" style={{ color: '#cbd5e1' }}>
        <span style={{ color: '#475569' }}>▸</span><span>{read}</span>
      </div>
    </div>
  )
}

// ── Setup drivers + regime + EV (rail section) ───────────────────────────────
export function SetupDrivers({ setup }: { setup: Setup }) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-xs uppercase tracking-wide" style={{ color: '#475569' }}>Entry-timing drivers</span>
      {setup.factors.map(f => {
        const c = f.contribution ?? 0; const pos = c >= 0
        return (
          <div key={f.label} className="flex items-center gap-2 text-xs">
            <span className="w-20 shrink-0" style={{ color: '#94a3b8' }}>{f.label}</span>
            <div className="flex-1 h-2 rounded-full relative" style={{ backgroundColor: 'rgba(255,255,255,0.05)' }}>
              <div className="absolute top-0 h-2 rounded-full" style={{ left: '50%', width: `${Math.min(Math.abs(c) * 200, 50)}%`, transform: pos ? 'none' : 'translateX(-100%)', backgroundColor: f.subscore == null ? '#475569' : pos ? '#00e676' : '#ff1744' }} />
            </div>
          </div>
        )
      })}
      <div className="flex items-center justify-between text-xs mt-1">
        <span style={{ color: '#94a3b8' }}>Regime</span>
        <span style={{ color: '#cbd5e1' }}>{setup.regime.label}{setup.regime.vix != null ? ` · VIX ${setup.regime.vix}` : ''} · ×{setup.regime.multiplier}</span>
      </div>
      {setup.expected_value_r != null && (
        <div className="flex items-center justify-between text-xs">
          <span style={{ color: '#94a3b8' }}>Expected value</span>
          <span style={{ color: setup.expected_value_r >= 0 ? '#00e676' : '#ff1744' }}>{setup.expected_value_r >= 0 ? '+' : ''}{setup.expected_value_r}R</span>
        </div>
      )}
      {setup.hit_rate != null && (
        <span className="text-xs" style={{ color: '#475569' }}>
          Track record: {setup.hit_rate}% up · {(setup.avg_forward_return ?? 0) >= 0 ? '+' : ''}{setup.avg_forward_return}%/{setup.horizon_days}d (n={setup.n}{setup.low_sample ? ', small' : ''})
        </span>
      )}
    </div>
  )
}

// ── Position sizing calculator (rail section) ────────────────────────────────
function SizeStat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="flex flex-col px-3 py-2 rounded-lg" style={{ backgroundColor: '#0a0e1a' }}>
      <span className="text-xs uppercase tracking-wide" style={{ color: '#475569' }}>{label}</span>
      <span className="text-sm font-bold tabular-nums" style={{ color: '#e2e8f0' }}>{value}</span>
      {sub ? <span className="text-xs" style={{ color: '#475569' }}>{sub}</span> : null}
    </div>
  )
}

export function PositionSizing({ score, entry, stop, currentPrice }: { score: number; entry: number | null; stop: number | null; currentPrice: number | null }) {
  const [equity, setEquity] = useState<number>(() => num(localStorage.getItem('decision.accountSize') ?? '', 100000))
  const [maxRisk, setMaxRisk] = useState<number>(() => num(localStorage.getItem('decision.maxRiskPct') ?? '', 1))
  const saveEquity = (v: number) => { setEquity(v); localStorage.setItem('decision.accountSize', String(v)) }
  const saveRisk = (v: number) => { setMaxRisk(v); localStorage.setItem('decision.maxRiskPct', String(v)) }
  const eff = entry ?? currentPrice
  const sizing = computeSizing({ equity, maxRiskPct: maxRisk, conviction: score, entry: eff, stop })
  const usd = (n: number) => `$${Math.round(n).toLocaleString()}`
  return (
    <div className="flex flex-col gap-2">
      <span className="text-xs uppercase tracking-wide" style={{ color: '#475569' }}>Position sizing</span>
      <div className="flex items-center gap-3 flex-wrap">
        <label className="text-xs flex items-center gap-1" style={{ color: '#475569' }}>Account $
          <input type="text" defaultValue={String(equity)} onBlur={e => saveEquity(num(e.target.value, equity))} className="w-24 px-2 py-1 rounded text-xs tabular-nums" style={{ backgroundColor: '#0a0e1a', color: '#e2e8f0', border: '1px solid rgba(255,255,255,0.08)' }} />
        </label>
        <label className="text-xs flex items-center gap-1" style={{ color: '#475569' }}>Risk %
          <input type="text" defaultValue={String(maxRisk)} onBlur={e => saveRisk(num(e.target.value, maxRisk))} className="w-14 px-2 py-1 rounded text-xs tabular-nums" style={{ backgroundColor: '#0a0e1a', color: '#e2e8f0', border: '1px solid rgba(255,255,255,0.08)' }} />
        </label>
      </div>
      {sizing.ok ? (
        <div className="grid grid-cols-2 gap-2">
          <SizeStat label="Shares" value={sizing.shares.toLocaleString()} />
          <SizeStat label="Position" value={usd(sizing.positionDollars)} sub={`${sizing.pctOfEquity.toFixed(1)}% acct`} />
          <SizeStat label="At risk" value={usd(sizing.riskDollars)} sub={`${sizing.riskPct.toFixed(2)}%`} />
          <SizeStat label="Timing-scaled" value={`${(score * 10).toFixed(0)}% max`} sub={sizing.capped ? 'capped' : ''} />
        </div>
      ) : (<div className="text-xs" style={{ color: '#ffab00' }}>{sizing.reason}</div>)}
    </div>
  )
}
