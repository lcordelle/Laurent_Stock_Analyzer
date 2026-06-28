import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Bell, Plus, X, RefreshCw, AlertTriangle } from 'lucide-react'
import { alertsApi } from '../services/api'
import PageWrapper from '../components/layout/PageWrapper'

const CARD: React.CSSProperties = {
  backgroundColor: '#111827',
  border: '1px solid rgba(255,255,255,0.06)',
  borderRadius: 12,
  padding: '16px',
}

const CONDITION_LABELS: Record<string, string> = {
  price_above: 'Price Above',
  price_below: 'Price Below',
  rsi_above: 'RSI Above (overbought)',
  rsi_below: 'RSI Below (oversold)',
}

const CONDITION_HINTS: Record<string, string> = {
  price_above: 'Alert fires when price rises above your threshold.',
  price_below: 'Alert fires when price drops below your threshold.',
  rsi_above: 'Alert fires when RSI(14) exceeds threshold. Typical: 70 = overbought.',
  rsi_below: 'Alert fires when RSI(14) drops below threshold. Typical: 30 = oversold.',
}

function StatusPill({ fired }: { fired: boolean }) {
  return (
    <span className="px-2 py-0.5 rounded text-xs font-semibold"
      style={{ backgroundColor: fired ? '#ffab0022' : '#00e67622', color: fired ? '#ffab00' : '#00e676' }}>
      {fired ? 'Fired' : 'Active'}
    </span>
  )
}

export default function Alerts() {
  const qc = useQueryClient()
  const [searchParams] = useSearchParams()
  const { data, isFetching } = useQuery({ queryKey: ['alerts'], queryFn: alertsApi.list, refetchInterval: 30000 })

  const prefilledTicker = searchParams.get('ticker') ?? ''
  const [form, setForm] = useState({ ticker: prefilledTicker, condition: 'price_below', threshold: '' })
  const [showForm, setShowForm] = useState(!!prefilledTicker)

  useEffect(() => {
    const t = searchParams.get('ticker')
    if (t) { setForm(f => ({ ...f, ticker: t })); setShowForm(true) }
  }, [searchParams])

  const addMut = useMutation({
    mutationFn: () => alertsApi.add(form.ticker.toUpperCase(), form.condition, parseFloat(form.threshold)),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['alerts'] }); setShowForm(false); setForm({ ticker: '', condition: 'price_below', threshold: '' }) },
  })
  const delMut = useMutation({
    mutationFn: alertsApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['alerts'] }),
  })
  const resetMut = useMutation({
    mutationFn: alertsApi.reset,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['alerts'] }),
  })

  const alerts: any[] = data?.alerts || []
  const active = alerts.filter(a => !a.fired)
  const fired = alerts.filter(a => a.fired)
  const conditionLabels: Record<string, string> = data?.condition_labels || CONDITION_LABELS

  return (
    <PageWrapper>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold mb-1" style={{ color: '#e2e8f0' }}>Price & Signal Alerts</h1>
          <p className="text-sm" style={{ color: '#475569' }}>Set conditions · get Telegram notifications when triggered</p>
        </div>
        <button
          onClick={() => setShowForm(f => !f)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold"
          style={{ backgroundColor: '#00d4ff', color: '#0a0e1a' }}
        >
          <Plus className="w-4 h-4" /> Add Alert
        </button>
      </div>

      {/* Info banner */}
      <div className="mb-4 p-3 rounded-lg flex items-start gap-2"
        style={{ backgroundColor: '#ffab0011', border: '1px solid rgba(255,171,0,0.3)' }}>
        <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" style={{ color: '#ffab00' }} />
        <p className="text-xs" style={{ color: '#94a3b8' }}>
          To receive Telegram push notifications, set <code style={{ color: '#00d4ff' }}>TELEGRAM_BOT_TOKEN</code> and{' '}
          <code style={{ color: '#00d4ff' }}>TELEGRAM_CHAT_ID</code> environment variables on the server. Alerts are
          checked every 60 seconds regardless.
        </p>
      </div>

      {/* Add Alert Form */}
      {showForm && (
        <div className="mb-6 p-4 rounded-xl" style={{ backgroundColor: '#1e2535', border: '1px solid rgba(0,212,255,0.2)' }}>
          <h3 className="text-sm font-semibold mb-4" style={{ color: '#00d4ff' }}>Create Alert</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
            <div>
              <label className="text-xs block mb-1" style={{ color: '#475569' }}>Ticker</label>
              <input value={form.ticker} onChange={e => setForm(f => ({ ...f, ticker: e.target.value.toUpperCase() }))}
                placeholder="AAPL" className="w-full px-3 py-2 rounded-lg text-sm outline-none"
                style={{ backgroundColor: '#111827', border: '1px solid rgba(255,255,255,0.08)', color: '#e2e8f0' }} />
            </div>
            <div>
              <label className="text-xs block mb-1" style={{ color: '#475569' }}>Condition</label>
              <select value={form.condition} onChange={e => setForm(f => ({ ...f, condition: e.target.value }))}
                className="w-full px-3 py-2 rounded-lg text-sm outline-none"
                style={{ backgroundColor: '#111827', border: '1px solid rgba(255,255,255,0.08)', color: '#e2e8f0' }}>
                {Object.entries(conditionLabels).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs block mb-1" style={{ color: '#475569' }}>Threshold</label>
              <input type="number" value={form.threshold}
                onChange={e => setForm(f => ({ ...f, threshold: e.target.value }))}
                placeholder="e.g. 180.00" className="w-full px-3 py-2 rounded-lg text-sm outline-none"
                style={{ backgroundColor: '#111827', border: '1px solid rgba(255,255,255,0.08)', color: '#e2e8f0' }} />
            </div>
          </div>
          {form.condition && (
            <p className="text-xs mb-3" style={{ color: '#475569' }}>{CONDITION_HINTS[form.condition]}</p>
          )}
          <div className="flex gap-2">
            <button onClick={() => addMut.mutate()} disabled={!form.ticker || !form.threshold || addMut.isPending}
              className="px-4 py-2 rounded-lg text-sm font-semibold disabled:opacity-50"
              style={{ backgroundColor: '#00d4ff', color: '#0a0e1a' }}>
              {addMut.isPending ? 'Creating…' : 'Create Alert'}
            </button>
            <button onClick={() => setShowForm(false)} className="px-4 py-2 rounded-lg text-sm" style={{ color: '#94a3b8' }}>
              Cancel
            </button>
          </div>
        </div>
      )}

      {isFetching && !alerts.length && (
        <p className="text-sm" style={{ color: '#475569' }}>Loading alerts…</p>
      )}

      {/* Active Alerts */}
      <div style={CARD} className="mb-4">
        <h2 className="text-sm font-semibold mb-4 flex items-center gap-2" style={{ color: '#94a3b8' }}>
          <Bell className="w-4 h-4" style={{ color: '#00e676' }} />
          Monitoring ({active.length} active)
        </h2>
        {!active.length ? (
          <p className="text-sm" style={{ color: '#475569' }}>No active alerts. Create one above.</p>
        ) : (
          <div className="space-y-2">
            {active.map(a => (
              <div key={a.id} className="flex items-center justify-between py-2 px-3 rounded-lg"
                style={{ backgroundColor: '#1e2535' }}>
                <div className="flex items-center gap-3">
                  <span className="font-semibold text-sm" style={{ color: '#e2e8f0' }}>{a.ticker}</span>
                  <span className="text-xs" style={{ color: '#94a3b8' }}>
                    {conditionLabels[a.condition] || a.condition} <strong style={{ color: '#00d4ff' }}>{a.threshold}</strong>
                  </span>
                  <StatusPill fired={false} />
                  <span className="text-xs" style={{ color: '#475569' }}>set {a.created?.slice(0, 10)}</span>
                </div>
                <button onClick={() => delMut.mutate(a.id)} className="p-1" style={{ color: '#475569' }}>
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Fired Alerts */}
      {fired.length > 0 && (
        <div style={CARD}>
          <h2 className="text-sm font-semibold mb-4" style={{ color: '#94a3b8' }}>Fired ({fired.length})</h2>
          <div className="space-y-2">
            {fired.map(a => (
              <div key={a.id} className="flex items-center justify-between py-2 px-3 rounded-lg"
                style={{ backgroundColor: '#1e2535' }}>
                <div className="flex items-center gap-3">
                  <span className="font-semibold text-sm" style={{ color: '#e2e8f0' }}>{a.ticker}</span>
                  <span className="text-xs" style={{ color: '#94a3b8' }}>
                    {conditionLabels[a.condition] || a.condition} {a.threshold}
                  </span>
                  <StatusPill fired />
                  <span className="text-xs" style={{ color: '#475569' }}>at {a.fired_at?.slice(0, 16)}</span>
                </div>
                <div className="flex gap-1">
                  <button onClick={() => resetMut.mutate(a.id)} className="p-1" style={{ color: '#00d4ff' }}
                    title="Reset — re-arm the alert">
                    <RefreshCw className="w-3.5 h-3.5" />
                  </button>
                  <button onClick={() => delMut.mutate(a.id)} className="p-1" style={{ color: '#475569' }}>
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </PageWrapper>
  )
}
