import type { StockMetrics } from '../../lib/types'
import { fmt, changeColor } from '../../lib/formatters'

interface KPITileProps {
  label: string
  value: string
  borderColor: string
}

function KPITile({ label, value, borderColor }: KPITileProps) {
  return (
    <div
      className="rounded-lg p-3 border-l-2 flex flex-col gap-1"
      style={{ backgroundColor: '#111827', borderColor, borderLeftWidth: 2, borderTopWidth: 0, borderRightWidth: 0, borderBottomWidth: 0, border: `1px solid rgba(255,255,255,0.06)`, borderLeft: `2px solid ${borderColor}` }}
    >
      <span className="text-xs font-medium uppercase tracking-wide" style={{ color: '#475569' }}>
        {label}
      </span>
      <span className="text-sm font-semibold" style={{ color: '#e2e8f0' }}>
        {value}
      </span>
    </div>
  )
}

interface KPIStripProps {
  metrics: StockMetrics
  forecast?: ForecastResult
}

export default function KPIStrip({ metrics, forecast }: KPIStripProps) {
  const tiles = [
    {
      label: 'Current Price',
      value: fmt.price(metrics.current_price),
      borderColor: '#00d4ff',
    },
    {
      label: 'P/E Ratio',
      value: fmt.ratio(metrics.pe_ratio),
      borderColor: metrics.pe_ratio != null && metrics.pe_ratio < 25 ? '#00e676' : metrics.pe_ratio != null && metrics.pe_ratio < 40 ? '#ffab00' : '#ff1744',
    },
    {
      label: 'ROE',
      value: metrics.roe != null ? fmt.pct(metrics.roe) : '—',
      borderColor: metrics.roe != null && metrics.roe > 15 ? '#00e676' : metrics.roe != null && metrics.roe > 0 ? '#ffab00' : '#ff1744',
    },
    {
      label: 'Gross Margin',
      value: metrics.gross_margin != null ? fmt.pct(metrics.gross_margin) : '—',
      borderColor: metrics.gross_margin != null && metrics.gross_margin > 40 ? '#00e676' : metrics.gross_margin != null && metrics.gross_margin > 20 ? '#ffab00' : '#ff1744',
    },
    {
      label: 'Rev Growth',
      value: metrics.revenue_growth != null ? fmt.pct(metrics.revenue_growth) : '—',
      borderColor: changeColor(metrics.revenue_growth),
    },
    {
      label: 'Beta',
      value: fmt.ratio(metrics.beta),
      borderColor: metrics.beta != null && metrics.beta < 1.2 ? '#00e676' : '#ffab00',
    },
    {
      label: 'Div Yield',
      value: metrics.dividend_yield != null ? fmt.pct(metrics.dividend_yield) : '—',
      borderColor: metrics.dividend_yield != null && metrics.dividend_yield > 2 ? '#00e676' : '#475569',
    },
    (() => {
      const hi = metrics.fifty_two_week_high
      const lo = metrics.fifty_two_week_low
      const cp = metrics.current_price
      if (hi != null && lo != null && cp != null && hi > lo) {
        const pos = Math.round(((cp - lo) / (hi - lo)) * 100)
        return {
          label: '52W Range',
          value: `${pos}% of range`,
          borderColor: pos >= 80 ? '#00e676' : pos <= 20 ? '#ff1744' : '#475569',
        }
      }
      return { label: '52W Range', value: '—', borderColor: '#475569' }
    })(),
  ]

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3" data-testid="kpi-strip">
      {tiles.map(t => (
        <KPITile key={t.label} label={t.label} value={t.value} borderColor={t.borderColor} />
      ))}
    </div>
  )
}
