import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { verdictApi } from '../../services/api'
import type { VerdictResponse } from '../../lib/types'
import { fmt } from '../../lib/formatters'

type Horizon = 'scalp' | 'swing' | 'position' | 'longterm'

const HORIZONS: { id: Horizon; label: string; sub: string }[] = [
  { id: 'scalp',    label: 'Scalp',     sub: '<1d'   },
  { id: 'swing',    label: 'Swing',     sub: '1–14d' },
  { id: 'position', label: 'Position',  sub: '1–3mo' },
  { id: 'longterm', label: 'Long-term', sub: '3mo+'  },
]

function verdictColor(verdict: string): string {
  if (verdict.includes('BUY'))  return '#00e676'
  if (verdict.includes('SELL')) return '#ff1744'
  return '#ffab00'
}

function entryTimingColor(timing: string): string {
  if (timing.startsWith('ENTER NOW'))  return '#00e676'
  if (timing.startsWith('ENTER'))      return '#69f0ae'
  if (timing.startsWith('SCALE'))      return '#ffab00'
  if (timing.startsWith('WAIT'))       return '#ff9800'
  if (timing.startsWith('DO NOT'))     return '#ff1744'
  return '#64748b'
}

function signalKey(key: string): string {
  const MAP: Record<string, string> = {
    ai_outlook: 'AI Outlook',
    news_sentiment: 'News',
    earnings_quality: 'Earnings',
  }
  return MAP[key] ?? key.charAt(0).toUpperCase() + key.slice(1)
}

function SignalPill({ name, detail }: { name: string; detail: VerdictResponse['signals']['technical'] }) {
  const bullish = detail.score > 60
  const neutral  = detail.score >= 40 && detail.score <= 60
  const color = bullish ? '#00e676' : neutral ? '#ffab00' : '#ff1744'
  return (
    <div
      className="flex items-center gap-2 rounded-lg px-3 py-1.5"
      style={{ background: `${color}0d`, border: `1px solid ${color}30` }}
    >
      <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: color }} />
      <span className="text-xs font-semibold" style={{ color: '#e2e8f0' }}>{signalKey(name)}</span>
      <span className="text-xs font-bold" style={{ color }}>{detail.label}</span>
      <span className="text-xs tabular-nums" style={{ color: '#475569' }}>
        {detail.score} <span style={{ color: '#334155' }}>({(detail.weight * 100).toFixed(0)}%)</span>
      </span>
    </div>
  )
}

function HorizonSelector({ horizon, onChange }: { horizon: Horizon; onChange: (h: Horizon) => void }) {
  return (
    <div className="flex gap-1 rounded-lg p-1" style={{ backgroundColor: '#0a0e1a' }}>
      {HORIZONS.map(h => (
        <button
          key={h.id}
          onClick={() => onChange(h.id)}
          className="flex flex-col items-center px-3 py-1.5 rounded-md transition-all"
          style={{
            backgroundColor: horizon === h.id ? '#1e293b' : 'transparent',
            border: `1px solid ${horizon === h.id ? 'rgba(255,255,255,0.12)' : 'transparent'}`,
          }}
        >
          <span className="text-xs font-bold" style={{ color: horizon === h.id ? '#e2e8f0' : '#475569' }}>
            {h.label}
          </span>
          <span className="text-xs" style={{ color: '#334155' }}>{h.sub}</span>
        </button>
      ))}
    </div>
  )
}

function PriceTargetRange({
  bear, base, bull, price,
}: {
  bear?: number; base?: number; bull?: number; price?: number
}) {
  if (!base) return null
  return (
    <div className="flex flex-col gap-1.5">
      <div className="text-xs uppercase tracking-wide mb-0.5" style={{ color: '#475569' }}>Price Target Range</div>
      <div className="flex items-end gap-4">
        {bear != null && (
          <div className="flex flex-col items-center">
            <span className="text-xs font-bold tabular-nums" style={{ color: '#ff1744' }}>{fmt.price(bear)}</span>
            <span className="text-xs mt-0.5" style={{ color: '#334155' }}>Bear</span>
          </div>
        )}
        <div className="flex flex-col items-center">
          <span className="text-lg font-black tabular-nums" style={{ color: '#00d4ff' }}>{fmt.price(base)}</span>
          <span className="text-xs mt-0.5" style={{ color: '#64748b' }}>Base</span>
        </div>
        {bull != null && (
          <div className="flex flex-col items-center">
            <span className="text-xs font-bold tabular-nums" style={{ color: '#00e676' }}>{fmt.price(bull)}</span>
            <span className="text-xs mt-0.5" style={{ color: '#334155' }}>Bull</span>
          </div>
        )}
      </div>
      {price != null && base != null && (
        <div className="text-xs tabular-nums" style={{ color: '#64748b' }}>
          Base <span style={{ color: base >= price ? '#00e676' : '#ff1744' }}>
            {base >= price ? '+' : ''}{(((base - price) / price) * 100).toFixed(1)}%
          </span>
          {bull != null && (
            <> · Bull <span style={{ color: '#00d4ff' }}>+{(((bull - price) / price) * 100).toFixed(1)}%</span></>
          )}
        </div>
      )}
    </div>
  )
}

function PositionSizing({ suggested, max }: { suggested?: number; max?: number }) {
  if (!suggested) return null
  return (
    <div className="flex flex-col gap-1">
      <div className="text-xs uppercase tracking-wide" style={{ color: '#475569' }}>Suggested Allocation</div>
      <div className="flex items-baseline gap-2">
        <span className="text-lg font-black tabular-nums" style={{ color: '#e2e8f0' }}>{suggested}%</span>
        <span className="text-xs" style={{ color: '#475569' }}>of portfolio</span>
        {max && <span className="text-xs" style={{ color: '#334155' }}>· max {max}%</span>}
      </div>
    </div>
  )
}

function VerdictSkeleton() {
  return (
    <div className="rounded-xl border p-5 animate-pulse"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
      <div className="h-8 w-48 rounded" style={{ backgroundColor: 'rgba(255,255,255,0.06)' }} />
      <div className="mt-3 flex gap-3">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="h-7 w-24 rounded-lg" style={{ backgroundColor: 'rgba(255,255,255,0.04)' }} />
        ))}
      </div>
    </div>
  )
}

export default function VerdictBanner({ ticker, period }: { ticker: string; period?: string }) {
  const [horizon, setHorizon] = useState<Horizon>('swing')

  const { data, isLoading } = useQuery({
    queryKey: ['verdict', ticker, period ?? '1y', horizon],
    queryFn: () => verdictApi.get(ticker, period ?? '1y', horizon),
    staleTime: 5 * 60 * 1000,
  })

  if (isLoading) return <VerdictSkeleton />
  if (!data) return null

  const vc = verdictColor(data.verdict)
  const ec = entryTimingColor(data.entry_timing)

  return (
    <div
      className="rounded-xl border p-5 flex flex-col gap-4"
      style={{
        backgroundColor: '#111827',
        borderColor: `${vc}35`,
        background: `linear-gradient(135deg, ${vc}0a, #111827 60%)`,
      }}
    >
      {/* Row 1: verdict + horizon selector */}
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div className="flex items-center gap-5">
          <div>
            <div className="text-3xl font-black tracking-wide leading-none" style={{ color: vc }}>
              {data.verdict}
            </div>
            <div className="text-xs mt-1" style={{ color: '#64748b' }}>
              {data.confidence}% confidence · {Object.values(data.signals).filter(s => s.score > 60).length} of 8 signals bullish
            </div>
          </div>
          <div className="w-px h-10 shrink-0" style={{ backgroundColor: 'rgba(255,255,255,0.08)' }} />
          <div>
            <div className="text-2xl font-black tabular-nums leading-none" style={{ color: '#e2e8f0' }}>
              {data.vf_score}
              <span className="text-sm font-normal" style={{ color: '#475569' }}>/100</span>
            </div>
            <div className="text-xs mt-0.5 uppercase tracking-wide" style={{ color: '#64748b' }}>VF Score</div>
          </div>
        </div>
        <HorizonSelector horizon={horizon} onChange={setHorizon} />
      </div>

      {/* Row 2: entry timing + catalyst */}
      <div className="flex items-center gap-3 flex-wrap">
        <div
          className="flex items-center gap-2 rounded-lg px-4 py-2 border"
          style={{ backgroundColor: `${ec}12`, borderColor: `${ec}40` }}
        >
          <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: ec }} />
          <span className="text-sm font-bold" style={{ color: ec }}>{data.entry_timing}</span>
          {data.entry_price_zone && (
            <span className="text-xs tabular-nums" style={{ color: '#64748b' }}>
              · zone {fmt.price(data.entry_price_zone[0])}–{fmt.price(data.entry_price_zone[1])}
            </span>
          )}
        </div>

        {data.catalyst_event && (
          <div
            className="flex items-center gap-2 rounded-lg px-3 py-1.5 border"
            style={{
              backgroundColor: (data.catalyst_days ?? 99) <= 7 ? '#ff174415' : '#ffab0010',
              borderColor: (data.catalyst_days ?? 99) <= 7 ? '#ff174440' : '#ffab0025',
            }}
          >
            <span className="text-xs font-semibold" style={{ color: (data.catalyst_days ?? 99) <= 7 ? '#ff1744' : '#ffab00' }}>
              CATALYST: {data.catalyst_event}
            </span>
          </div>
        )}
      </div>

      {/* Row 3: price target range + stop loss + position sizing */}
      <div className="flex gap-8 flex-wrap items-start">
        <PriceTargetRange
          bear={data.price_target_bear}
          base={data.price_target ?? undefined}
          bull={data.price_target_bull}
        />
        {data.stop_loss != null && (
          <div className="flex flex-col gap-1">
            <div className="text-xs uppercase tracking-wide" style={{ color: '#475569' }}>Stop Loss</div>
            <span className="text-lg font-black tabular-nums" style={{ color: '#ff1744' }}>
              {fmt.price(data.stop_loss)}
            </span>
          </div>
        )}
        <PositionSizing suggested={data.position_size_pct ?? undefined} max={data.position_max_pct ?? undefined} />
      </div>

      {/* Row 4: conflict note */}
      {data.conflict_note && (
        <div
          className="rounded-lg px-3 py-2 text-xs leading-relaxed flex items-start gap-2"
          style={{ backgroundColor: '#ffab0008', borderLeft: '2px solid #ffab00' }}
        >
          <span className="shrink-0 font-semibold" style={{ color: '#ffab00' }}>CONFLICT:</span>
          <span style={{ color: '#94a3b8' }}>{data.conflict_note}</span>
        </div>
      )}

      {/* Row 5: why text */}
      <div
        className="rounded-lg px-3 py-2 text-xs leading-relaxed"
        style={{ backgroundColor: '#0a0e1a', color: '#94a3b8', borderLeft: `2px solid ${vc}` }}
      >
        {data.why}
      </div>

      {/* Row 6: signal pills with weight */}
      <div className="flex flex-wrap gap-2">
        {(Object.entries(data.signals) as [keyof VerdictResponse['signals'], VerdictResponse['signals']['technical']][]).map(
          ([key, detail]) => <SignalPill key={key} name={key} detail={detail} />
        )}
      </div>
    </div>
  )
}
