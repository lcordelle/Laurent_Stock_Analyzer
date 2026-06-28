import {
  ComposedChart, Area, Line, XAxis, YAxis, Tooltip, ReferenceLine,
  ResponsiveContainer, CartesianGrid,
} from 'recharts'
import type { OHLCVRow, ValuationTunnel } from '../../lib/types'

interface Props {
  ohlcv: OHLCVRow[]
  tunnel: ValuationTunnel
  currentPrice?: number
}

interface Row {
  dateLabel: string
  dateISO: string
  price: number | null
  lower: number | null
  upper: number | null
  lowerBase: number | null
  band: number | null
  midHist: number | null
  midFc: number | null
}

function fmtLabel(iso: string) {
  return iso.length >= 10 ? iso.slice(5, 10) : iso
}

function fmtPrice(v: number) {
  return '$' + v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function buildRows(ohlcv: OHLCVRow[], tunnel: ValuationTunnel): { rows: Row[]; seamLabel: string } {
  const histLen = Math.min(tunnel.hist_mid.length, ohlcv.length)
  const offset = ohlcv.length - histLen

  const rows: Row[] = []

  for (let i = 0; i < histLen; i++) {
    const lo = tunnel.hist_lower[i]
    const hi = tunnel.hist_upper[i]
    const mid = tunnel.hist_mid[i]
    rows.push({
      dateLabel: fmtLabel(ohlcv[offset + i].date),
      dateISO: ohlcv[offset + i].date,
      price: ohlcv[offset + i].close,
      lower: lo,
      upper: hi,
      lowerBase: lo,
      band: lo != null && hi != null ? hi - lo : null,
      midHist: mid,
      midFc: i === histLen - 1 ? (mid ?? null) : null,
    })
  }

  for (let j = 0; j < tunnel.future_dates.length; j++) {
    rows.push({
      dateLabel: fmtLabel(tunnel.future_dates[j]),
      dateISO: tunnel.future_dates[j],
      price: null,
      lower: tunnel.fc_lower[j],
      upper: tunnel.fc_upper[j],
      lowerBase: tunnel.fc_lower[j],
      band: tunnel.fc_upper[j] - tunnel.fc_lower[j],
      midHist: null,
      midFc: tunnel.fc_mid[j],
    })
  }

  const seamLabel = tunnel.future_dates.length > 0 ? fmtLabel(tunnel.future_dates[0]) : ''
  return { rows, seamLabel }
}

function lastNonNull(arr: (number | null)[]): number | null {
  for (let i = arr.length - 1; i >= 0; i--) {
    if (arr[i] != null) return arr[i]
  }
  return null
}

interface TooltipPayloadEntry {
  dataKey: string
  value: number | null | undefined
  name?: string
}

interface CustomTooltipProps {
  active?: boolean
  payload?: TooltipPayloadEntry[]
  label?: string
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload || !payload.length) return null
  const get = (key: string) => payload.find(p => p.dataKey === key)?.value

  const price   = get('price')
  const midHist = get('midHist')
  const midFc   = get('midFc')
  const lower   = get('lower')
  const upper   = get('upper')

  return (
    <div className="rounded-xl border px-3 py-2 text-xs flex flex-col gap-1"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.12)', color: '#94a3b8', minWidth: 160 }}>
      <div className="font-semibold mb-0.5" style={{ color: '#e2e8f0' }}>{label}</div>
      {price     != null && <div>Price: <span style={{ color: '#e2e8f0', fontWeight: 700 }}>{fmtPrice(price)}</span></div>}
      {midHist   != null && <div>Fair value: <span style={{ color: '#3b82f6', fontWeight: 700 }}>{fmtPrice(midHist)}</span></div>}
      {midFc     != null && price == null && <div>Forecast: <span style={{ color: '#3b82f6', fontWeight: 700 }}>{fmtPrice(midFc)}</span></div>}
      {lower     != null && upper != null && (
        <div>Band: <span style={{ color: '#64748b' }}>{fmtPrice(lower)} – {fmtPrice(upper)}</span></div>
      )}
    </div>
  )
}

export default function ValuationTunnelChart({ ohlcv, tunnel, currentPrice }: Props) {
  const histLen = Math.min(tunnel.hist_mid.length, ohlcv.length)
  if (histLen < 2) {
    return (
      <p className="text-xs py-4 text-center" style={{ color: '#475569' }}>
        Valuation tunnel unavailable for this period
      </p>
    )
  }

  const { rows, seamLabel } = buildRows(ohlcv, tunnel)

  // Tighten the y-axis to the band/price range — the stacked-area baseline
  // otherwise drags the domain down to 0 and compresses the tunnel.
  const yVals = rows.flatMap(r =>
    [r.lower, r.upper, r.price, r.midHist, r.midFc].filter((v): v is number => v != null))
  const yMin = yVals.length ? Math.min(...yVals) : 0
  const yMax = yVals.length ? Math.max(...yVals) : 1
  const yPad = (yMax - yMin) * 0.08 || 1
  const yDomain: [number, number] = [Math.max(0, yMin - yPad), yMax + yPad]

  const price = currentPrice ?? ohlcv.at(-1)?.close ?? null
  const lastMid = lastNonNull(tunnel.hist_mid)
  const fcEnd = tunnel.fc_mid.at(-1) ?? null
  const fcLo  = tunnel.fc_lower.at(-1) ?? null
  const fcHi  = tunnel.fc_upper.at(-1) ?? null

  const vssFairValue = price != null && lastMid != null
    ? (price / lastMid - 1) * 100
    : null

  const vsForecast = price != null && fcEnd != null && price > 0
    ? (fcEnd / price - 1) * 100
    : null

  const labelColor = (v: number) => v >= 0 ? '#00e676' : '#ff1744'
  const aboveBelow = (v: number) => v >= 0 ? 'above' : 'below'

  return (
    <div className="flex flex-col gap-4">
      {/* Readout strip */}
      <div className="flex gap-3 flex-wrap">
        {vssFairValue != null && (
          <div className="flex flex-col px-4 py-2.5 rounded-xl"
            style={{ backgroundColor: '#0a0e1a', border: '1px solid rgba(255,255,255,0.06)', minWidth: 140 }}>
            <span className="text-xs font-semibold uppercase tracking-wide mb-1" style={{ color: '#475569' }}>
              vs Fair Value
            </span>
            <span className="text-sm font-black tabular-nums" style={{ color: labelColor(vssFairValue) }}>
              {(vssFairValue >= 0 ? '+' : '') + vssFairValue.toFixed(1)}% {aboveBelow(vssFairValue)} fair value
            </span>
          </div>
        )}

        {fcEnd != null && vsForecast != null && (
          <div className="flex flex-col px-4 py-2.5 rounded-xl"
            style={{ backgroundColor: '#0a0e1a', border: '1px solid rgba(255,255,255,0.06)', minWidth: 140 }}>
            <span className="text-xs font-semibold uppercase tracking-wide mb-1" style={{ color: '#475569' }}>
              {tunnel.horizon_days}d Forecast
            </span>
            <span className="text-sm font-black tabular-nums" style={{ color: labelColor(vsForecast) }}>
              {fmtPrice(fcEnd)} ({vsForecast >= 0 ? '+' : ''}{vsForecast.toFixed(1)}%)
            </span>
          </div>
        )}

        {fcLo != null && fcHi != null && (
          <div className="flex flex-col px-4 py-2.5 rounded-xl"
            style={{ backgroundColor: '#0a0e1a', border: '1px solid rgba(255,255,255,0.06)', minWidth: 140 }}>
            <span className="text-xs font-semibold uppercase tracking-wide mb-1" style={{ color: '#475569' }}>
              Forecast Range
            </span>
            <span className="text-sm font-black tabular-nums" style={{ color: '#64748b' }}>
              {fmtPrice(fcLo)} – {fmtPrice(fcHi)}
            </span>
          </div>
        )}
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={380}>
        <ComposedChart data={rows} margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1a2235" vertical={false} />
          <XAxis
            dataKey="dateLabel"
            tick={{ fontSize: 11, fill: '#475569' }}
            tickLine={false}
            axisLine={{ stroke: '#1a2235' }}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={yDomain}
            allowDataOverflow
            tickFormatter={fmtPrice}
            tick={{ fontSize: 11, fill: '#475569' }}
            tickLine={false}
            axisLine={false}
            width={72}
          />
          <Tooltip content={<CustomTooltip />} />

          {/* Band fill: stacked areas */}
          <Area
            dataKey="lowerBase"
            stackId="band"
            stroke="none"
            fill="transparent"
            isAnimationActive={false}
            legendType="none"
          />
          <Area
            dataKey="band"
            stackId="band"
            stroke="none"
            fill="#3b82f6"
            fillOpacity={0.15}
            isAnimationActive={false}
            legendType="none"
          />

          {/* Band edges */}
          <Line dataKey="upper" stroke="#3b82f6" strokeOpacity={0.4} strokeWidth={1} dot={false} isAnimationActive={false} legendType="none" connectNulls={false} />
          <Line dataKey="lower" stroke="#3b82f6" strokeOpacity={0.4} strokeWidth={1} dot={false} isAnimationActive={false} legendType="none" connectNulls={false} />

          {/* Fair value — history */}
          <Line dataKey="midHist" stroke="#3b82f6" strokeWidth={2} dot={false} isAnimationActive={false} name="Fair value" connectNulls={false} />

          {/* Forecast center — dashed */}
          <Line dataKey="midFc" stroke="#3b82f6" strokeWidth={2} strokeDasharray="5 4" dot={false} isAnimationActive={false} name="Forecast" connectNulls={false} />

          {/* Price (on top) */}
          <Line dataKey="price" stroke="#e2e8f0" strokeWidth={1.5} dot={false} isAnimationActive={false} name="Price" connectNulls={false} />

          {/* Today divider */}
          {seamLabel && (
            <ReferenceLine
              x={seamLabel}
              stroke="#64748b"
              strokeDasharray="3 3"
              label={{ value: 'Today', position: 'top', fill: '#94a3b8', fontSize: 11 }}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
