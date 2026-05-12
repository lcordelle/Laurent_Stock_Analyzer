import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { aiApi } from '../../services/api'
import type { FullStockAnalysis } from '../../lib/types'
import ReactMarkdown from 'react-markdown'

interface Props { data: FullStockAnalysis }

export default function EarningsPreview({ data }: Props) {
  const [enabled, setEnabled] = useState(false)

  const { data: result, isLoading } = useQuery({
    queryKey: ['earnings-preview', data.ticker],
    queryFn: () => aiApi.earningsPreview(
      data.ticker,
      data.company_name ?? '',
      data.sector ?? '',
      (data.metrics ?? {}) as object,
      data.earnings_dates ?? [],
    ),
    enabled,
    staleTime: 30 * 60_000,
  })

  return (
    <div className="rounded-xl border p-5" style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold" style={{ color: '#e2e8f0' }}>Earnings Preview</h3>
          <p className="text-xs mt-0.5" style={{ color: '#475569' }}>Bull/bear scenarios · key metrics to watch</p>
        </div>
        {!enabled && (
          <button
            onClick={() => setEnabled(true)}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
            style={{ backgroundColor: 'rgba(0,212,255,0.1)', color: '#00d4ff', border: '1px solid rgba(0,212,255,0.25)' }}
          >
            Generate Preview
          </button>
        )}
      </div>

      {isLoading && (
        <div className="flex items-center gap-2 py-4" style={{ color: '#475569' }}>
          <div className="w-3 h-3 rounded-full border-2 border-current border-t-transparent animate-spin" />
          <span className="text-xs">Analysing earnings setup…</span>
        </div>
      )}

      {result?.error && (
        <p className="text-xs" style={{ color: '#ef4444' }}>{result.error}</p>
      )}

      {result?.content && (
        <div className="prose prose-invert prose-sm max-w-none text-xs leading-relaxed"
          style={{ color: '#94a3b8' }}>
          <ReactMarkdown>{result.content}</ReactMarkdown>
        </div>
      )}
    </div>
  )
}
