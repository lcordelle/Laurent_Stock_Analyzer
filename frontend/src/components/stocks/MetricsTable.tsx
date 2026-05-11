import type { StockMetrics, ShortInterestData } from '../../lib/types'
import { fmt } from '../../lib/formatters'

interface MetricRow {
  label: string
  value: string
  color: string
}

function metricColor(val: number | undefined, goodAbove?: number, goodBelow?: number): string {
  if (val == null) return '#475569'
  if (goodAbove != null) return val > goodAbove ? '#00e676' : val > goodAbove * 0.5 ? '#ffab00' : '#ff1744'
  if (goodBelow != null) return val < goodBelow ? '#00e676' : val < goodBelow * 1.5 ? '#ffab00' : '#ff1744'
  return '#94a3b8'
}

function MetricCell({ label, value, color }: MetricRow) {
  return (
    <div className="flex justify-between items-center py-2 border-b" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
      <span className="text-xs" style={{ color: '#94a3b8' }}>{label}</span>
      <span className="text-xs font-semibold tabular-nums" style={{ color }}>{value}</span>
    </div>
  )
}

interface MetricsTableProps {
  metrics: StockMetrics
  shortInterest?: ShortInterestData | null
}

function formatSharesShort(n: number | null | undefined): string {
  if (n == null) return '—'
  if (n > 1_000_000_000) return `${(n / 1_000_000_000).toFixed(2)}b shares`
  if (n > 1_000_000) return `${(n / 1_000_000).toFixed(1)}m shares`
  return n.toLocaleString()
}

function shortFloatColor(pct: number | null | undefined): string {
  if (pct == null) return '#475569'
  if (pct < 0.03) return '#00e676'
  if (pct < 0.10) return '#ffab00'
  return '#ff1744'
}

function daysToCoverColor(ratio: number | null | undefined): string {
  if (ratio == null) return '#475569'
  if (ratio > 5) return '#ff1744'
  if (ratio > 3) return '#ffab00'
  return '#94a3b8'
}

interface OwnershipTileProps {
  label: string
  value: string
  color: string
}

function OwnershipTile({ label, value, color }: OwnershipTileProps) {
  return (
    <div
      style={{
        backgroundColor: '#0a0e1a',
        borderRadius: '0.5rem',
        padding: '0.625rem 0.75rem',
        border: '1px solid rgba(255,255,255,0.04)',
      }}
    >
      <div style={{ fontSize: '0.65rem', color: '#475569', marginBottom: '0.25rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {label}
      </div>
      <div style={{ fontSize: '0.9375rem', fontWeight: 700, color, fontVariantNumeric: 'tabular-nums' }}>
        {value}
      </div>
    </div>
  )
}

export default function MetricsTable({ metrics: m, shortInterest: si }: MetricsTableProps) {
  const valuation: MetricRow[] = [
    { label: 'P/E Ratio', value: fmt.ratio(m.pe_ratio), color: metricColor(m.pe_ratio, undefined, 25) },
    { label: 'Forward P/E', value: fmt.ratio(m.forward_pe), color: metricColor(m.forward_pe, undefined, 20) },
    { label: 'PEG Ratio', value: fmt.ratio(m.peg_ratio), color: metricColor(m.peg_ratio, undefined, 1.5) },
    { label: 'Price / Book', value: fmt.ratio(m.price_to_book), color: metricColor(m.price_to_book, undefined, 3) },
    { label: 'Market Cap', value: fmt.mcap(m.market_cap), color: '#94a3b8' },
    { label: 'Dividend Yield', value: m.dividend_yield != null ? fmt.pct(m.dividend_yield) : '—', color: metricColor(m.dividend_yield, 2) },
    { label: 'Beta', value: fmt.ratio(m.beta), color: metricColor(m.beta, undefined, 1.2) },
    { label: 'Target Price', value: fmt.price(m.target_price), color: '#00d4ff' },
  ]

  const profitability: MetricRow[] = [
    { label: 'Gross Margin', value: m.gross_margin != null ? fmt.pct(m.gross_margin) : '—', color: metricColor(m.gross_margin, 40) },
    { label: 'Operating Margin', value: m.operating_margin != null ? fmt.pct(m.operating_margin) : '—', color: metricColor(m.operating_margin, 15) },
    { label: 'Net Margin', value: m.profit_margin != null ? fmt.pct(m.profit_margin) : '—', color: metricColor(m.profit_margin, 10) },
    { label: 'ROE', value: m.roe != null ? fmt.pct(m.roe) : '—', color: metricColor(m.roe, 15) },
    { label: 'ROA', value: m.roa != null ? fmt.pct(m.roa) : '—', color: metricColor(m.roa, 5) },
    { label: 'Revenue Growth', value: m.revenue_growth != null ? fmt.pct(m.revenue_growth) : '—', color: metricColor(m.revenue_growth, 10) },
    { label: 'Debt / Equity', value: fmt.ratio(m.debt_to_equity), color: metricColor(m.debt_to_equity, undefined, 1) },
    { label: 'Current Ratio', value: fmt.ratio(m.current_ratio), color: metricColor(m.current_ratio, 1.5) },
  ]

  return (
    <div
      className="rounded-xl border p-5"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
      data-testid="metrics-table"
    >
      <h3 className="text-sm font-semibold mb-4 uppercase tracking-wide" style={{ color: '#94a3b8' }}>
        Financial Metrics
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: '#475569' }}>Valuation</p>
          {valuation.map(r => <MetricCell key={r.label} {...r} />)}
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: '#475569' }}>Profitability</p>
          {profitability.map(r => <MetricCell key={r.label} {...r} />)}
        </div>
      </div>

      {si && (
        <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '1rem', marginTop: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
            <p className="text-xs font-semibold uppercase tracking-wide" style={{ color: '#475569' }}>
              Ownership &amp; Short Interest
            </p>
            {si.short_pct_float != null && si.short_pct_float > 0.15 &&
             si.short_ratio != null && si.short_ratio > 5 && (
              <span
                style={{
                  fontSize: '0.65rem',
                  fontWeight: 700,
                  padding: '0.2rem 0.5rem',
                  borderRadius: '9999px',
                  backgroundColor: 'rgba(255,171,0,0.15)',
                  color: '#ffab00',
                  border: '1px solid rgba(255,171,0,0.3)',
                  letterSpacing: '0.03em',
                }}
              >
                ⚡ Squeeze Risk
              </span>
            )}
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            <OwnershipTile
              label="Short Float %"
              value={si.short_pct_float != null ? `${(si.short_pct_float * 100).toFixed(1)}%` : '—'}
              color={shortFloatColor(si.short_pct_float)}
            />
            <OwnershipTile
              label="Days to Cover"
              value={si.short_ratio != null ? si.short_ratio.toFixed(1) : '—'}
              color={daysToCoverColor(si.short_ratio)}
            />
            <OwnershipTile
              label="Insider Own %"
              value={si.insider_own_pct != null ? `${(si.insider_own_pct * 100).toFixed(1)}%` : '—'}
              color={si.insider_own_pct != null && si.insider_own_pct * 100 > 5 ? '#00e676' : '#94a3b8'}
            />
            <OwnershipTile
              label="Inst. Own %"
              value={si.institution_own_pct != null ? `${(si.institution_own_pct * 100).toFixed(1)}%` : '—'}
              color="#94a3b8"
            />
            <OwnershipTile
              label="Shares Short"
              value={formatSharesShort(si.shares_short)}
              color="#94a3b8"
            />
          </div>
        </div>
      )}
    </div>
  )
}
