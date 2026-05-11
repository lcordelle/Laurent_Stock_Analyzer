import type { FullStockAnalysis } from '../../lib/types'
import { fmt, changeColor } from '../../lib/formatters'

interface Props {
  data: FullStockAnalysis
}

function signalMeta(signal?: string | null) {
  const s = (signal ?? '').toUpperCase()
  if (s.includes('STRONG BUY'))  return { label: 'STRONG BUY',  color: '#00e676', bg: '#00e67612' }
  if (s.includes('BUY'))         return { label: 'BUY',          color: '#00e676', bg: '#00e67610' }
  if (s.includes('STRONG SELL')) return { label: 'STRONG SELL',  color: '#ff1744', bg: '#ff174412' }
  if (s.includes('SELL'))        return { label: 'SELL',          color: '#ff5252', bg: '#ff525210' }
  return { label: 'HOLD', color: '#ffab00', bg: '#ffab0010' }
}

function analystColor(rec?: string | null) {
  const r = (rec ?? '').toLowerCase()
  if (r.includes('strong buy'))  return '#00e676'
  if (r.includes('buy'))         return '#69f0ae'
  if (r.includes('strong sell')) return '#ff1744'
  if (r.includes('sell'))        return '#ff5252'
  return '#ffab00'
}

function Row({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="flex items-center justify-between gap-4 py-1" style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
      <span className="text-xs uppercase tracking-wide" style={{ color: '#475569' }}>{label}</span>
      <span className="text-xs font-semibold tabular-nums" style={{ color: color ?? '#e2e8f0' }}>{value}</span>
    </div>
  )
}

function convictionTierColor(tier: string): string {
  if (tier === 'STRONG BUY') return '#00e676'
  if (tier === 'BUY')        return '#69f0ae'
  if (tier === 'WATCH')      return '#ffab00'
  return '#ff1744'
}

function computeConvictionTier(signal?: string | null, score?: number, confidence?: number): string {
  const s = (signal ?? '').toUpperCase()
  if (s.includes('SELL')) return 'AVOID'
  if (!s.includes('BUY')) return 'WATCH'
  const combined = (score ?? 0) * 0.6 + (confidence ?? 0) * 0.4
  return combined >= 75 ? 'STRONG BUY' : 'BUY'
}

function computeWhyNow(
  score: number, signal?: string | null, rsi?: number | null, macd?: string | null,
  momentum?: number | null, roe?: number | null, gm?: number | null,
  rg?: number | null, upside?: number | null
): string {
  const sig = signal ?? ''
  const r = rsi ?? 50
  if (score >= 80 && sig.includes('BUY')) return 'Elite fundamentals aligned with bullish technicals — rare high-conviction setup'
  if (r < 35 && score >= 60) return 'Technically oversold with strong fundamentals — asymmetric reversal opportunity'
  if (r < 45 && macd === 'BULLISH' && score >= 65) return 'Momentum turning bullish while still early in the move — ideal entry zone'
  if (momentum != null && momentum < 25 && score >= 70) return 'Near 52-week lows with premium fundamentals — deep value entry point'
  if (upside != null && upside > 20 && score >= 60) return `Analyst consensus implies ${upside.toFixed(0)}% upside — significant margin of safety`
  if (rg != null && rg > 25 && score >= 70) return `${rg.toFixed(0)}% revenue growth with high-quality fundamentals — growth at a reasonable price`
  if (sig.includes('STRONG BUY')) return 'Technical scoring at maximum bullish extreme — high-momentum entry'
  if (score >= 75 && sig.includes('HOLD')) return 'World-class business at fair value — accumulate on weakness'
  if (gm != null && gm > 60 && score >= 65) return `${gm.toFixed(0)}% gross margins signal structural pricing power — quality compounder`
  return 'Solid fundamentals with improving technical picture — monitor for entry'
}

function computeScoreDrivers(
  components: Record<string, number>,
  gm?: number | null, roe?: number | null, rg?: number | null, pe?: number | null,
  rsi?: number | null, macd?: string | null, trend?: string | null,
  momentum?: number | null, upside?: number | null
): string[] {
  const d: string[] = []
  const gmPts = components['Gross Margin'] ?? 0
  if (gmPts === 25 && gm) d.push(`Gross margin ${gm.toFixed(0)}% — elite pricing power`)
  else if (gmPts >= 15 && gm) d.push(`Gross margin ${gm.toFixed(0)}% — above-average profitability`)
  const roePts = components['ROE'] ?? 0
  if (roePts === 20 && roe) d.push(`ROE ${roe.toFixed(0)}% — exceptional capital efficiency`)
  else if (roePts >= 15 && roe) d.push(`ROE ${roe.toFixed(0)}% — strong returns on equity`)
  const valPts = components['Valuation'] ?? 0
  if (valPts === 20 && pe) d.push(`P/E ${pe.toFixed(1)}x — attractive valuation`)
  const grwPts = components['Growth'] ?? 0
  if (grwPts >= 10 && rg) d.push(`Revenue growth +${rg.toFixed(0)}% — expanding top line`)
  if (rsi != null && rsi < 30) d.push(`RSI ${rsi.toFixed(0)} — technically oversold`)
  else if (rsi != null && rsi < 40) d.push(`RSI ${rsi.toFixed(0)} — approaching oversold`)
  if (macd === 'BULLISH' && (trend === 'UPTREND' || trend === 'STRONG UPTREND')) d.push('MACD bullish + uptrend confirmed')
  else if (macd === 'BULLISH') d.push('MACD crossover bullish')
  if (momentum != null && momentum < 25) d.push(`${momentum.toFixed(0)}% of 52w range — deep value entry`)
  else if (momentum != null && momentum > 80) d.push(`${momentum.toFixed(0)}% of 52w range — breakout momentum`)
  if (upside != null && upside > 25) d.push(`Analyst consensus +${upside.toFixed(0)}% upside`)
  else if (upside != null && upside > 15) d.push(`Analyst target +${upside.toFixed(0)}% upside`)
  return d.slice(0, 3)
}

export default function AnalysisBrief({ data }: Props) {
  const sig = data.trading_signals
  const rat = data.analyst_rating
  const met = data.metrics
  const rsk = data.risk_profile
  const fct = data.forecast
  const sco = data.score

  const sm = signalMeta(sig?.signal)
  const currentPrice = met?.current_price

  const targetUpside = (rat?.target_mean && currentPrice)
    ? ((rat.target_mean - currentPrice) / currentPrice) * 100
    : null

  const momentum52 = (met?.fifty_two_week_high != null && met?.fifty_two_week_low != null &&
                      currentPrice != null && (met.fifty_two_week_high - met.fifty_two_week_low) > 0)
    ? Math.round((currentPrice - met.fifty_two_week_low) / (met.fifty_two_week_high - met.fifty_two_week_low) * 100)
    : null

  const tier = computeConvictionTier(sig?.signal, sco?.total, sig?.confidence)
  const whyNow = computeWhyNow(
    sco?.total ?? 0, sig?.signal, sig?.rsi_value, sig?.macd_signal,
    momentum52, met?.roe, met?.gross_margin, met?.revenue_growth, targetUpside
  )
  const drivers = computeScoreDrivers(
    sco?.components ?? {}, met?.gross_margin, met?.roe, met?.revenue_growth, met?.pe_ratio,
    sig?.rsi_value, sig?.macd_signal, sig?.trend_strength, momentum52, targetUpside
  )
  const recentNewsCount = (data.news ?? []).filter(n => {
    if (!n.published) return false
    const d = new Date(n.published)
    return !isNaN(d.getTime()) && (Date.now() - d.getTime()) < 7 * 86400 * 1000
  }).length
  const suggestedPosition = rsk?.volatility != null
    ? (rsk.volatility > 50 ? 1 : rsk.volatility > 35 ? 2 : rsk.volatility > 25 ? 3 : 5)
    : null

  return (
    <div className="rounded-xl overflow-hidden" style={{ border: '1px solid rgba(255,255,255,0.08)', backgroundColor: '#0f172a' }}>

      {/* ── Verdict bar ────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-4 px-4 py-3" style={{ backgroundColor: sm.bg, borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-widest" style={{ color: '#475569' }}>Signal</span>
          <span className="text-base font-bold tracking-wide" style={{ color: sm.color }}>{sm.label}</span>
        </div>
        {sig?.confidence != null && (
          <div className="flex items-center gap-1.5">
            <span className="text-xs" style={{ color: '#475569' }}>Confidence</span>
            <span className="text-sm font-bold" style={{ color: sm.color }}>{sig.confidence}%</span>
          </div>
        )}
        {sco && (
          <div className="flex items-center gap-1.5">
            <span className="text-xs" style={{ color: '#475569' }}>Score</span>
            <span className="text-sm font-bold" style={{ color: sco.total >= 70 ? '#00e676' : sco.total >= 45 ? '#ffab00' : '#ff1744' }}>
              {sco.total}/100
            </span>
          </div>
        )}
        <div className="flex items-center gap-1.5">
          <span className="text-xs" style={{ color: '#475569' }}>Tier</span>
          <span className="text-sm font-bold" style={{ color: convictionTierColor(tier) }}>{tier}</span>
        </div>
        {sig?.trend_strength && (
          <div className="flex items-center gap-1.5">
            <span className="text-xs" style={{ color: '#475569' }}>Trend</span>
            <span className="text-sm font-semibold" style={{ color: '#e2e8f0' }}>{sig.trend_strength}</span>
          </div>
        )}
        {fct && (
          <div className="flex items-center gap-1.5 ml-auto">
            <span className="text-xs" style={{ color: '#475569' }}>AI Forecast</span>
            <span className="text-sm font-bold" style={{ color: changeColor(fct.forecast_change_pct) }}>
              {fmt.price(fct.forecast_price)} ({fct.forecast_change_pct >= 0 ? '+' : ''}{fct.forecast_change_pct.toFixed(1)}%)
            </span>
          </div>
        )}
      </div>

      {/* ── Three-column body ───────────────────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x" style={{ '--tw-divide-opacity': 1, borderColor: 'rgba(255,255,255,0.06)' } as React.CSSProperties}>

        {/* Col 1 — Trade levels */}
        <div className="px-4 py-3">
          <p className="text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: '#475569' }}>Trade Setup</p>
          {sig?.optimal_entry != null
            ? <>
                <Row label="Entry"     value={fmt.price(sig.optimal_entry)}  color="#00d4ff" />
                <Row label="Stop Loss" value={fmt.price(sig.stop_loss)}       color="#ff1744" />
                <Row label="TP 1"      value={fmt.price(sig.tp1)}             color="#69f0ae" />
                <Row label="TP 2"      value={fmt.price(sig.tp2)}             color="#00e676" />
                <Row label="TP 3"      value={fmt.price(sig.tp3)}             color="#00c853" />
                {sig.risk_reward != null && (
                  <Row label="Risk / Reward" value={`${sig.risk_reward.toFixed(1)}:1`} color={sig.risk_reward >= 2 ? '#00e676' : '#ffab00'} />
                )}
              </>
            : <p className="text-xs" style={{ color: '#475569' }}>No active signal</p>
          }
        </div>

        {/* Col 2 — Analyst consensus */}
        <div className="px-4 py-3">
          <p className="text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: '#475569' }}>Analyst Consensus</p>
          {rat
            ? <>
                {rat.recommendation && (
                  <div className="mb-2">
                    <span className="text-sm font-bold capitalize" style={{ color: analystColor(rat.recommendation) }}>
                      {rat.recommendation}
                    </span>
                    {rat.count != null && (
                      <span className="ml-1.5 text-xs" style={{ color: '#475569' }}>({rat.count} analysts)</span>
                    )}
                  </div>
                )}
                {rat.mean != null && (
                  <Row label="Mean Score" value={`${rat.mean.toFixed(1)} / 5`} color="#e2e8f0" />
                )}
                {rat.target_mean != null && (
                  <Row
                    label="Target (mean)"
                    value={`${fmt.price(rat.target_mean)}${targetUpside != null ? ` (${targetUpside >= 0 ? '+' : ''}${targetUpside.toFixed(1)}%)` : ''}`}
                    color={targetUpside != null ? changeColor(targetUpside) : '#e2e8f0'}
                  />
                )}
                {rat.target_high != null && <Row label="Target High" value={fmt.price(rat.target_high)} color="#00e676" />}
                {rat.target_low != null  && <Row label="Target Low"  value={fmt.price(rat.target_low)}  color="#ff5252" />}
              </>
            : <p className="text-xs" style={{ color: '#475569' }}>No analyst data</p>
          }
        </div>

        {/* Col 3 — Key indicators */}
        <div className="px-4 py-3">
          <p className="text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: '#475569' }}>Key Indicators</p>
          {met?.pe_ratio != null && (
            <Row label="P/E Ratio"    value={fmt.ratio(met.pe_ratio)}
              color={met.pe_ratio < 25 ? '#00e676' : met.pe_ratio < 40 ? '#ffab00' : '#ff1744'} />
          )}
          {met?.roe != null && (
            <Row label="ROE"          value={fmt.pct(met.roe)}
              color={met.roe > 15 ? '#00e676' : met.roe > 0 ? '#ffab00' : '#ff1744'} />
          )}
          {met?.gross_margin != null && (
            <Row label="Gross Margin" value={fmt.pct(met.gross_margin)}
              color={met.gross_margin > 40 ? '#00e676' : met.gross_margin > 20 ? '#ffab00' : '#ff1744'} />
          )}
          {met?.beta != null && (
            <Row label="Beta"         value={fmt.ratio(met.beta)}
              color={met.beta < 1.2 ? '#00e676' : '#ffab00'} />
          )}
          {rsk?.sharpe_ratio != null && (
            <Row label="Sharpe"       value={rsk.sharpe_ratio.toFixed(2)}
              color={rsk.sharpe_ratio > 1 ? '#00e676' : rsk.sharpe_ratio > 0 ? '#ffab00' : '#ff1744'} />
          )}
          {rsk?.volatility != null && (
            <Row label="Volatility"   value={`${rsk.volatility.toFixed(1)}%`}
              color={rsk.volatility <= 20 ? '#00e676' : rsk.volatility <= 35 ? '#ffab00' : '#ff1744'} />
          )}
          {rsk?.max_drawdown_pct != null && (
            <Row label="Max Drawdown" value={`${rsk.max_drawdown_pct.toFixed(1)}%`}
              color={rsk.max_drawdown_pct <= 15 ? '#00e676' : rsk.max_drawdown_pct <= 30 ? '#ffab00' : '#ff1744'} />
          )}
        </div>
      </div>

      {/* ── Why now + score drivers ──────────────────────────────────────── */}
      <div className="px-4 py-3 flex flex-col gap-2.5" style={{ borderTop: '1px solid rgba(255,255,255,0.06)' }}>
        <div className="rounded-lg px-3 py-2 text-xs leading-relaxed"
          style={{ backgroundColor: '#0a0e1a', color: '#94a3b8', borderLeft: `2px solid ${sm.color}` }}>
          {whyNow}
        </div>
        {drivers.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {drivers.map((d, i) => (
              <span key={i} className="text-xs px-2 py-0.5 rounded-full"
                style={{ backgroundColor: '#00d4ff10', color: '#94a3b8', border: '1px solid rgba(0,212,255,0.12)' }}>
                {d}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* ── Qualification checks ─────────────────────────────────────────── */}
      <div className="px-4 py-3 flex flex-col gap-1.5" style={{ borderTop: '1px solid rgba(255,255,255,0.06)', backgroundColor: '#080d17' }}>
        <p className="text-xs font-semibold uppercase tracking-wide mb-0.5" style={{ color: '#334155' }}>Due Diligence</p>

        <div className="flex items-center justify-between text-xs">
          <span style={{ color: '#475569' }}>Recent news (7d)</span>
          {recentNewsCount > 0
            ? <span style={{ color: '#00e676' }}>✓ {recentNewsCount} article{recentNewsCount !== 1 ? 's' : ''} — check catalysts</span>
            : <span style={{ color: '#ffab00' }}>⚠ No recent news — verify catalyst manually</span>
          }
        </div>

        {data.analyst_target_age_days != null && (
          <div className="flex items-center justify-between text-xs">
            <span style={{ color: '#475569' }}>Analyst target age</span>
            {data.analyst_target_age_days > 90
              ? <span style={{ color: '#ff5252' }}>⚠ {data.analyst_target_age_days}d old — may be stale</span>
              : <span style={{ color: '#00e676' }}>✓ {data.analyst_target_age_days}d old — fresh</span>
            }
          </div>
        )}

        {suggestedPosition != null && (
          <div className="flex items-center justify-between text-xs">
            <span style={{ color: '#475569' }}>Max position size</span>
            <span style={{ color: '#94a3b8' }}>
              {suggestedPosition}% of portfolio
              {rsk?.volatility != null && <span style={{ color: '#334155' }}> (vol {rsk.volatility.toFixed(0)}%/yr)</span>}
            </span>
          </div>
        )}

        {momentum52 != null && (
          <div className="flex items-center justify-between text-xs">
            <span style={{ color: '#475569' }}>52-week position</span>
            <div className="flex items-center gap-2">
              <div className="w-20 bg-white/10 rounded-full h-1.5">
                <div className="h-1.5 rounded-full" style={{
                  width: `${momentum52}%`,
                  backgroundColor: momentum52 < 30 ? '#ff1744' : momentum52 > 70 ? '#00e676' : '#ffab00'
                }} />
              </div>
              <span style={{ color: momentum52 < 30 ? '#ff1744' : momentum52 > 70 ? '#00e676' : '#ffab00' }}>
                {momentum52}%
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
