import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { stockApi, portfolioApi } from '../services/api'
import type { BatchAnalysisResponse } from '../lib/types'
import { fmt, scoreColor } from '../lib/formatters'
import PageWrapper from '../components/layout/PageWrapper'

type TabId = 'screener' | 'portfolio'

const TABS: { id: TabId; label: string }[] = [
  { id: 'screener', label: 'Stock Screener' },
  { id: 'portfolio', label: 'Portfolio Analyzer' },
]

function Tab({ id, label, active, onClick }: { id: TabId; label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="px-4 py-2 text-sm font-medium transition-colors border-b-2"
      style={{
        color: active ? '#00d4ff' : '#94a3b8',
        borderColor: active ? '#00d4ff' : 'transparent',
      }}
      data-testid={`tab-${id}`}
    >
      {label}
    </button>
  )
}

function NumberInput({ label, id, value, onChange, placeholder }: {
  label: string; id: string; value: string; onChange: (v: string) => void; placeholder?: string
}) {
  return (
    <div>
      <label htmlFor={id} className="block text-xs font-medium mb-1" style={{ color: '#94a3b8' }}>{label}</label>
      <input
        id={id}
        type="number"
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-3 py-2 rounded-lg text-sm outline-none"
        style={{
          backgroundColor: '#1a2235',
          border: '1px solid rgba(255,255,255,0.08)',
          color: '#e2e8f0',
        }}
      />
    </div>
  )
}

function ScreenerTab() {
  const [tickers, setTickers] = useState('')
  const [peMin, setPeMin] = useState('')
  const [peMax, setPeMax] = useState('')
  const [marginMin, setMarginMin] = useState('')
  const [roeMin, setRoeMin] = useState('')
  const [growthMin, setGrowthMin] = useState('')

  const { mutate, data, isPending, isError } = useMutation<BatchAnalysisResponse, Error, Parameters<typeof stockApi.screen>>({
    mutationFn: ([tickerList, filters]) => stockApi.screen(tickerList, filters),
  })

  const handleRun = () => {
    const tickerList = tickers.split(/[,\s\n]+/).map(t => t.trim().toUpperCase()).filter(Boolean).slice(0, 20)
    if (!tickerList.length) return
    const filters: Record<string, number> = {}
    if (peMin) filters.pe_min = parseFloat(peMin)
    if (peMax) filters.pe_max = parseFloat(peMax)
    if (marginMin) filters.margin_min = parseFloat(marginMin) / 100
    if (roeMin) filters.roe_min = parseFloat(roeMin) / 100
    if (growthMin) filters.growth_min = parseFloat(growthMin) / 100
    mutate([tickerList, filters])
  }

  const results = data?.results ?? []

  return (
    <div className="flex flex-col gap-5">
      <div
        className="rounded-xl border p-5 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4"
        style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
      >
        <div className="col-span-2 md:col-span-3 lg:col-span-6">
          <label className="block text-xs font-medium mb-1" style={{ color: '#94a3b8' }}>Tickers (max 20)</label>
          <input
            type="text"
            value={tickers}
            onChange={e => setTickers(e.target.value)}
            placeholder="AAPL, MSFT, GOOGL, ..."
            className="w-full px-3 py-2 rounded-lg text-sm font-mono outline-none"
            style={{
              backgroundColor: '#1a2235',
              border: '1px solid rgba(255,255,255,0.08)',
              color: '#e2e8f0',
            }}
            data-testid="screener-tickers"
          />
        </div>
        <NumberInput label="P/E Min" id="pe-min" value={peMin} onChange={setPeMin} placeholder="0" />
        <NumberInput label="P/E Max" id="pe-max" value={peMax} onChange={setPeMax} placeholder="50" />
        <NumberInput label="Gross Margin Min %" id="margin-min" value={marginMin} onChange={setMarginMin} placeholder="20" />
        <NumberInput label="ROE Min %" id="roe-min" value={roeMin} onChange={setRoeMin} placeholder="10" />
        <NumberInput label="Rev Growth Min %" id="growth-min" value={growthMin} onChange={setGrowthMin} placeholder="5" />
        <div className="flex items-end">
          <button
            onClick={handleRun}
            disabled={isPending || !tickers.trim()}
            className="w-full py-2 rounded-lg text-sm font-semibold flex items-center justify-center gap-2 disabled:opacity-50"
            style={{ background: 'linear-gradient(135deg, #00d4ff, #0088cc)', color: '#0a0e1a' }}
            data-testid="screener-run-btn"
          >
            {isPending && <Loader2 className="w-4 h-4 animate-spin" />}
            {isPending ? 'Screening...' : 'Run Screen'}
          </button>
        </div>
      </div>

      {isError && (
        <div
          className="rounded-xl border p-4"
          style={{ backgroundColor: 'rgba(255,23,68,0.05)', borderColor: 'rgba(255,23,68,0.2)' }}
          role="alert"
        >
          <p className="text-sm" style={{ color: '#ff1744' }}>Screener failed. Check tickers and try again.</p>
        </div>
      )}

      {results.length > 0 && (
        <div
          className="rounded-xl border overflow-hidden"
          style={{ borderColor: 'rgba(255,255,255,0.06)' }}
          data-testid="screener-results"
        >
          <table className="w-full text-sm">
            <thead>
              <tr style={{ backgroundColor: '#1a2235' }}>
                {['Ticker', 'Company', 'Score', 'Price', 'P/E', 'Gross Margin', 'ROE', 'Rev Growth'].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider" style={{ color: '#94a3b8' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {results
                .sort((a, b) => (b.score?.total ?? 0) - (a.score?.total ?? 0))
                .map(stock => {
                  const score = stock.score?.total ?? 0
                  const m = stock.metrics
                  return (
                    <tr
                      key={stock.ticker}
                      className="border-t hover:bg-white/[0.02] transition-colors"
                      style={{ borderColor: 'rgba(255,255,255,0.04)' }}
                    >
                      <td className="px-4 py-3">
                        <span className="font-bold font-mono text-xs px-2 py-0.5 rounded" style={{ color: '#00d4ff', backgroundColor: '#00d4ff20' }}>
                          {stock.ticker}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs" style={{ color: '#94a3b8' }}>{stock.company_name ?? '—'}</td>
                      <td className="px-4 py-3">
                        <span className="text-sm font-bold" style={{ color: scoreColor(score) }}>{Math.round(score)}</span>
                      </td>
                      <td className="px-4 py-3 text-xs tabular-nums" style={{ color: '#e2e8f0' }}>{fmt.price(m?.current_price)}</td>
                      <td className="px-4 py-3 text-xs tabular-nums" style={{ color: '#e2e8f0' }}>{fmt.ratio(m?.pe_ratio)}</td>
                      <td className="px-4 py-3 text-xs tabular-nums" style={{ color: '#e2e8f0' }}>{m?.gross_margin != null ? fmt.pct(m.gross_margin) : '—'}</td>
                      <td className="px-4 py-3 text-xs tabular-nums" style={{ color: '#e2e8f0' }}>{m?.roe != null ? fmt.pct(m.roe) : '—'}</td>
                      <td className="px-4 py-3 text-xs tabular-nums" style={{ color: '#e2e8f0' }}>{m?.revenue_growth != null ? fmt.pct(m.revenue_growth) : '—'}</td>
                    </tr>
                  )
                })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

interface HoldingSignals {
  signal?: string
  confidence?: number
  rsi?: number
  rsi_signal?: string
  macd_signal?: string
  trend?: string
  stop_loss?: number
  tp1?: number
  tp2?: number
  tp3?: number
  risk_reward?: number
  vf_score?: number
}

interface PortfolioHolding {
  shares: number
  current_price: number
  market_value: number
  info: { sector?: string; industry?: string; shortName?: string }
  signals?: HoldingSignals
}

interface PortfolioResult {
  error?: string
  total_value?: number
  num_holdings?: number
  weighted_pe?: number
  weighted_forward_pe?: number
  weighted_peg?: number
  weighted_roe?: number
  weighted_roa?: number
  weighted_gross_margin?: number
  weighted_operating_margin?: number
  weighted_profit_margin?: number
  weighted_revenue_growth?: number
  weighted_beta?: number
  weighted_dividend_yield?: number
  sector_allocation?: Record<string, number>
  industry_allocation?: Record<string, number>
  concentration_hhi?: number
  portfolio_data?: Record<string, PortfolioHolding>
}

function MetricTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl p-3 border" style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
      <div className="text-xs mb-1" style={{ color: '#94a3b8' }}>{label}</div>
      <div className="text-sm font-bold tabular-nums" style={{ color: '#e2e8f0' }}>{value}</div>
    </div>
  )
}

function PortfolioTab() {
  const [input, setInput] = useState('')

  const { mutate, data, isPending, isError } = useMutation<PortfolioResult, Error, string>({
    mutationFn: (text) => portfolioApi.analyze(text),
  })

  const holdings = data?.portfolio_data ? Object.entries(data.portfolio_data) : []
  const totalValue = data?.total_value ?? 0

  const hhi = data?.concentration_hhi ?? 0
  const concentrationLabel = hhi > 2500 ? 'High' : hhi > 1500 ? 'Moderate' : 'Diversified'
  const concentrationColor = hhi > 2500 ? '#ff1744' : hhi > 1500 ? '#ffab00' : '#00e676'

  return (
    <div className="flex flex-col gap-5">
      <div
        className="rounded-xl border p-5 flex flex-col gap-4"
        style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
      >
        <div>
          <label htmlFor="portfolio-input" className="block text-xs font-medium mb-1.5" style={{ color: '#94a3b8' }}>
            Portfolio Holdings (format: TICKER:SHARES per line)
          </label>
          <textarea
            id="portfolio-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            rows={5}
            placeholder={'AAPL:10\nMSFT:5\nNVDA:3\nGOOGL:2'}
            className="w-full px-3 py-2.5 rounded-lg text-sm font-mono outline-none resize-none"
            style={{
              backgroundColor: '#1a2235',
              border: '1px solid rgba(255,255,255,0.08)',
              color: '#e2e8f0',
            }}
            data-testid="portfolio-input"
          />
        </div>
        <button
          onClick={() => mutate(input)}
          disabled={isPending || !input.trim()}
          className="self-start px-5 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2 disabled:opacity-50"
          style={{ background: 'linear-gradient(135deg, #00d4ff, #0088cc)', color: '#0a0e1a' }}
          data-testid="portfolio-analyze-btn"
        >
          {isPending && <Loader2 className="w-4 h-4 animate-spin" />}
          {isPending ? 'Analyzing...' : 'Analyze Portfolio'}
        </button>
      </div>

      {isError && (
        <div
          className="rounded-xl border p-4"
          style={{ backgroundColor: 'rgba(255,23,68,0.05)', borderColor: 'rgba(255,23,68,0.2)' }}
          role="alert"
        >
          <p className="text-sm" style={{ color: '#ff1744' }}>Portfolio analysis failed. Check your input format.</p>
        </div>
      )}

      {data?.error && (
        <div className="rounded-xl border p-4" style={{ backgroundColor: 'rgba(255,23,68,0.05)', borderColor: 'rgba(255,23,68,0.2)' }}>
          <p className="text-sm" style={{ color: '#ff1744' }}>{data.error}</p>
        </div>
      )}

      {data && !data.error && holdings.length > 0 && (
        <div className="flex flex-col gap-5" data-testid="portfolio-results">
          {/* Summary row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <MetricTile label="Total Value" value={fmt.currency(totalValue)} />
            <MetricTile label="Holdings" value={String(data.num_holdings ?? holdings.length)} />
            <MetricTile label="Portfolio Beta" value={(data.weighted_beta ?? 0).toFixed(2)} />
            <div className="rounded-xl p-3 border" style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
              <div className="text-xs mb-1" style={{ color: '#94a3b8' }}>Concentration</div>
              <div className="text-sm font-bold" style={{ color: concentrationColor }}>{concentrationLabel}</div>
            </div>
          </div>

          {/* Holdings table with signals */}
          <div className="rounded-xl border overflow-hidden" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
            <div className="px-4 py-3 border-b" style={{ backgroundColor: '#1a2235', borderColor: 'rgba(255,255,255,0.06)' }}>
              <h3 className="text-sm font-semibold" style={{ color: '#e2e8f0' }}>Holdings & Signals</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm min-w-[900px]">
                <thead>
                  <tr style={{ backgroundColor: '#111827' }}>
                    {['Ticker', 'Name', 'Shares', 'Price', 'Value', 'Weight', 'Signal', 'Confidence', 'VF Score', 'Stop Loss', 'TP1', 'Trend'].map(h => (
                      <th key={h} className="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wider whitespace-nowrap" style={{ color: '#94a3b8' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {holdings.map(([ticker, h]) => {
                    const weight = totalValue > 0 ? (h.market_value / totalValue) * 100 : 0
                    const sig = h.signals ?? {}
                    const signalColor = sig.signal?.includes('BUY') ? '#00e676' : sig.signal?.includes('SELL') ? '#ff1744' : '#ffab00'
                    const vfColor = scoreColor(sig.vf_score ?? 0)
                    return (
                      <tr key={ticker} className="border-t hover:bg-white/[0.02]" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
                        <td className="px-3 py-3">
                          <a href={`/analysis?ticker=${ticker}`} className="font-bold font-mono text-xs px-2 py-0.5 rounded hover:opacity-80" style={{ color: '#00d4ff', backgroundColor: '#00d4ff20' }}>
                            {ticker}
                          </a>
                        </td>
                        <td className="px-3 py-3 text-xs max-w-[120px] truncate" style={{ color: '#94a3b8' }}>{h.info?.shortName ?? '—'}</td>
                        <td className="px-3 py-3 text-xs tabular-nums" style={{ color: '#e2e8f0' }}>{h.shares}</td>
                        <td className="px-3 py-3 text-xs tabular-nums" style={{ color: '#e2e8f0' }}>{fmt.price(h.current_price)}</td>
                        <td className="px-3 py-3 text-xs tabular-nums font-semibold" style={{ color: '#e2e8f0' }}>{fmt.currency(h.market_value)}</td>
                        <td className="px-3 py-3 text-xs tabular-nums" style={{ color: '#00d4ff' }}>{weight.toFixed(1)}%</td>
                        <td className="px-3 py-3">
                          {sig.signal ? (
                            <span className="text-xs font-bold px-2 py-0.5 rounded" style={{ color: signalColor, backgroundColor: `${signalColor}20` }}>
                              {sig.signal}
                            </span>
                          ) : '—'}
                        </td>
                        <td className="px-3 py-3">
                          {sig.confidence != null ? (
                            <div className="flex items-center gap-2">
                              <div className="w-16 bg-white/10 rounded-full h-1.5">
                                <div className="h-1.5 rounded-full" style={{ width: `${sig.confidence}%`, backgroundColor: signalColor }} />
                              </div>
                              <span className="text-xs tabular-nums" style={{ color: '#94a3b8' }}>{sig.confidence}%</span>
                            </div>
                          ) : '—'}
                        </td>
                        <td className="px-3 py-3 text-xs font-bold tabular-nums" style={{ color: vfColor }}>{sig.vf_score ?? '—'}</td>
                        <td className="px-3 py-3 text-xs tabular-nums" style={{ color: '#ff1744' }}>{sig.stop_loss ? fmt.price(sig.stop_loss) : '—'}</td>
                        <td className="px-3 py-3 text-xs tabular-nums" style={{ color: '#00e676' }}>{sig.tp1 ? fmt.price(sig.tp1) : '—'}</td>
                        <td className="px-3 py-3 text-xs whitespace-nowrap" style={{ color: '#94a3b8' }}>{sig.trend ?? '—'}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Portfolio fundamentals */}
          <div className="rounded-xl border overflow-hidden" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
            <div className="px-4 py-3 border-b" style={{ backgroundColor: '#1a2235', borderColor: 'rgba(255,255,255,0.06)' }}>
              <h3 className="text-sm font-semibold" style={{ color: '#e2e8f0' }}>Weighted Fundamentals</h3>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 p-4">
              <MetricTile label="P/E (TTM)" value={(data.weighted_pe ?? 0).toFixed(1) + 'x'} />
              <MetricTile label="Forward P/E" value={(data.weighted_forward_pe ?? 0).toFixed(1) + 'x'} />
              <MetricTile label="PEG Ratio" value={(data.weighted_peg ?? 0).toFixed(2)} />
              <MetricTile label="ROE" value={((data.weighted_roe ?? 0) * 100).toFixed(1) + '%'} />
              <MetricTile label="ROA" value={((data.weighted_roa ?? 0) * 100).toFixed(1) + '%'} />
              <MetricTile label="Gross Margin" value={(data.weighted_gross_margin ?? 0).toFixed(1) + '%'} />
              <MetricTile label="Operating Margin" value={(data.weighted_operating_margin ?? 0).toFixed(1) + '%'} />
              <MetricTile label="Net Margin" value={(data.weighted_profit_margin ?? 0).toFixed(1) + '%'} />
              <MetricTile label="Revenue Growth" value={(data.weighted_revenue_growth ?? 0).toFixed(1) + '%'} />
            </div>
          </div>

          {/* Risk Simulation */}
          {holdings.length > 0 && (() => {
            const beta = data.weighted_beta ?? 1
            const portfolioStdDev = beta * 0.045
            const var95 = 1.645 * portfolioStdDev * totalValue
            const riskFreeRate = 0.053
            const expectedReturn = holdings.reduce((sum, [, h]) => {
              const sig = h.signals ?? {}
              const weight = totalValue > 0 ? h.market_value / totalValue : 0
              const tp1Upside = sig.tp1 && h.current_price ? (sig.tp1 - h.current_price) / h.current_price : 0.08
              const confidence = (sig.confidence ?? 60) / 100
              return sum + weight * tp1Upside * confidence
            }, 0)
            const annualReturn = expectedReturn * 4
            const sharpe = portfolioStdDev > 0 ? (annualReturn - riskFreeRate) / (portfolioStdDev * Math.sqrt(12)) : 0
            const maxDrawdownApprox = portfolioStdDev * 2.5 * totalValue

            const riskItems = [
              {
                label: 'Expected Return (annualised)',
                value: `${(annualReturn * 100).toFixed(1)}%`,
                color: annualReturn > 0.1 ? '#00e676' : annualReturn > 0 ? '#ffab00' : '#ff1744',
              },
              {
                label: 'Sharpe Ratio',
                value: sharpe.toFixed(2),
                color: sharpe > 1 ? '#00e676' : sharpe > 0.5 ? '#ffab00' : '#ff1744',
              },
              {
                label: 'VaR 95% (1-month)',
                value: `-${fmt.currency(var95)}`,
                color: '#ff1744',
              },
              {
                label: 'Est. Max Drawdown',
                value: `-${fmt.currency(maxDrawdownApprox)}`,
                color: '#ffab00',
              },
            ]

            return (
              <div className="rounded-xl border overflow-hidden" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
                <div className="px-4 py-3 border-b" style={{ backgroundColor: '#1a2235', borderColor: 'rgba(255,255,255,0.06)' }}>
                  <h3 className="text-sm font-semibold" style={{ color: '#e2e8f0' }}>Risk Simulation</h3>
                  <p className="text-xs mt-0.5" style={{ color: '#475569' }}>Based on TP1 targets × signal confidence × portfolio beta</p>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4">
                  {riskItems.map(({ label, value, color }) => (
                    <div key={label} className="rounded-xl p-3 border" style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}>
                      <div className="text-xs mb-1" style={{ color: '#94a3b8' }}>{label}</div>
                      <div className="text-sm font-bold tabular-nums" style={{ color }}>{value}</div>
                    </div>
                  ))}
                </div>
              </div>
            )
          })()}

          {/* Sector allocation */}
          {data.sector_allocation && Object.keys(data.sector_allocation).length > 0 && (
            <div className="rounded-xl border overflow-hidden" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
              <div className="px-4 py-3 border-b" style={{ backgroundColor: '#1a2235', borderColor: 'rgba(255,255,255,0.06)' }}>
                <h3 className="text-sm font-semibold" style={{ color: '#e2e8f0' }}>Sector Allocation</h3>
              </div>
              <div className="p-4 flex flex-col gap-2">
                {Object.entries(data.sector_allocation)
                  .sort(([, a], [, b]) => b - a)
                  .map(([sector, value]) => {
                    const pct = totalValue > 0 ? (value / totalValue) * 100 : 0
                    return (
                      <div key={sector} className="flex items-center gap-3">
                        <div className="w-28 text-xs shrink-0" style={{ color: '#94a3b8' }}>{sector}</div>
                        <div className="flex-1 bg-white/5 rounded-full h-2">
                          <div className="h-2 rounded-full" style={{ width: `${pct}%`, backgroundColor: '#00d4ff' }} />
                        </div>
                        <div className="text-xs tabular-nums w-12 text-right font-semibold" style={{ color: '#e2e8f0' }}>{pct.toFixed(1)}%</div>
                        <div className="text-xs tabular-nums w-20 text-right" style={{ color: '#94a3b8' }}>{fmt.currency(value)}</div>
                      </div>
                    )
                  })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function Screener() {
  const [activeTab, setActiveTab] = useState<TabId>('screener')

  return (
    <PageWrapper>
      <div className="flex flex-col gap-6">
        <div>
          <h1 className="text-xl font-bold mb-1" style={{ color: '#e2e8f0' }}>Screener & Portfolio</h1>
          <p className="text-sm" style={{ color: '#94a3b8' }}>Filter stocks by fundamentals or analyze your portfolio</p>
        </div>

        <div className="flex gap-0 border-b" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
          {TABS.map(t => (
            <Tab key={t.id} {...t} active={activeTab === t.id} onClick={() => setActiveTab(t.id)} />
          ))}
        </div>

        {activeTab === 'screener' ? <ScreenerTab /> : <PortfolioTab />}
      </div>
    </PageWrapper>
  )
}
