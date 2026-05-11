import { useState } from 'react'
import { Sparkles, Loader2, TrendingUp, TrendingDown, AlertTriangle, Target } from 'lucide-react'
import { aiApi } from '../../services/api'
import type { AiAnalystReportResponse, FullStockAnalysis } from '../../lib/types'

interface Props {
  ticker: string
  data: FullStockAnalysis
}

export default function AiAnalystReport({ ticker, data }: Props) {
  const [report, setReport] = useState<AiAnalystReportResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function generate() {
    if (loading) return
    setLoading(true)
    setError(null)
    try {
      const result = await aiApi.analystReport(
        ticker,
        data.company_name ?? ticker,
        data.sector ?? '',
        data.metrics ?? {},
        data.score ?? {},
      )
      if (result.error) {
        setError(result.error)
      } else {
        setReport(result)
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  const s = report?.sections

  return (
    <div
      className="rounded-xl border overflow-hidden"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(0,212,255,0.15)' }}
    >
      <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="flex items-center gap-2">
          <Sparkles size={15} style={{ color: '#00d4ff' }} />
          <span className="text-sm font-semibold" style={{ color: '#e2e8f0' }}>AI Analyst Report</span>
          {report?.provider && (
            <span className="text-xs px-1.5 py-0.5 rounded" style={{ backgroundColor: '#00d4ff10', color: '#00d4ff60' }}>
              {report.provider}
            </span>
          )}
        </div>
        {!report && (
          <button
            onClick={generate}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold"
            style={{
              background: loading ? 'rgba(0,212,255,0.1)' : 'linear-gradient(135deg, #00d4ff, #0088cc)',
              color: loading ? '#475569' : '#0a0e1a',
              cursor: loading ? 'not-allowed' : 'pointer',
              border: 'none',
            }}
          >
            {loading
              ? <><Loader2 size={12} className="animate-spin" /> Generating…</>
              : <><Sparkles size={12} /> Generate Report</>
            }
          </button>
        )}
        {report && (
          <button
            onClick={() => { setReport(null); setError(null) }}
            className="text-xs"
            style={{ color: '#475569', background: 'none', border: 'none', cursor: 'pointer' }}
          >
            Regenerate
          </button>
        )}
      </div>

      {error && (
        <div className="px-5 py-4">
          <p className="text-xs" style={{ color: '#ff1744' }}>{error}</p>
        </div>
      )}

      {loading && !report && (
        <div className="flex items-center gap-2 px-5 py-8" style={{ color: '#475569' }}>
          <Loader2 size={16} className="animate-spin" style={{ color: '#00d4ff' }} />
          <span className="text-sm">Analyzing {ticker} with AI…</span>
        </div>
      )}

      {!report && !loading && !error && (
        <div className="px-5 py-6 text-center">
          <p className="text-sm" style={{ color: '#475569' }}>
            Generate an institutional-grade research report powered by{' '}
            <span style={{ color: '#00d4ff' }}>Groq Llama 3.3 70B</span>
          </p>
        </div>
      )}

      {s && (
        <div className="px-5 py-4 flex flex-col gap-4">
          {s.executive_summary && (
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide mb-2" style={{ color: '#00d4ff' }}>Executive Summary</p>
              <p className="text-sm leading-relaxed" style={{ color: '#e2e8f0' }}>{s.executive_summary}</p>
            </div>
          )}

          {(s.bulls_say.length > 0 || s.bears_say.length > 0) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {s.bulls_say.length > 0 && (
                <div
                  className="rounded-lg p-3"
                  style={{ backgroundColor: 'rgba(0,230,118,0.05)', border: '1px solid rgba(0,230,118,0.15)' }}
                >
                  <div className="flex items-center gap-1.5 mb-2">
                    <TrendingUp size={13} style={{ color: '#00e676' }} />
                    <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: '#00e676' }}>Bulls Say</span>
                  </div>
                  <ul className="flex flex-col gap-1.5">
                    {s.bulls_say.map((b, i) => (
                      <li key={i} className="text-xs leading-relaxed flex gap-1.5" style={{ color: '#94a3b8' }}>
                        <span style={{ color: '#00e676', flexShrink: 0 }}>+</span>{b}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {s.bears_say.length > 0 && (
                <div
                  className="rounded-lg p-3"
                  style={{ backgroundColor: 'rgba(255,23,68,0.05)', border: '1px solid rgba(255,23,68,0.15)' }}
                >
                  <div className="flex items-center gap-1.5 mb-2">
                    <TrendingDown size={13} style={{ color: '#ff1744' }} />
                    <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: '#ff1744' }}>Bears Say</span>
                  </div>
                  <ul className="flex flex-col gap-1.5">
                    {s.bears_say.map((b, i) => (
                      <li key={i} className="text-xs leading-relaxed flex gap-1.5" style={{ color: '#94a3b8' }}>
                        <span style={{ color: '#ff1744', flexShrink: 0 }}>−</span>{b}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {s.key_risks && (
            <div
              className="rounded-lg p-3"
              style={{ backgroundColor: 'rgba(245,158,11,0.06)', border: '1px solid rgba(245,158,11,0.2)' }}
            >
              <div className="flex items-center gap-1.5 mb-2">
                <AlertTriangle size={13} style={{ color: '#f59e0b' }} />
                <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: '#f59e0b' }}>Key Risks</span>
              </div>
              <p className="text-xs leading-relaxed" style={{ color: '#94a3b8' }}>{s.key_risks}</p>
            </div>
          )}

          {s.investment_thesis && (
            <div
              className="rounded-lg p-3"
              style={{ backgroundColor: 'rgba(0,212,255,0.05)', border: '1px solid rgba(0,212,255,0.15)' }}
            >
              <div className="flex items-center gap-1.5 mb-2">
                <Target size={13} style={{ color: '#00d4ff' }} />
                <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: '#00d4ff' }}>Investment Thesis</span>
              </div>
              <p className="text-xs leading-relaxed" style={{ color: '#94a3b8' }}>{s.investment_thesis}</p>
            </div>
          )}
        </div>
      )}
      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
