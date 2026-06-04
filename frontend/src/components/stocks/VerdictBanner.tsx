import { useQuery } from '@tanstack/react-query'
import { verdictApi } from '../../services/api'
import type { VerdictResponse } from '../../lib/types'
import { fmt } from '../../lib/formatters'

function verdictColor(verdict: string): string {
  if (verdict.includes('BUY'))  return '#00e676'
  if (verdict.includes('SELL')) return '#ff1744'
  return '#ffab00'
}

function signalKey(key: string): string {
  return key === 'ai_outlook' ? 'AI Outlook' : key.charAt(0).toUpperCase() + key.slice(1)
}

function SignalPill({ name, detail }: { name: string; detail: VerdictResponse['signals']['technical'] }) {
  const bullish = detail.score > 60
  const neutral  = detail.score >= 40 && detail.score <= 60
  const color = bullish ? '#00e676' : neutral ? '#ffab00' : '#ff1744'
  return (
    <div
      className="flex items-center gap-2 rounded-lg px-3 py-1.5"
      style={{
        background: `${color}0d`,
        border: `1px solid ${color}30`,
      }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full shrink-0"
        style={{ backgroundColor: color }}
      />
      <span className="text-xs font-semibold" style={{ color: '#e2e8f0' }}>
        {signalKey(name)}
      </span>
      <span className="text-xs font-bold" style={{ color }}>
        {detail.label}
      </span>
      <span className="text-xs tabular-nums" style={{ color: '#475569' }}>
        {detail.score}
      </span>
    </div>
  )
}

function VerdictSkeleton() {
  return (
    <div
      className="rounded-xl border p-5 animate-pulse"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
    >
      <div className="h-8 w-48 rounded" style={{ backgroundColor: 'rgba(255,255,255,0.06)' }} />
      <div className="mt-3 flex gap-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-7 w-24 rounded-lg" style={{ backgroundColor: 'rgba(255,255,255,0.04)' }} />
        ))}
      </div>
    </div>
  )
}

export default function VerdictBanner({ ticker, period }: { ticker: string; period?: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ['verdict', ticker, period ?? '1y'],
    queryFn: () => verdictApi.get(ticker, period ?? '1y'),
    staleTime: 5 * 60 * 1000,
  })

  if (isLoading) return <VerdictSkeleton />
  if (!data) return null

  const vc = verdictColor(data.verdict)

  return (
    <div
      className="rounded-xl border p-5 flex flex-col gap-4"
      style={{
        backgroundColor: '#111827',
        borderColor: `${vc}35`,
        background: `linear-gradient(135deg, ${vc}0a, #111827 60%)`,
      }}
    >
      {/* Top row: verdict + key numbers */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-5">
          <div>
            <div
              className="text-3xl font-black tracking-wide leading-none"
              style={{ color: vc }}
            >
              {data.verdict}
            </div>
            <div className="text-xs mt-1" style={{ color: '#64748b' }}>
              {data.confidence}% confidence · {Object.values(data.signals).filter(s => s.score > 60).length} of 6 signals bullish
            </div>
          </div>

          <div className="w-px h-10 shrink-0" style={{ backgroundColor: 'rgba(255,255,255,0.08)' }} />

          <div className="flex gap-5">
            <div>
              <div className="text-2xl font-black tabular-nums leading-none" style={{ color: '#e2e8f0' }}>
                {data.vf_score}
                <span className="text-sm font-normal" style={{ color: '#475569' }}>/100</span>
              </div>
              <div className="text-xs mt-0.5 uppercase tracking-wide" style={{ color: '#64748b' }}>VF Score</div>
            </div>
            {data.price_target != null && (
              <div>
                <div className="text-2xl font-black tabular-nums leading-none" style={{ color: '#00d4ff' }}>
                  {fmt.price(data.price_target)}
                </div>
                <div className="text-xs mt-0.5 uppercase tracking-wide" style={{ color: '#64748b' }}>Price Target</div>
              </div>
            )}
            {data.stop_loss != null && (
              <div>
                <div className="text-2xl font-black tabular-nums leading-none" style={{ color: '#ff1744' }}>
                  {fmt.price(data.stop_loss)}
                </div>
                <div className="text-xs mt-0.5 uppercase tracking-wide" style={{ color: '#64748b' }}>Stop Loss</div>
              </div>
            )}
          </div>
        </div>

        <p className="text-xs italic max-w-xs leading-relaxed" style={{ color: '#94a3b8' }}>
          "{data.why}"
        </p>
      </div>

      {/* Signal pills */}
      <div className="flex flex-wrap gap-2">
        {(Object.entries(data.signals) as [keyof VerdictResponse['signals'], VerdictResponse['signals']['technical']][]).map(
          ([key, detail]) => <SignalPill key={key} name={key} detail={detail} />
        )}
      </div>
    </div>
  )
}
