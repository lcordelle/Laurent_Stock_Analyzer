import type { RiskProfile as RiskProfileType } from '../../lib/types'

interface Props {
  riskProfile: RiskProfileType
  ticker: string
}

interface MetricCfg {
  label: string
  value: string
  color: string
  caption: string
}

function metricCfg(rp: RiskProfileType): MetricCfg[] {
  const col = {
    green: '#00e676',
    amber: '#ffab00',
    red: '#ff1744',
    neutral: '#94a3b8',
  }

  return [
    {
      label: 'Volatility',
      value: rp.volatility != null ? `${rp.volatility.toFixed(1)}%` : '—',
      color: rp.volatility == null ? col.neutral : rp.volatility <= 20 ? col.green : rp.volatility <= 35 ? col.amber : col.red,
      caption: 'Annualised daily return std dev',
    },
    {
      label: 'Sharpe Ratio',
      value: rp.sharpe_ratio != null ? rp.sharpe_ratio.toFixed(2) : '—',
      color: rp.sharpe_ratio == null ? col.neutral : rp.sharpe_ratio > 1 ? col.green : rp.sharpe_ratio > 0 ? col.amber : col.red,
      caption: 'Return per unit of total risk · assumes risk-free rate 4.3%',
    },
    {
      label: 'Sortino Ratio',
      value: rp.sortino_ratio != null ? rp.sortino_ratio.toFixed(2) : '—',
      color: rp.sortino_ratio == null ? col.neutral : rp.sortino_ratio > 1 ? col.green : rp.sortino_ratio > 0 ? col.amber : col.red,
      caption: 'Return per unit of downside risk · assumes risk-free rate 4.3%',
    },
    {
      label: 'VaR (5%)',
      value: rp.var_5pct != null ? `${rp.var_5pct.toFixed(2)}%` : '—',
      color: rp.var_5pct == null ? col.neutral : rp.var_5pct <= 2 ? col.green : rp.var_5pct <= 4 ? col.amber : col.red,
      caption: '95th-pct max daily loss',
    },
    {
      label: 'Max Drawdown',
      value: rp.max_drawdown_pct != null ? `${rp.max_drawdown_pct.toFixed(1)}%` : '—',
      color: rp.max_drawdown_pct == null ? col.neutral : rp.max_drawdown_pct <= 15 ? col.green : rp.max_drawdown_pct <= 30 ? col.amber : col.red,
      caption: 'Peak-to-trough decline',
    },
  ]
}

export default function RiskProfile({ riskProfile, ticker }: Props) {
  const metrics = metricCfg(riskProfile)

  return (
    <div className="rounded-xl p-4" style={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.06)' }}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-semibold uppercase tracking-wide" style={{ color: '#94a3b8' }}>
          Risk Profile — {ticker}
        </span>
        <span className="text-xs" style={{ color: '#475569' }}>Trailing 1-year daily returns</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {metrics.map(m => (
          <div
            key={m.label}
            className="rounded-lg p-3 flex flex-col gap-1"
            style={{ backgroundColor: '#111827', border: '1px solid rgba(255,255,255,0.06)' }}
          >
            <span className="text-xs font-medium uppercase tracking-wide" style={{ color: '#475569' }}>
              {m.label}
            </span>
            <span className="text-lg font-bold" style={{ color: m.color }}>
              {m.value}
            </span>
            <span className="text-xs" style={{ color: '#475569' }}>
              {m.caption}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
