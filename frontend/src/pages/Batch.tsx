import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Loader2, ChevronDown, ChevronUp } from 'lucide-react'
import { stockApi } from '../services/api'
import type { BatchAnalysisResponse, FullStockAnalysis } from '../lib/types'
import { fmt, scoreColor } from '../lib/formatters'
import PageWrapper from '../components/layout/PageWrapper'

type SortKey = 'score' | 'ticker' | 'price' | 'pe_ratio' | 'roe' | 'gross_margin' | 'revenue_growth'

function sortResults(results: FullStockAnalysis[], key: SortKey, asc: boolean): FullStockAnalysis[] {
  return [...results].sort((a, b) => {
    let va: number | string = 0
    let vb: number | string = 0
    if (key === 'score') { va = a.score?.total ?? -1; vb = b.score?.total ?? -1 }
    else if (key === 'ticker') { va = a.ticker; vb = b.ticker }
    else if (key === 'price') { va = a.metrics?.current_price ?? 0; vb = b.metrics?.current_price ?? 0 }
    else if (key === 'pe_ratio') { va = a.metrics?.pe_ratio ?? 9999; vb = b.metrics?.pe_ratio ?? 9999 }
    else if (key === 'roe') { va = a.metrics?.roe ?? -1; vb = b.metrics?.roe ?? -1 }
    else if (key === 'gross_margin') { va = a.metrics?.gross_margin ?? -1; vb = b.metrics?.gross_margin ?? -1 }
    else if (key === 'revenue_growth') { va = a.metrics?.revenue_growth ?? -1; vb = b.metrics?.revenue_growth ?? -1 }
    if (va < vb) return asc ? -1 : 1
    if (va > vb) return asc ? 1 : -1
    return 0
  })
}

interface ThProps {
  label: string
  sortKey: SortKey
  current: SortKey
  asc: boolean
  onSort: (k: SortKey) => void
}

function Th({ label, sortKey, current, asc, onSort }: ThProps) {
  const active = current === sortKey
  return (
    <th
      className="px-4 py-3 text-left cursor-pointer select-none hover:bg-white/5 transition-colors"
      style={{ color: active ? '#00d4ff' : '#94a3b8' }}
      onClick={() => onSort(sortKey)}
    >
      <div className="flex items-center gap-1 text-xs font-semibold uppercase tracking-wider">
        {label}
        {active ? (asc ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />) : null}
      </div>
    </th>
  )
}

export default function Batch() {
  const [input, setInput] = useState('')
  const [sortKey, setSortKey] = useState<SortKey>('score')
  const [sortAsc, setSortAsc] = useState(false)

  const { mutate, data, isPending, isError, error } = useMutation<BatchAnalysisResponse, Error, string[]>({
    mutationFn: (tickers) => stockApi.batch(tickers),
  })

  const handleAnalyze = () => {
    const tickers = input
      .split(/[,\s\n]+/)
      .map(t => t.trim().toUpperCase())
      .filter(Boolean)
      .slice(0, 10)
    if (tickers.length > 0) mutate(tickers)
  }

  const handleSort = (key: SortKey) => {
    if (key === sortKey) setSortAsc(a => !a)
    else { setSortKey(key); setSortAsc(false) }
  }

  const sorted = data ? sortResults(data.results, sortKey, sortAsc) : []

  return (
    <PageWrapper>
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-xl font-bold mb-1" style={{ color: '#e2e8f0' }}>Batch Comparison</h1>
          <p className="text-sm" style={{ color: '#94a3b8' }}>Compare up to 10 stocks side-by-side, ranked by VF Score</p>
        </div>

        <div
          className="rounded-xl border p-5 flex flex-col gap-4"
          style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
        >
          <div>
            <label htmlFor="batch-input" className="block text-xs font-medium mb-1.5" style={{ color: '#94a3b8' }}>
              Tickers (comma-separated, max 10)
            </label>
            <textarea
              id="batch-input"
              value={input}
              onChange={e => setInput(e.target.value)}
              rows={3}
              placeholder="AAPL, MSFT, GOOGL, NVDA, AMZN"
              className="w-full px-3 py-2.5 rounded-lg text-sm font-mono outline-none resize-none"
              style={{
                backgroundColor: '#1a2235',
                border: '1px solid rgba(255,255,255,0.08)',
                color: '#e2e8f0',
              }}
              data-testid="batch-input"
            />
          </div>
          <button
            onClick={handleAnalyze}
            disabled={isPending || !input.trim()}
            className="self-start px-5 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ background: 'linear-gradient(135deg, #00d4ff, #0088cc)', color: '#0a0e1a' }}
            data-testid="batch-analyze-btn"
          >
            {isPending && <Loader2 className="w-4 h-4 animate-spin" />}
            {isPending ? 'Analyzing...' : 'Analyze All'}
          </button>
        </div>

        {isError && (
          <div
            className="rounded-xl border p-4"
            style={{ backgroundColor: 'rgba(255,23,68,0.05)', borderColor: 'rgba(255,23,68,0.2)' }}
            role="alert"
          >
            <p className="text-sm" style={{ color: '#ff1744' }}>{(error as Error)?.message ?? 'Batch analysis failed'}</p>
          </div>
        )}

        {data && (
          <div className="flex flex-col gap-3">
            {data.failed.length > 0 && (
              <p className="text-xs" style={{ color: '#ffab00' }}>
                Failed: {data.failed.join(', ')}
              </p>
            )}
            <div
              className="rounded-xl border overflow-hidden"
              style={{ borderColor: 'rgba(255,255,255,0.06)' }}
              data-testid="batch-results"
            >
              <table className="w-full text-sm">
                <thead>
                  <tr style={{ backgroundColor: '#1a2235' }}>
                    <Th label="Ticker" sortKey="ticker" current={sortKey} asc={sortAsc} onSort={handleSort} />
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: '#94a3b8' }}>Company</th>
                    <Th label="Score" sortKey="score" current={sortKey} asc={sortAsc} onSort={handleSort} />
                    <Th label="Price" sortKey="price" current={sortKey} asc={sortAsc} onSort={handleSort} />
                    <Th label="P/E" sortKey="pe_ratio" current={sortKey} asc={sortAsc} onSort={handleSort} />
                    <Th label="ROE" sortKey="roe" current={sortKey} asc={sortAsc} onSort={handleSort} />
                    <Th label="Gross Margin" sortKey="gross_margin" current={sortKey} asc={sortAsc} onSort={handleSort} />
                    <Th label="Rev Growth" sortKey="revenue_growth" current={sortKey} asc={sortAsc} onSort={handleSort} />
                  </tr>
                </thead>
                <tbody>
                  {sorted.map(stock => {
                    const score = stock.score?.total ?? 0
                    const m = stock.metrics
                    return (
                      <tr
                        key={stock.ticker}
                        className="border-t hover:bg-white/[0.02] transition-colors"
                        style={{ borderColor: 'rgba(255,255,255,0.04)' }}
                        data-testid={`batch-row-${stock.ticker}`}
                      >
                        <td className="px-4 py-3">
                          <span
                            className="font-bold font-mono text-xs px-2 py-0.5 rounded"
                            style={{ color: '#00d4ff', backgroundColor: '#00d4ff20' }}
                          >
                            {stock.ticker}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-xs" style={{ color: '#94a3b8' }}>
                          {stock.company_name ?? '—'}
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-sm font-bold tabular-nums" style={{ color: scoreColor(score) }}>
                            {Math.round(score)}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-xs tabular-nums" style={{ color: '#e2e8f0' }}>{fmt.price(m?.current_price)}</td>
                        <td className="px-4 py-3 text-xs tabular-nums" style={{ color: '#e2e8f0' }}>{fmt.ratio(m?.pe_ratio)}</td>
                        <td className="px-4 py-3 text-xs tabular-nums" style={{ color: '#e2e8f0' }}>
                          {m?.roe != null ? fmt.pct(m.roe) : '—'}
                        </td>
                        <td className="px-4 py-3 text-xs tabular-nums" style={{ color: '#e2e8f0' }}>
                          {m?.gross_margin != null ? fmt.pct(m.gross_margin) : '—'}
                        </td>
                        <td className="px-4 py-3 text-xs tabular-nums" style={{ color: '#e2e8f0' }}>
                          {m?.revenue_growth != null ? fmt.pct(m.revenue_growth) : '—'}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </PageWrapper>
  )
}
