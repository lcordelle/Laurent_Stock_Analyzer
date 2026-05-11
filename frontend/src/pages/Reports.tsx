import { useState, type FormEvent } from 'react'
import { FileDown, Loader2 } from 'lucide-react'
import PageWrapper from '../components/layout/PageWrapper'

const PERIODS = [
  { value: '1mo', label: '1 Month' },
  { value: '3mo', label: '3 Months' },
  { value: '6mo', label: '6 Months' },
  { value: '1y', label: '1 Year' },
  { value: '2y', label: '2 Years' },
]

export default function Reports() {
  const [ticker, setTicker] = useState('')
  const [period, setPeriod] = useState('1y')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [downloadUrl, setDownloadUrl] = useState('')

  const handleGenerate = async (e: FormEvent) => {
    e.preventDefault()
    const t = ticker.trim().toUpperCase()
    if (!t) return
    setError('')
    setDownloadUrl('')
    setLoading(true)
    try {
      const token = localStorage.getItem('token')
      const res = await fetch(`/api/report/${t}?period=${period}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (!res.ok) throw new Error(`Server returned ${res.status}`)
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      setDownloadUrl(url)
    } catch (err) {
      setError((err as Error).message ?? 'Failed to generate report')
    } finally {
      setLoading(false)
    }
  }

  return (
    <PageWrapper>
      <div className="flex flex-col gap-6 max-w-lg">
        <div>
          <h1 className="text-xl font-bold mb-1" style={{ color: '#e2e8f0' }}>PDF Reports</h1>
          <p className="text-sm" style={{ color: '#94a3b8' }}>Generate a detailed analysis report for any stock</p>
        </div>

        <div
          className="rounded-xl border p-6 flex flex-col gap-5"
          style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
        >
          <form onSubmit={handleGenerate} className="flex flex-col gap-4" data-testid="report-form">
            <div>
              <label htmlFor="report-ticker" className="block text-xs font-medium mb-1.5" style={{ color: '#94a3b8' }}>
                Ticker Symbol
              </label>
              <input
                id="report-ticker"
                type="text"
                value={ticker}
                onChange={e => setTicker(e.target.value.toUpperCase())}
                placeholder="e.g. AAPL"
                className="w-full px-3 py-2.5 rounded-lg text-sm font-mono outline-none"
                style={{
                  backgroundColor: '#1a2235',
                  border: '1px solid rgba(255,255,255,0.08)',
                  color: '#e2e8f0',
                }}
                data-testid="report-ticker-input"
              />
            </div>

            <div>
              <label htmlFor="report-period" className="block text-xs font-medium mb-1.5" style={{ color: '#94a3b8' }}>
                Period
              </label>
              <select
                id="report-period"
                value={period}
                onChange={e => setPeriod(e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg text-sm outline-none"
                style={{
                  backgroundColor: '#1a2235',
                  border: '1px solid rgba(255,255,255,0.08)',
                  color: '#e2e8f0',
                }}
                data-testid="report-period-select"
              >
                {PERIODS.map(p => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </div>

            <button
              type="submit"
              disabled={loading || !ticker.trim()}
              className="flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ background: 'linear-gradient(135deg, #00d4ff, #0088cc)', color: '#0a0e1a' }}
              data-testid="generate-report-btn"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileDown className="w-4 h-4" />}
              {loading ? 'Generating...' : 'Generate PDF Report'}
            </button>
          </form>

          {error && (
            <div
              className="rounded-lg p-3"
              style={{ backgroundColor: 'rgba(255,23,68,0.08)', border: '1px solid rgba(255,23,68,0.2)' }}
              role="alert"
            >
              <p className="text-xs" style={{ color: '#ff1744' }}>{error}</p>
            </div>
          )}

          {downloadUrl && (
            <div
              className="rounded-lg p-4 flex items-center justify-between"
              style={{ backgroundColor: 'rgba(0,230,118,0.08)', border: '1px solid rgba(0,230,118,0.2)' }}
              data-testid="report-download"
            >
              <div>
                <p className="text-sm font-semibold" style={{ color: '#00e676' }}>Report ready</p>
                <p className="text-xs mt-0.5" style={{ color: '#94a3b8' }}>
                  {ticker} — {PERIODS.find(p => p.value === period)?.label}
                </p>
              </div>
              <a
                href={downloadUrl}
                download={`${ticker}_analysis_${period}.pdf`}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold"
                style={{ backgroundColor: '#00e67620', color: '#00e676' }}
              >
                <FileDown className="w-3.5 h-3.5" />
                Download
              </a>
            </div>
          )}
        </div>
      </div>
    </PageWrapper>
  )
}
