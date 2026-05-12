import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { aiApi } from '../../services/api'
import type { FullStockAnalysis } from '../../lib/types'
import ReactMarkdown from 'react-markdown'

interface Props { data: FullStockAnalysis }

function PluginCard({
  title, subtitle, buttonLabel, buttonColor, queryKey, queryFn, loadingText,
}: {
  title: string; subtitle: string; buttonLabel: string
  buttonColor: { bg: string; text: string; border: string }
  queryKey: string[]; queryFn: () => Promise<{ content?: string; error?: string }>
  loadingText: string
}) {
  const [enabled, setEnabled] = useState(false)
  const { data: result, isLoading } = useQuery({
    queryKey,
    queryFn,
    enabled,
    staleTime: 60 * 60_000,
  })

  return (
    <div className="rounded-xl border p-5" style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold" style={{ color: '#e2e8f0' }}>{title}</h3>
          <p className="text-xs mt-0.5" style={{ color: '#475569' }}>{subtitle}</p>
        </div>
        {!enabled && (
          <button
            onClick={() => setEnabled(true)}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
            style={{ backgroundColor: buttonColor.bg, color: buttonColor.text, border: `1px solid ${buttonColor.border}` }}
          >
            {buttonLabel}
          </button>
        )}
      </div>

      {isLoading && (
        <div className="flex items-center gap-2 py-4" style={{ color: '#475569' }}>
          <div className="w-3 h-3 rounded-full border-2 border-current border-t-transparent animate-spin" />
          <span className="text-xs">{loadingText}</span>
        </div>
      )}

      {result?.error && <p className="text-xs" style={{ color: '#ef4444' }}>{result.error}</p>}

      {result?.content && (
        <div className="prose prose-invert prose-sm max-w-none text-xs leading-relaxed" style={{ color: '#94a3b8' }}>
          <ReactMarkdown>{result.content}</ReactMarkdown>
        </div>
      )}
    </div>
  )
}

export default function ValuationTools({ data }: Props) {
  const m = (data.metrics ?? {}) as object
  const ticker = data.ticker
  const name = data.company_name ?? ''
  const sector = data.sector ?? ''
  const industry = data.industry ?? ''

  return (
    <div className="flex flex-col gap-5">
      <PluginCard
        title="DCF Valuation"
        subtitle="Intrinsic value · WACC · sensitivity table"
        buttonLabel="Run DCF"
        buttonColor={{ bg: 'rgba(16,185,129,0.1)', text: '#34d399', border: 'rgba(16,185,129,0.25)' }}
        queryKey={['dcf', ticker]}
        queryFn={() => aiApi.dcf(ticker, name, sector, m)}
        loadingText="Building DCF model…"
      />
      <PluginCard
        title="Comparable Company Analysis"
        subtitle="Peer multiples · EV/EBITDA · premium/discount"
        buttonLabel="Run Comps"
        buttonColor={{ bg: 'rgba(245,158,11,0.1)', text: '#fbbf24', border: 'rgba(245,158,11,0.25)' }}
        queryKey={['comps', ticker]}
        queryFn={() => aiApi.comps(ticker, name, sector, industry, m)}
        loadingText="Benchmarking peer multiples…"
      />
    </div>
  )
}
