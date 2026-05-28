import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, X, CheckCircle, BookOpen } from 'lucide-react'
import { journalApi } from '../services/api'
import PageWrapper from '../components/layout/PageWrapper'

const CARD: React.CSSProperties = {
  backgroundColor: '#111827',
  border: '1px solid rgba(255,255,255,0.06)',
  borderRadius: 12,
  padding: '16px',
}

function pnlColor(v: number) { return v > 0 ? '#00e676' : v < 0 ? '#ff1744' : '#94a3b8' }

function KPI({ label, value, color = '#e2e8f0' }: { label: string; value: string; color?: string }) {
  return (
    <div style={CARD}>
      <p className="text-xs mb-1" style={{ color: '#475569' }}>{label}</p>
      <p className="text-xl font-bold" style={{ color }}>{value}</p>
    </div>
  )
}

// ── Add Trade Form ────────────────────────────────────────────────────────────
function AddTradeForm({ onDone }: { onDone: () => void }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({
    ticker: '', direction: 'LONG', entry_date: new Date().toISOString().slice(0, 10),
    entry_price: '', shares: '', notes: '', tags: '',
  })

  const mutation = useMutation({
    mutationFn: () => journalApi.add({
      ticker: form.ticker.toUpperCase(),
      direction: form.direction,
      entry_date: form.entry_date,
      entry_price: parseFloat(form.entry_price),
      shares: parseFloat(form.shares),
      notes: form.notes,
      tags: form.tags,
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['journal-open'] })
      onDone()
    },
  })

  const field = (label: string, key: keyof typeof form, type = 'text', opts?: string[]) => (
    <div>
      <label className="block text-xs mb-1" style={{ color: '#475569' }}>{label}</label>
      {opts ? (
        <select
          value={form[key]}
          onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
          className="w-full px-3 py-2 rounded-lg text-sm outline-none"
          style={{ backgroundColor: '#1e2535', border: '1px solid rgba(255,255,255,0.08)', color: '#e2e8f0' }}
        >
          {opts.map(o => <option key={o} value={o}>{o}</option>)}
        </select>
      ) : (
        <input
          type={type}
          value={form[key]}
          onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
          className="w-full px-3 py-2 rounded-lg text-sm outline-none"
          style={{ backgroundColor: '#1e2535', border: '1px solid rgba(255,255,255,0.08)', color: '#e2e8f0' }}
        />
      )}
    </div>
  )

  return (
    <div className="mb-6 p-4 rounded-xl" style={{ backgroundColor: '#1e2535', border: '1px solid rgba(0,212,255,0.2)' }}>
      <h3 className="text-sm font-semibold mb-4" style={{ color: '#00d4ff' }}>Log New Trade</h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-3">
        {field('Ticker', 'ticker')}
        {field('Direction', 'direction', 'text', ['LONG', 'SHORT'])}
        {field('Entry Date', 'entry_date', 'date')}
        {field('Entry Price ($)', 'entry_price', 'number')}
        {field('Shares', 'shares', 'number')}
        {field('Tags', 'tags')}
      </div>
      <div className="mb-3">
        <label className="block text-xs mb-1" style={{ color: '#475569' }}>Notes</label>
        <textarea
          value={form.notes}
          onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
          rows={2}
          className="w-full px-3 py-2 rounded-lg text-sm outline-none resize-none"
          style={{ backgroundColor: '#111827', border: '1px solid rgba(255,255,255,0.08)', color: '#e2e8f0' }}
        />
      </div>
      <div className="flex gap-2">
        <button
          onClick={() => mutation.mutate()}
          disabled={!form.ticker || !form.entry_price || !form.shares || mutation.isPending}
          className="px-4 py-2 rounded-lg text-sm font-semibold disabled:opacity-50"
          style={{ backgroundColor: '#00d4ff', color: '#0a0e1a' }}
        >
          {mutation.isPending ? 'Saving…' : 'Log Trade'}
        </button>
        <button onClick={onDone} className="px-4 py-2 rounded-lg text-sm" style={{ color: '#94a3b8' }}>
          Cancel
        </button>
      </div>
    </div>
  )
}

// ── Open Positions ────────────────────────────────────────────────────────────
function OpenPositions() {
  const qc = useQueryClient()
  const { data = [], isFetching } = useQuery({ queryKey: ['journal-open'], queryFn: journalApi.open })
  const [closing, setClosing] = useState<number | null>(null)
  const [closeForm, setCloseForm] = useState({ exit_date: new Date().toISOString().slice(0, 10), exit_price: '' })

  const closeMut = useMutation({
    mutationFn: (id: number) => journalApi.close(id, closeForm.exit_date, parseFloat(closeForm.exit_price)),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['journal-open'] }); qc.invalidateQueries({ queryKey: ['journal-closed'] }); setClosing(null) },
  })
  const delMut = useMutation({
    mutationFn: journalApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['journal-open'] }),
  })

  if (isFetching) return <p className="text-sm" style={{ color: '#475569' }}>Loading positions…</p>
  if (!data.length) return <p className="text-sm" style={{ color: '#475569' }}>No open positions. Click "Add Trade" to log your first entry.</p>

  return (
    <div className="space-y-3">
      {data.map((t: any) => (
        <div key={t.id} style={{ ...CARD, padding: '12px 16px' }}>
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-base font-bold" style={{ color: '#e2e8f0' }}>{t.ticker}</span>
                <span className="px-2 py-0.5 rounded text-xs font-semibold"
                  style={{ backgroundColor: t.direction === 'LONG' ? '#00e67622' : '#ff174422', color: t.direction === 'LONG' ? '#00e676' : '#ff1744' }}>
                  {t.direction}
                </span>
                <span className="text-xs" style={{ color: '#475569' }}>{t.shares} shares @ ${t.entry_price?.toFixed(2)}</span>
                <span className="text-xs" style={{ color: '#475569' }}>entered {t.entry_date}</span>
              </div>
              {t.notes && <p className="text-xs" style={{ color: '#475569' }}>{t.notes}</p>}
            </div>
            <div className="flex gap-2">
              <button onClick={() => setClosing(t.id)} className="p-1.5 rounded text-xs" style={{ color: '#00d4ff' }}>
                <CheckCircle className="w-4 h-4" />
              </button>
              <button onClick={() => delMut.mutate(t.id)} className="p-1.5 rounded text-xs" style={{ color: '#475569' }}>
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
          {closing === t.id && (
            <div className="mt-3 flex items-center gap-3 flex-wrap">
              <div>
                <label className="text-xs block mb-1" style={{ color: '#475569' }}>Exit Date</label>
                <input type="date" value={closeForm.exit_date}
                  onChange={e => setCloseForm(f => ({ ...f, exit_date: e.target.value }))}
                  className="px-2 py-1 rounded text-sm outline-none"
                  style={{ backgroundColor: '#1e2535', border: '1px solid rgba(255,255,255,0.08)', color: '#e2e8f0' }} />
              </div>
              <div>
                <label className="text-xs block mb-1" style={{ color: '#475569' }}>Exit Price ($)</label>
                <input type="number" value={closeForm.exit_price}
                  onChange={e => setCloseForm(f => ({ ...f, exit_price: e.target.value }))}
                  className="px-2 py-1 rounded text-sm outline-none w-28"
                  style={{ backgroundColor: '#1e2535', border: '1px solid rgba(255,255,255,0.08)', color: '#e2e8f0' }} />
              </div>
              <button onClick={() => closeMut.mutate(t.id)} disabled={!closeForm.exit_price}
                className="mt-4 px-3 py-1 rounded text-xs font-semibold disabled:opacity-50"
                style={{ backgroundColor: '#00d4ff', color: '#0a0e1a' }}>
                Close Trade
              </button>
              <button onClick={() => setClosing(null)} className="mt-4 px-3 py-1 rounded text-xs" style={{ color: '#475569' }}>
                Cancel
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

// ── Closed Trades ─────────────────────────────────────────────────────────────
function ClosedTrades() {
  const { data: trades = [], isFetching } = useQuery({ queryKey: ['journal-closed'], queryFn: journalApi.closed })
  const { data: summary } = useQuery({ queryKey: ['journal-summary'], queryFn: journalApi.summary })

  if (isFetching) return <p className="text-sm" style={{ color: '#475569' }}>Loading closed trades…</p>

  return (
    <div>
      {summary && summary.total_trades > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          <KPI label="Total P&L" value={`$${summary.total_pnl > 0 ? '+' : ''}${summary.total_pnl?.toFixed(2)}`}
            color={pnlColor(summary.total_pnl)} />
          <KPI label="Win Rate" value={`${summary.win_rate}%`} color={summary.win_rate >= 50 ? '#00e676' : '#ff1744'} />
          <KPI label="Avg Return" value={`${summary.avg_pnl_pct > 0 ? '+' : ''}${summary.avg_pnl_pct?.toFixed(1)}%`}
            color={pnlColor(summary.avg_pnl_pct)} />
          <KPI label="Trades" value={String(summary.total_trades)} />
        </div>
      )}
      {!trades.length ? (
        <p className="text-sm" style={{ color: '#475569' }}>No closed trades yet.</p>
      ) : (
        <div className="overflow-x-auto rounded-xl" style={{ border: '1px solid rgba(255,255,255,0.06)' }}>
          <table className="w-full text-xs">
            <thead>
              <tr style={{ backgroundColor: '#1e2535' }}>
                {['Ticker', 'Dir', 'Entry', 'Entry $', 'Exit $', 'Shares', 'P&L %', 'P&L $', 'SPY %', 'Alpha %'].map(h => (
                  <th key={h} className="px-3 py-2 text-left font-semibold" style={{ color: '#475569' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {trades.map((t: any) => (
                <tr key={t.id} style={{ borderTop: '1px solid rgba(255,255,255,0.04)' }}>
                  <td className="px-3 py-2 font-semibold" style={{ color: '#e2e8f0' }}>{t.ticker}</td>
                  <td className="px-3 py-2">
                    <span className="px-1.5 rounded text-xs font-semibold"
                      style={{ backgroundColor: t.direction === 'LONG' ? '#00e67622' : '#ff174422', color: t.direction === 'LONG' ? '#00e676' : '#ff1744' }}>
                      {t.direction}
                    </span>
                  </td>
                  <td className="px-3 py-2" style={{ color: '#94a3b8' }}>{t.entry_date}</td>
                  <td className="px-3 py-2" style={{ color: '#94a3b8' }}>${t.entry_price?.toFixed(2)}</td>
                  <td className="px-3 py-2" style={{ color: '#94a3b8' }}>${t.exit_price?.toFixed(2)}</td>
                  <td className="px-3 py-2" style={{ color: '#94a3b8' }}>{t.shares}</td>
                  <td className="px-3 py-2 font-semibold" style={{ color: pnlColor(t.pnl_pct) }}>
                    {t.pnl_pct > 0 ? '+' : ''}{t.pnl_pct?.toFixed(2)}%
                  </td>
                  <td className="px-3 py-2 font-semibold" style={{ color: pnlColor(t.pnl_dollars) }}>
                    {t.pnl_dollars > 0 ? '+$' : '-$'}{Math.abs(t.pnl_dollars)?.toFixed(2)}
                  </td>
                  <td className="px-3 py-2" style={{ color: pnlColor(t.spy_return || 0) }}>
                    {(t.spy_return || 0) > 0 ? '+' : ''}{(t.spy_return || 0).toFixed(2)}%
                  </td>
                  <td className="px-3 py-2 font-semibold" style={{ color: pnlColor(t.alpha || 0) }}>
                    {(t.alpha || 0) > 0 ? '+' : ''}{(t.alpha || 0).toFixed(2)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function Journal() {
  const [tab, setTab] = useState<'open' | 'closed'>('open')
  const [showForm, setShowForm] = useState(false)

  return (
    <PageWrapper title="Trade Journal">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold mb-1" style={{ color: '#e2e8f0' }}>Trade Journal</h1>
          <p className="text-sm" style={{ color: '#475569' }}>Log entries · track P&L · compare vs SPY benchmark</p>
        </div>
        <button
          onClick={() => setShowForm(f => !f)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold"
          style={{ backgroundColor: '#00d4ff', color: '#0a0e1a' }}
        >
          <Plus className="w-4 h-4" /> Add Trade
        </button>
      </div>

      {showForm && <AddTradeForm onDone={() => setShowForm(false)} />}

      <div className="flex gap-1 mb-6 p-1 rounded-lg w-fit" style={{ backgroundColor: '#111827' }}>
        {(['open', 'closed'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className="px-5 py-2 rounded-md text-sm font-medium"
            style={{ backgroundColor: tab === t ? '#1e2535' : 'transparent', color: tab === t ? '#00d4ff' : '#475569' }}>
            {t === 'open' ? '📂 Open Positions' : '✅ Closed Trades'}
          </button>
        ))}
      </div>

      <div style={CARD}>
        {tab === 'open' ? <OpenPositions /> : <ClosedTrades />}
      </div>
    </PageWrapper>
  )
}
