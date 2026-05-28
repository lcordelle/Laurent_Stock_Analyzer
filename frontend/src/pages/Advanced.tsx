import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, TrendingDown, Building2, Eye, Activity } from 'lucide-react'
import { advancedApi } from '../services/api'
import PageWrapper from '../components/layout/PageWrapper'

const TABS = [
  { id: 'options', label: '🎯 Options Flow', icon: Activity },
  { id: 'insider', label: '👥 Insider', icon: Eye },
  { id: 'short', label: '📉 Short Interest', icon: TrendingDown },
  { id: 'institutional', label: '🏦 Institutional', icon: Building2 },
]

const CARD: React.CSSProperties = {
  backgroundColor: '#111827',
  border: '1px solid rgba(255,255,255,0.06)',
  borderRadius: 12,
  padding: '16px',
}

function Badge({ label, color = '#00d4ff' }: { label: string; color?: string }) {
  return (
    <span
      className="px-2 py-0.5 rounded text-xs font-semibold"
      style={{ backgroundColor: color + '22', color }}
    >
      {label}
    </span>
  )
}

function TickerSearch({ value, onChange, onSearch, placeholder = 'e.g. NVDA' }: {
  value: string; onChange: (v: string) => void
  onSearch: () => void; placeholder?: string
}) {
  return (
    <div className="flex gap-2 mb-6">
      <div className="relative flex-1 max-w-xs">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: '#475569' }} />
        <input
          value={value}
          onChange={e => onChange(e.target.value.toUpperCase())}
          onKeyDown={e => e.key === 'Enter' && onSearch()}
          placeholder={placeholder}
          className="w-full pl-9 pr-4 py-2 rounded-lg text-sm outline-none"
          style={{
            backgroundColor: '#1e2535', border: '1px solid rgba(255,255,255,0.08)',
            color: '#e2e8f0',
          }}
        />
      </div>
      <button
        onClick={onSearch}
        className="px-4 py-2 rounded-lg text-sm font-semibold transition-opacity hover:opacity-80"
        style={{ backgroundColor: '#00d4ff', color: '#0a0e1a' }}
      >
        Fetch
      </button>
    </div>
  )
}

// ── Options Flow Tab ──────────────────────────────────────────────────────────
function OptionsTab() {
  const [input, setInput] = useState('NVDA')
  const [ticker, setTicker] = useState('')
  const { data, isFetching, refetch } = useQuery({
    queryKey: ['options', ticker],
    queryFn: () => advancedApi.options(ticker),
    enabled: !!ticker,
  })

  const handleSearch = () => { if (input) setTicker(input) }

  return (
    <div>
      <TickerSearch value={input} onChange={setInput} onSearch={handleSearch} />
      {isFetching && <p className="text-sm" style={{ color: '#475569' }}>Fetching options chain…</p>}
      {data && (
        <>
          {data.error && !data.unusual?.length && (
            <p className="text-sm" style={{ color: '#ef4444' }}>Options unavailable: {data.error}</p>
          )}
          {data.summary && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
              {[
                { label: 'Call OI', value: (data.summary.total_call_oi || 0).toLocaleString() },
                { label: 'Put OI', value: (data.summary.total_put_oi || 0).toLocaleString() },
                { label: 'P/C OI Ratio', value: (data.summary.pc_ratio || 0).toFixed(2) },
                { label: 'P/C Vol Ratio', value: (data.summary.pc_volume_ratio || 0).toFixed(2) },
              ].map(m => (
                <div key={m.label} style={CARD}>
                  <p className="text-xs mb-1" style={{ color: '#475569' }}>{m.label}</p>
                  <p className="text-xl font-bold" style={{ color: '#e2e8f0' }}>{m.value}</p>
                </div>
              ))}
            </div>
          )}
          {data.sentiment_label && (
            <div className="mb-4 flex items-center gap-3">
              <Badge label={`Options Sentiment: ${data.sentiment_label}`} color={data.sentiment_color || '#00d4ff'} />
            </div>
          )}
          {data.unusual?.length > 0 && (
            <>
              <h3 className="text-sm font-semibold mb-3" style={{ color: '#94a3b8' }}>
                Unusual Activity (Vol &gt; OI, Vol &gt; 100)
              </h3>
              <div className="overflow-x-auto rounded-xl" style={{ border: '1px solid rgba(255,255,255,0.06)' }}>
                <table className="w-full text-xs">
                  <thead>
                    <tr style={{ backgroundColor: '#1e2535' }}>
                      {['Expiry', 'Type', 'Strike', 'Volume', 'OI', 'Vol/OI', 'IV %', 'Last $'].map(h => (
                        <th key={h} className="px-3 py-2 text-left font-semibold" style={{ color: '#475569' }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data.unusual.map((u: any, i: number) => (
                      <tr key={i} style={{ borderTop: '1px solid rgba(255,255,255,0.04)' }}>
                        <td className="px-3 py-2" style={{ color: '#94a3b8' }}>{u.expiry}</td>
                        <td className="px-3 py-2">
                          <Badge label={u.type?.toUpperCase() || '—'} color={u.type === 'call' ? '#00e676' : '#ff1744'} />
                        </td>
                        <td className="px-3 py-2 font-semibold" style={{ color: '#e2e8f0' }}>${u.strike?.toFixed(1)}</td>
                        <td className="px-3 py-2 font-semibold" style={{ color: '#00d4ff' }}>{u.volume?.toLocaleString()}</td>
                        <td className="px-3 py-2" style={{ color: '#94a3b8' }}>{u.oi?.toLocaleString()}</td>
                        <td className="px-3 py-2" style={{ color: '#ffab00' }}>{u.vol_oi_ratio}x</td>
                        <td className="px-3 py-2" style={{ color: '#94a3b8' }}>{u.iv ? `${u.iv}%` : '—'}</td>
                        <td className="px-3 py-2" style={{ color: '#e2e8f0' }}>${u.last?.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
          {data.unusual?.length === 0 && !isFetching && ticker && (
            <p className="text-sm" style={{ color: '#475569' }}>No unusual options activity in the next 4 expiries.</p>
          )}
        </>
      )}
    </div>
  )
}

// ── Insider Tab ───────────────────────────────────────────────────────────────
function InsiderTab() {
  const [input, setInput] = useState('AAPL')
  const [ticker, setTicker] = useState('')
  const { data, isFetching } = useQuery({
    queryKey: ['insider', ticker],
    queryFn: () => advancedApi.insider(ticker),
    enabled: !!ticker,
  })

  return (
    <div>
      <TickerSearch value={input} onChange={setInput} onSearch={() => { if (input) setTicker(input) }} />
      {isFetching && <p className="text-sm" style={{ color: '#475569' }}>Fetching insider data…</p>}
      {data && (
        <>
          {data.cluster_buy && (
            <div className="mb-4 p-3 rounded-lg flex items-center gap-2"
              style={{ backgroundColor: '#00e67622', border: '1px solid #00e676' }}>
              <span className="text-sm font-semibold" style={{ color: '#00e676' }}>
                Cluster Buy Signal — {data.buy_count} insider purchases detected
              </span>
            </div>
          )}
          {data.transactions?.length > 0 ? (
            <div className="overflow-x-auto rounded-xl" style={{ border: '1px solid rgba(255,255,255,0.06)' }}>
              <table className="w-full text-xs">
                <thead>
                  <tr style={{ backgroundColor: '#1e2535' }}>
                    {Object.keys(data.transactions[0]).slice(0, 6).map((h: string) => (
                      <th key={h} className="px-3 py-2 text-left font-semibold" style={{ color: '#475569' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.transactions.map((r: any, i: number) => (
                    <tr key={i} style={{ borderTop: '1px solid rgba(255,255,255,0.04)' }}>
                      {Object.keys(data.transactions[0]).slice(0, 6).map((k: string) => (
                        <td key={k} className="px-3 py-2" style={{ color: '#94a3b8' }}>
                          {r[k] != null ? String(r[k]) : '—'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-sm" style={{ color: '#475569' }}>No recent insider transaction data.</p>
          )}
        </>
      )}
    </div>
  )
}

// ── Short Interest Tab ────────────────────────────────────────────────────────
function ShortTab() {
  const [input, setInput] = useState('AAPL')
  const [ticker, setTicker] = useState('')
  const { data, isFetching } = useQuery({
    queryKey: ['short', ticker],
    queryFn: () => advancedApi.shortInterest(ticker),
    enabled: !!ticker,
  })

  const riskColor = data?.squeeze_risk === 'High' ? '#ff1744'
    : data?.squeeze_risk === 'Moderate' ? '#ffab00' : '#00e676'

  return (
    <div>
      <TickerSearch value={input} onChange={setInput} onSearch={() => { if (input) setTicker(input) }} />
      {isFetching && <p className="text-sm" style={{ color: '#475569' }}>Fetching short interest…</p>}
      {data?.available && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
            {[
              { label: 'Short % of Float', value: `${(data.short_percent_of_float || 0).toFixed(1)}%` },
              { label: 'Days to Cover', value: (data.short_ratio || 0).toFixed(1) },
              { label: 'Shares Short', value: (data.shares_short || 0).toLocaleString() },
              { label: 'MoM Change', value: `${(data.short_percent_change || 0) > 0 ? '+' : ''}${(data.short_percent_change || 0).toFixed(1)}%` },
            ].map(m => (
              <div key={m.label} style={CARD}>
                <p className="text-xs mb-1" style={{ color: '#475569' }}>{m.label}</p>
                <p className="text-xl font-bold" style={{ color: '#e2e8f0' }}>{m.value}</p>
              </div>
            ))}
          </div>
          <div className="p-3 rounded-lg" style={{ backgroundColor: riskColor + '18', border: `1px solid ${riskColor}` }}>
            <span className="text-sm font-semibold" style={{ color: riskColor }}>
              Squeeze Risk: {data.squeeze_risk}
            </span>
            <p className="text-xs mt-1" style={{ color: '#94a3b8' }}>
              High risk = short% &gt; 20% AND days-to-cover &gt; 5
            </p>
          </div>
        </>
      )}
      {data && !data.available && !isFetching && ticker && (
        <p className="text-sm" style={{ color: '#475569' }}>Short interest data not available for {ticker}.</p>
      )}
    </div>
  )
}

// ── Institutional Tab ─────────────────────────────────────────────────────────
function InstitutionalTab() {
  const [input, setInput] = useState('AAPL')
  const [ticker, setTicker] = useState('')
  const { data, isFetching } = useQuery({
    queryKey: ['institutional', ticker],
    queryFn: () => advancedApi.institutional(ticker),
    enabled: !!ticker,
  })

  return (
    <div>
      <TickerSearch value={input} onChange={setInput} onSearch={() => { if (input) setTicker(input) }} />
      {isFetching && <p className="text-sm" style={{ color: '#475569' }}>Fetching 13F data…</p>}
      {data?.available && data.holders?.length > 0 && (
        <div className="overflow-x-auto rounded-xl" style={{ border: '1px solid rgba(255,255,255,0.06)' }}>
          <table className="w-full text-xs">
            <thead>
              <tr style={{ backgroundColor: '#1e2535' }}>
                {Object.keys(data.holders[0]).slice(0, 5).map((h: string) => (
                  <th key={h} className="px-3 py-2 text-left font-semibold" style={{ color: '#475569' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.holders.map((r: any, i: number) => (
                <tr key={i} style={{ borderTop: '1px solid rgba(255,255,255,0.04)' }}>
                  {Object.keys(data.holders[0]).slice(0, 5).map((k: string) => (
                    <td key={k} className="px-3 py-2" style={{ color: '#94a3b8' }}>
                      {r[k] != null ? String(r[k]) : '—'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {data && !data.available && !isFetching && ticker && (
        <p className="text-sm" style={{ color: '#475569' }}>Institutional holdings data not available.</p>
      )}
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function Advanced() {
  const [tab, setTab] = useState('options')

  return (
    <PageWrapper title="Advanced Analysis">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-1" style={{ color: '#e2e8f0' }}>Advanced Analysis</h1>
        <p className="text-sm" style={{ color: '#475569' }}>
          Options flow · Insider transactions · Short interest · Institutional 13F holdings
        </p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 mb-6 p-1 rounded-lg w-fit" style={{ backgroundColor: '#111827' }}>
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className="px-4 py-2 rounded-md text-sm font-medium transition-colors"
            style={{
              backgroundColor: tab === t.id ? '#1e2535' : 'transparent',
              color: tab === t.id ? '#00d4ff' : '#475569',
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div style={CARD}>
        {tab === 'options' && <OptionsTab />}
        {tab === 'insider' && <InsiderTab />}
        {tab === 'short' && <ShortTab />}
        {tab === 'institutional' && <InstitutionalTab />}
      </div>
    </PageWrapper>
  )
}
