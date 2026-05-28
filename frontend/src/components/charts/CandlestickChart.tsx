import { useEffect, useRef, useMemo, useState } from 'react'
import {
  ResponsiveContainer, ComposedChart, Line, Bar,
  XAxis, YAxis, Tooltip, ReferenceLine, Cell
} from 'recharts'
import type { OHLCVRow, IndicatorData, FullStockAnalysis, EarningsDate } from '../../lib/types'

interface PatternMarker {
  date: string
  pattern: string
  direction: string
  confidence: number
}

interface Props {
  ohlcv: OHLCVRow[]
  indicators?: IndicatorData
  tradingSignals?: FullStockAnalysis['trading_signals']
  earningsDates?: EarningsDate[]
  relativeStrength?: (number | null)[]
  patterns?: PatternMarker[]
  period: string
  onPeriodChange: (p: string) => void
}

const PATTERN_INFO: Record<string, { meaning: string; action: string }> = {
  'Hammer':            { meaning: 'Buyers rejected a sharp selloff — the long lower wick shows sellers tried and failed to hold price down.', action: 'Watch for bullish follow-through above the candle high. Volume on the next candle confirms strength.' },
  'Shooting Star':     { meaning: 'Sellers rejected a rally — the long upper wick shows bulls lost control near the session high.', action: 'Reduce long exposure or wait for bearish confirmation on the next candle before shorting.' },
  'Doji':              { meaning: 'Opening and closing price are nearly equal — the market is indecisive and a reversal or pause is possible.', action: 'Do not act alone on a Doji. Wait for the next candle to confirm direction.' },
  'Bullish Engulfing': { meaning: 'The current green candle fully engulfs the prior red candle — a decisive shift from sellers to buyers.', action: 'High-probability long setup. Consider entry at the close of the engulfing candle with a stop below its low.' },
  'Bearish Engulfing': { meaning: 'The current red candle fully engulfs the prior green candle — sellers took decisive control from buyers.', action: 'Consider reducing longs or entering short. Confirm with volume and a test of key support.' },
  'Morning Star':      { meaning: '3-candle bullish reversal: large down candle, small indecision body, then a strong up candle closing into the first candle. Classic bottom signal.', action: 'Strong long entry signal after a downtrend. Volume spike on the third candle is the key confirmation.' },
  'Evening Star':      { meaning: '3-candle bearish reversal: large up candle, small indecision body, then a strong down candle. Classic top signal.', action: 'Consider taking profits on longs or entering short. Best used at resistance levels after an extended uptrend.' },
}

const PERIODS = [
  { label: '1M', value: '1mo' },
  { label: '3M', value: '3mo' },
  { label: '6M', value: '6mo' },
  { label: '1Y', value: '1y' },
  { label: '2Y', value: '2y' },
  { label: '5Y', value: '5y' },
]

interface SignalMarker {
  time: string
  position: 'aboveBar' | 'belowBar'
  color: string
  shape: 'arrowDown' | 'arrowUp'
  text: string
  reasons: string[]
}

interface TooltipData {
  x: number; y: number
  signal: 'BUY' | 'SELL'
  reasons: string[]
  date: string
  price: number
}

interface PatternTooltipData {
  x: number; y: number
  name: string
  direction: string
  meaning: string
  action: string
  confidence: number
  date: string
  price: number
}

// RSI crossings + multi-indicator correlation reasons
function computeMarkers(ohlcv: OHLCVRow[], ind: IndicatorData): SignalMarker[] {
  const { rsi, macd, macd_signal: macdSig, sma_50, sma_200, bb_upper, bb_lower } = ind
  if (!rsi) return []
  const out: SignalMarker[] = []

  for (let i = 1; i < rsi.length; i++) {
    const prev = rsi[i - 1]; const curr = rsi[i]
    if (prev == null || curr == null || !ohlcv[i]) continue
    const time = ohlcv[i].date.slice(0, 10)
    const price = ohlcv[i].close
    const reasons: string[] = []

    if (prev <= 30 && curr > 30) {
      reasons.push(`RSI ${curr.toFixed(1)} exits oversold zone`)
      if (macd?.[i] != null && macdSig?.[i] != null) {
        const h = macd[i]! - macdSig[i]!
        const ph = i > 0 && macd[i - 1] != null && macdSig[i - 1] != null ? macd[i - 1]! - macdSig[i - 1]! : null
        if (ph != null && ph <= 0 && h > 0) reasons.push('MACD bullish crossover')
        else if (h > 0) reasons.push('MACD above signal line')
      }
      if (sma_50?.[i] && price > sma_50[i]!) reasons.push('Price reclaiming SMA50')
      if (sma_200?.[i] && price > sma_200[i]!) reasons.push('Above SMA200 — uptrend intact')
      if (bb_lower?.[i] && price <= bb_lower[i]! * 1.02) reasons.push('Near lower Bollinger Band')
      out.push({ time, position: 'belowBar', color: '#00e676', shape: 'arrowUp', text: 'B', reasons })
    } else if (prev >= 70 && curr < 70) {
      reasons.push(`RSI ${curr.toFixed(1)} exits overbought zone`)
      if (macd?.[i] != null && macdSig?.[i] != null) {
        const h = macd[i]! - macdSig[i]!
        const ph = i > 0 && macd[i - 1] != null && macdSig[i - 1] != null ? macd[i - 1]! - macdSig[i - 1]! : null
        if (ph != null && ph >= 0 && h < 0) reasons.push('MACD bearish crossover')
        else if (h < 0) reasons.push('MACD below signal line')
      }
      if (sma_50?.[i] && price < sma_50[i]!) reasons.push('Price losing SMA50 support')
      if (sma_200?.[i] && price < sma_200[i]!) reasons.push('Below SMA200 — downtrend risk')
      if (bb_upper?.[i] && price >= bb_upper[i]! * 0.98) reasons.push('Near upper Bollinger Band')
      out.push({ time, position: 'aboveBar', color: '#ff1744', shape: 'arrowDown', text: 'S', reasons })
    }
  }
  // RSI divergence pass (15-bar lookback)
  const WINDOW = 15; const MIN_PRICE_DIFF = 0.015; const MIN_RSI_DIFF = 4
  for (let i = WINDOW; i < rsi.length; i++) {
    const curr = rsi[i]; const price = ohlcv[i]?.close
    if (curr == null || !ohlcv[i]) continue
    const wPrices = ohlcv.slice(i - WINDOW, i).map(r => r.close)
    const wRsi = rsi.slice(i - WINDOW, i) as (number | null)[]

    const prevHigh = Math.max(...wPrices)
    const prevHighRsi = wRsi[wPrices.indexOf(prevHigh)]
    if (price > prevHigh * (1 + MIN_PRICE_DIFF) && prevHighRsi != null && curr < prevHighRsi - MIN_RSI_DIFF) {
      out.push({ time: ohlcv[i].date.slice(0, 10), position: 'aboveBar', color: '#ff9800', shape: 'circle', text: '↓', reasons: ['Bearish RSI divergence: price higher high, RSI lower high'] })
      i += Math.floor(WINDOW / 2)
      continue
    }

    const prevLow = Math.min(...wPrices)
    const prevLowRsi = wRsi[wPrices.indexOf(prevLow)]
    if (price < prevLow * (1 - MIN_PRICE_DIFF) && prevLowRsi != null && curr > prevLowRsi + MIN_RSI_DIFF) {
      out.push({ time: ohlcv[i].date.slice(0, 10), position: 'belowBar', color: '#ff9800', shape: 'circle', text: '↑', reasons: ['Bullish RSI divergence: price lower low, RSI higher low'] })
      i += Math.floor(WINDOW / 2)
      continue
    }
  }

  return out
}

export default function CandlestickChart({ ohlcv, indicators, tradingSignals, earningsDates, relativeStrength, patterns, period, onPeriodChange }: Props) {
  const mainRef = useRef<HTMLDivElement>(null)
  const volRef = useRef<HTMLDivElement>(null)
  const mainChartRef = useRef<import('lightweight-charts').IChartApi | null>(null)
  const volChartRef = useRef<import('lightweight-charts').IChartApi | null>(null)
  const markersMapRef = useRef<Map<string, SignalMarker>>(new Map())
  const patternsMapRef = useRef<Map<string, PatternMarker>>(new Map())
  const [tooltip, setTooltip] = useState<TooltipData | null>(null)
  const [patternTooltip, setPatternTooltip] = useState<PatternTooltipData | null>(null)
  const [showRS, setShowRS] = useState(false)
  const [earningsLines, setEarningsLines] = useState<{ x: number; color: string; beat: boolean | null | undefined; date: string }[]>([])

  // Build Recharts data for RSI / MACD panels
  const subData = useMemo(() => {
    if (!indicators) return []
    return ohlcv.map((bar, i) => {
      const macdVal = indicators.macd?.[i] ?? null
      const macdSig = indicators.macd_signal?.[i] ?? null
      return {
        date: bar.date.slice(5, 10), // MM-DD for label
        rsi: indicators.rsi?.[i] ?? null,
        macd: macdVal,
        signal: macdSig,
        hist: macdVal != null && macdSig != null ? +(macdVal - macdSig).toFixed(4) : null,
      }
    }).filter(d => d.rsi != null || d.macd != null)
  }, [ohlcv, indicators])

  // Visible label decimation for Recharts x-axis
  const xTick = useMemo(() => {
    if (subData.length === 0) return []
    const step = Math.max(1, Math.floor(subData.length / 8))
    return subData.filter((_, i) => i % step === 0).map(d => d.date)
  }, [subData])

  useEffect(() => {
    if (!mainRef.current || !volRef.current || ohlcv.length === 0) return

    let syncing = false
    let mounted = true
    let resizeHandler: (() => void) | null = null

    // Cleanup any previously mounted charts before async creates new ones
    mainChartRef.current?.remove()
    volChartRef.current?.remove()
    mainChartRef.current = null
    volChartRef.current = null

    import('lightweight-charts').then(({ createChart, ColorType, LineStyle }) => {
      if (!mounted || !mainRef.current || !volRef.current) return

      const chartOpts = (height: number) => ({
        width: mainRef.current!.clientWidth,
        height,
        layout: { background: { type: ColorType.Solid, color: '#111827' }, textColor: '#94a3b8' },
        grid: { vertLines: { color: '#1a2235' }, horzLines: { color: '#1a2235' } },
        crosshair: { vertLine: { color: '#00d4ff40', style: LineStyle.Dashed }, horzLine: { color: '#00d4ff40', style: LineStyle.Dashed } },
        rightPriceScale: { borderColor: '#1a2235', scaleMargins: { top: 0.08, bottom: 0.05 } },
        timeScale: { borderColor: '#1a2235', timeVisible: true },
      })

      // ── Main chart ──────────────────────────────────────────────────
      const mainChart = createChart(mainRef.current, chartOpts(380))
      mainChartRef.current = mainChart

      const candleSeries = mainChart.addCandlestickSeries({
        upColor: '#00e676', downColor: '#ff1744',
        borderUpColor: '#00e676', borderDownColor: '#ff1744',
        wickUpColor: '#00e676', wickDownColor: '#ff1744',
      })

      const candles = ohlcv
        .filter(r => r.date)
        .map(r => ({
          time: r.date.slice(0, 10) as import('lightweight-charts').Time,
          open: r.open, high: r.high, low: r.low, close: r.close,
        }))
        .sort((a, b) => (a.time < b.time ? -1 : 1))

      candleSeries.setData(candles)

      // Horizontal price lines for trade setup levels
      if (tradingSignals) {
        const pls = [
          { price: tradingSignals.stop_loss, color: '#ff174490', title: 'SL', style: LineStyle.Dashed },
          { price: tradingSignals.optimal_entry, color: '#00d4ffcc', title: 'Entry', style: LineStyle.Solid },
          { price: tradingSignals.tp1, color: '#00e67655', title: 'TP1', style: LineStyle.Dashed },
          { price: tradingSignals.tp2, color: '#00e67655', title: 'TP2', style: LineStyle.Dashed },
          { price: tradingSignals.tp3, color: '#00e67655', title: 'TP3', style: LineStyle.Dashed },
        ]
        for (const { price, color, title, style } of pls) {
          if (price != null) {
            candleSeries.createPriceLine({ price, color, lineWidth: 1, lineStyle: style, axisLabelVisible: true, title })
          }
        }
      }

      // RSI-based buy/sell markers with multi-indicator correlation
      const lwMarkers: Array<{
        time: import('lightweight-charts').Time
        position: 'aboveBar' | 'belowBar'
        color: string
        shape: 'arrowDown' | 'arrowUp' | 'circle'
        text: string
      }> = []

      if (indicators) {
        const signalMarkers = computeMarkers(ohlcv, indicators)
        markersMapRef.current = new Map(signalMarkers.map(m => [m.time, m]))

        for (const { time, position, color, shape, text } of signalMarkers) {
          lwMarkers.push({ time: time as import('lightweight-charts').Time, position, color, shape, text })
        }

        // Append current backend signal on latest candle
        const last = candles[candles.length - 1]
        if (tradingSignals?.signal?.includes('BUY')) {
          lwMarkers.push({ time: last.time, position: 'belowBar', color: '#00e676', shape: 'arrowUp', text: '★' })
        } else if (tradingSignals?.signal?.includes('SELL')) {
          lwMarkers.push({ time: last.time, position: 'aboveBar', color: '#ff1744', shape: 'arrowDown', text: '★' })
        }

        // Crosshair tooltip — shows correlation when hovering a signal candle
        mainChart.subscribeCrosshairMove(param => {
          if (!param.time || !param.point) { setTooltip(null); return }
          const timeStr = typeof param.time === 'object'
            ? `${(param.time as { year: number; month: number; day: number }).year}-${String((param.time as { year: number; month: number; day: number }).month).padStart(2, '0')}-${String((param.time as { year: number; month: number; day: number }).day).padStart(2, '0')}`
            : String(param.time)
          const marker = markersMapRef.current.get(timeStr)
          if (!marker) { setTooltip(null); return }
          const bar = ohlcv.find(r => r.date.slice(0, 10) === timeStr)
          setTooltip({
            x: param.point.x, y: param.point.y,
            signal: marker.shape === 'arrowUp' ? 'BUY' : 'SELL',
            reasons: marker.reasons,
            date: timeStr,
            price: bar?.close ?? 0,
          })
        })
      }

      // Earnings markers — amber/green/red "E" circles
      if (earningsDates && earningsDates.length > 0) {
        const earningsMarkers = earningsDates
          .map(e => ({
            time: e.date.slice(0, 10) as import('lightweight-charts').Time,
            position: 'aboveBar' as const,
            color: e.beat === true ? '#00e676' : e.beat === false ? '#ff1744' : '#ffab00',
            shape: 'circle' as const,
            text: 'E',
          }))
          .filter(m => candles.some(c => c.time === m.time))
        lwMarkers.push(...earningsMarkers)
      }

      // Candlestick pattern markers — overlaid directly on the chart
      patternsMapRef.current = new Map()
      if (patterns && patterns.length > 0) {
        const abbr: Record<string, string> = {
          'Hammer': 'H', 'Shooting Star': 'SS', 'Doji': 'D',
          'Bullish Engulfing': 'BE', 'Bearish Engulfing': 'SE',
          'Morning Star': 'MS', 'Evening Star': 'ES',
        }
        for (const p of patterns) {
          const t = p.date.slice(0, 10) as import('lightweight-charts').Time
          if (!candles.some(c => c.time === t)) continue
          patternsMapRef.current.set(p.date.slice(0, 10), p)
          lwMarkers.push({
            time: t,
            position: p.direction === 'bearish' ? 'aboveBar' : 'belowBar',
            color: p.direction === 'bullish' ? '#00e676' : p.direction === 'bearish' ? '#ff1744' : '#ffab00',
            shape: p.direction === 'bullish' ? 'arrowUp' : p.direction === 'bearish' ? 'arrowDown' : 'circle',
            text: abbr[p.pattern] ?? p.pattern.slice(0, 2),
          })
        }

        mainChart.subscribeCrosshairMove(param => {
          if (!param.time || !param.point) { setPatternTooltip(null); return }
          const timeStr = typeof param.time === 'object'
            ? `${(param.time as { year: number; month: number; day: number }).year}-${String((param.time as { year: number; month: number; day: number }).month).padStart(2, '0')}-${String((param.time as { year: number; month: number; day: number }).day).padStart(2, '0')}`
            : String(param.time)
          const p = patternsMapRef.current.get(timeStr)
          if (!p) { setPatternTooltip(null); return }
          const bar = ohlcv.find(r => r.date.slice(0, 10) === timeStr)
          const info = PATTERN_INFO[p.pattern]
          setPatternTooltip({
            x: param.point.x, y: param.point.y,
            name: p.pattern,
            direction: p.direction,
            meaning: info?.meaning ?? `${p.pattern} pattern detected.`,
            action: info?.action ?? 'Review chart context before acting.',
            confidence: p.confidence,
            date: timeStr,
            price: bar?.close ?? 0,
          })
        })
      }

      if (lwMarkers.length > 0) {
        const sorted = [...lwMarkers].sort((a, b) => (a.time < b.time ? -1 : 1))
        candleSeries.setMarkers(sorted as Parameters<typeof candleSeries.setMarkers>[0])
      }

      // Bollinger Bands
      if (indicators?.bb_upper && indicators?.bb_lower) {
        const bbUpper = mainChart.addLineSeries({ color: '#47556930', lineWidth: 1, title: 'BB Upper', lastValueVisible: false, priceLineVisible: false })
        const bbLower = mainChart.addLineSeries({ color: '#47556930', lineWidth: 1, title: 'BB Lower', lastValueVisible: false, priceLineVisible: false })
        const toLine = (arr: (number | null)[]) =>
          ohlcv.map((r, i) => ({ time: r.date.slice(0, 10) as import('lightweight-charts').Time, value: arr[i] }))
            .filter((d): d is { time: import('lightweight-charts').Time; value: number } => d.value != null)
            .sort((a, b) => a.time < b.time ? -1 : 1)
        bbUpper.setData(toLine(indicators.bb_upper))
        bbLower.setData(toLine(indicators.bb_lower))
      }

      // SMA + VWAP overlays
      const smaConfig = [
        { key: 'sma_20' as const, color: '#ffab00', title: 'SMA20', width: 1 },
        { key: 'sma_50' as const, color: '#00d4ff', title: 'SMA50', width: 1 },
        { key: 'sma_200' as const, color: '#a78bfa', title: 'SMA200', width: 1 },
        { key: 'vwap' as const, color: '#f472b6', title: 'VWAP', width: 1 },
      ]
      for (const { key, color, title, width } of smaConfig) {
        const arr = indicators?.[key]
        if (!arr) continue
        const series = mainChart.addLineSeries({ color, lineWidth: width as 1, title, lastValueVisible: false, priceLineVisible: false })
        series.setData(
          ohlcv.map((r, i) => ({ time: r.date.slice(0, 10) as import('lightweight-charts').Time, value: arr[i] }))
            .filter((d): d is { time: import('lightweight-charts').Time; value: number } => d.value != null)
            .sort((a, b) => a.time < b.time ? -1 : 1)
        )
      }

      // Relative Strength vs SPY overlay
      if (showRS && relativeStrength && relativeStrength.length > 0) {
        const rsData = ohlcv
          .map((r, i) => ({
            time: r.date.slice(0, 10) as import('lightweight-charts').Time,
            value: relativeStrength[i],
          }))
          .filter((d): d is { time: import('lightweight-charts').Time; value: number } => d.value != null)
          .sort((a, b) => (a.time < b.time ? -1 : 1))

        if (rsData.length > 0) {
          const rsSeries = mainChart.addLineSeries({
            color: '#94a3b840',
            lineWidth: 1,
            title: 'RS/SPY',
            lastValueVisible: false,
            priceLineVisible: false,
            priceScaleId: 'rs-overlay',
          })
          mainChart.priceScale('rs-overlay').applyOptions({
            scaleMargins: { top: 0.7, bottom: 0 },
          })
          rsSeries.setData(rsData)
        }
      }

      // ── Volume chart ────────────────────────────────────────────────
      const volChart = createChart(volRef.current, {
        ...chartOpts(100),
        rightPriceScale: { borderColor: '#1a2235', scaleMargins: { top: 0.1, bottom: 0 } },
        timeScale: { borderColor: '#1a2235', timeVisible: true, visible: true },
      })
      volChartRef.current = volChart

      const volSeries = volChart.addHistogramSeries({
        color: '#00d4ff30',
        priceFormat: { type: 'volume' },
        priceScaleId: 'right',
      })

      volSeries.setData(
        ohlcv
          .filter(r => r.date && r.volume != null)
          .map(r => ({
            time: r.date.slice(0, 10) as import('lightweight-charts').Time,
            value: r.volume,
            color: r.close >= r.open ? '#00e67640' : '#ff174440',
          }))
          .sort((a, b) => (a.time < b.time ? -1 : 1))
      )

      // 20-bar volume MA overlay
      const volSorted = ohlcv.filter(r => r.date && r.volume != null).sort((a, b) => a.date < b.date ? -1 : 1)
      if (volSorted.length >= 20) {
        const volMaSeries = volChart.addLineSeries({
          color: '#ffab0080', lineWidth: 1, title: 'Vol MA20',
          lastValueVisible: false, priceLineVisible: false,
        })
        const volMaData = volSorted.map((r, i, arr) => {
          if (i < 19) return null
          const sum = arr.slice(i - 19, i + 1).reduce((acc, b) => acc + b.volume, 0)
          return { time: r.date.slice(0, 10) as import('lightweight-charts').Time, value: sum / 20 }
        }).filter((d): d is { time: import('lightweight-charts').Time; value: number } => d !== null)
        volMaSeries.setData(volMaData)
      }

      // OBV overlay on secondary scale
      if (indicators?.obv && indicators.obv.length > 0) {
        const obvSeries = volChart.addLineSeries({
          color: '#00d4ff60', lineWidth: 1, title: 'OBV',
          lastValueVisible: false, priceLineVisible: false, priceScaleId: 'obv',
        })
        volChart.priceScale('obv').applyOptions({ scaleMargins: { top: 0.5, bottom: 0 } })
        obvSeries.setData(
          ohlcv.map((r, i) => ({ time: r.date.slice(0, 10) as import('lightweight-charts').Time, value: indicators.obv![i] }))
            .filter((d): d is { time: import('lightweight-charts').Time; value: number } => d.value != null)
            .sort((a, b) => a.time < b.time ? -1 : 1)
        )
      }

      // Sync scroll/zoom between main and volume
      mainChart.timeScale().subscribeVisibleLogicalRangeChange(range => {
        if (syncing || !range) return
        syncing = true
        volChart?.timeScale().setVisibleLogicalRange(range)
        syncing = false
      })
      volChart.timeScale().subscribeVisibleLogicalRangeChange(range => {
        if (syncing || !range) return
        syncing = true
        mainChart?.timeScale().setVisibleLogicalRange(range)
        syncing = false
      })

      mainChart.timeScale().fitContent()

      // Compute pixel-X positions for earnings vertical lines; recompute on scroll/zoom
      const earningsDatesFiltered = (earningsDates ?? [])
        .filter(e => candles.some(c => c.time === e.date.slice(0, 10)))

      const updateEarningsLines = () => {
        if (!earningsDatesFiltered.length) { setEarningsLines([]); return }
        const lines = earningsDatesFiltered
          .map(e => {
            const x = mainChart.timeScale().timeToCoordinate(e.date.slice(0, 10) as import('lightweight-charts').Time)
            if (x === null) return null
            const color = e.beat === true ? '#00e676' : e.beat === false ? '#ff1744' : '#ffab00'
            return { x, color, beat: e.beat, date: e.date.slice(0, 10) }
          })
          .filter((l): l is { x: number; color: string; beat: boolean | null | undefined; date: string } => l !== null)
        setEarningsLines(lines)
      }

      if (earningsDatesFiltered.length > 0) {
        mainChart.timeScale().subscribeVisibleLogicalRangeChange(updateEarningsLines)
        updateEarningsLines()
      }

      resizeHandler = () => {
        const w = mainRef.current?.clientWidth ?? 600
        mainChart.applyOptions({ width: w })
        volChart.applyOptions({ width: w })
      }
      window.addEventListener('resize', resizeHandler)
    })

    return () => {
      mounted = false
      setEarningsLines([])
      if (resizeHandler) window.removeEventListener('resize', resizeHandler)
      mainChartRef.current?.remove()
      volChartRef.current?.remove()
      mainChartRef.current = null
      volChartRef.current = null
    }
  }, [ohlcv, indicators, tradingSignals, earningsDates, relativeStrength, patterns, showRS])

  const rsiLast = useMemo(() => {
    if (!indicators?.rsi) return null
    for (let i = indicators.rsi.length - 1; i >= 0; i--) {
      if (indicators.rsi[i] != null) return indicators.rsi[i]
    }
    return null
  }, [indicators])

  const rsiColor = rsiLast == null ? '#94a3b8' : rsiLast < 30 ? '#00e676' : rsiLast > 70 ? '#ff1744' : '#ffab00'

  return (
    <div
      className="rounded-xl border overflow-hidden"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
      data-testid="candlestick-chart"
    >
      {/* Header */}
      <div className="px-4 py-3 border-b flex flex-wrap items-center justify-between gap-3" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
        <div className="flex items-center gap-4 flex-wrap">
          <span className="text-sm font-semibold" style={{ color: '#94a3b8' }}>Price Chart</span>
          {indicators?.sma_20 && <LegendDot color="#ffab00" label="SMA20" />}
          {indicators?.sma_50 && <LegendDot color="#00d4ff" label="SMA50" />}
          {indicators?.sma_200 && <LegendDot color="#a78bfa" label="SMA200" />}
          {indicators?.bb_upper && <LegendDot color="#475569" label="BB" />}
          {earningsDates && earningsDates.length > 0 && <LegendDot color="#ffab00" label="Earnings" dot />}
          {tradingSignals?.signal && (() => {
            const sc = tradingSignals.signal.includes('BUY') ? '#00e676' : tradingSignals.signal.includes('SELL') ? '#ff1744' : '#ffab00'
            const arrow = tradingSignals.signal.includes('BUY') ? '▲' : tradingSignals.signal.includes('SELL') ? '▼' : '●'
            return (
              <div className="flex items-center gap-2">
                <span className="text-xs font-black px-3 py-1 rounded-lg border" style={{ color: sc, backgroundColor: `${sc}18`, borderColor: `${sc}50` }}>
                  {arrow} {tradingSignals.signal}
                </span>
                {tradingSignals.confidence != null && (
                  <span className="text-xs font-bold" style={{ color: sc }}>{tradingSignals.confidence}%</span>
                )}
              </div>
            )
          })()}
        </div>

        {/* Period selector + RS toggle */}
        <div className="flex items-center gap-1">
          {PERIODS.map(p => (
            <button
              key={p.value}
              onClick={() => onPeriodChange(p.value)}
              className="px-2.5 py-1 rounded text-xs font-semibold transition-colors"
              style={{
                backgroundColor: period === p.value ? '#00d4ff' : 'transparent',
                color: period === p.value ? '#0a0e1a' : '#475569',
              }}
            >
              {p.label}
            </button>
          ))}
          <button
            onClick={() => setShowRS(s => !s)}
            className="px-2.5 py-1 rounded text-xs font-semibold transition-colors"
            style={{
              backgroundColor: showRS ? '#94a3b8' : 'transparent',
              color: showRS ? '#0a0e1a' : '#475569',
            }}
          >
            RS
          </button>
        </div>
      </div>

      {/* Main candlestick chart + signal correlation tooltip */}
      <div className="relative">
        <div ref={mainRef} />
        {earningsLines.map(line => (
          <div
            key={line.date}
            className="absolute pointer-events-none"
            style={{ left: Math.round(line.x) - 1, top: 0, bottom: 0, width: 2, zIndex: 5 }}
          >
            <div style={{ position: 'absolute', inset: 0, borderLeft: `1px dashed ${line.color}90` }} />
            <div
              style={{
                position: 'absolute',
                bottom: 6,
                left: 4,
                fontSize: '0.6rem',
                fontWeight: 700,
                color: line.color,
                backgroundColor: `${line.color}22`,
                padding: '1px 4px',
                borderRadius: 3,
                border: `1px solid ${line.color}55`,
                lineHeight: 1.4,
                whiteSpace: 'nowrap',
              }}
            >
              E{line.beat === true ? ' ✓' : line.beat === false ? ' ✗' : ''}
            </div>
          </div>
        ))}
        {tooltip && (
          <div
            className="absolute pointer-events-none z-20 rounded-xl border p-3 text-xs shadow-2xl"
            style={{
              left: Math.min(tooltip.x + 14, (mainRef.current?.clientWidth ?? 600) - 210),
              top: Math.max(tooltip.y - 20, 8),
              backgroundColor: '#0d1526',
              borderColor: tooltip.signal === 'BUY' ? '#00e67660' : '#ff174460',
              minWidth: 190,
              backdropFilter: 'blur(8px)',
            }}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="font-black text-sm" style={{ color: tooltip.signal === 'BUY' ? '#00e676' : '#ff1744' }}>
                {tooltip.signal === 'BUY' ? '▲' : '▼'} {tooltip.signal}
              </span>
              <span className="tabular-nums" style={{ color: '#475569' }}>${tooltip.price.toFixed(2)}</span>
              <span style={{ color: '#334155' }}>{tooltip.date}</span>
            </div>
            <div className="text-xs font-semibold uppercase tracking-wide mb-1.5" style={{ color: '#475569' }}>
              Why this signal
            </div>
            {tooltip.reasons.map((r, i) => (
              <div key={i} className="flex items-start gap-1.5 mb-1 last:mb-0">
                <span className="mt-0.5 shrink-0" style={{ color: tooltip.signal === 'BUY' ? '#00e676' : '#ff1744' }}>•</span>
                <span style={{ color: '#94a3b8' }}>{r}</span>
              </div>
            ))}
          </div>
        )}
        {patternTooltip && (() => {
          const c = patternTooltip.direction === 'bullish' ? '#00e676' : patternTooltip.direction === 'bearish' ? '#ff1744' : '#ffab00'
          const icon = patternTooltip.direction === 'bullish' ? '▲' : patternTooltip.direction === 'bearish' ? '▼' : '◆'
          return (
            <div
              className="absolute pointer-events-none z-20 rounded-xl border p-3 text-xs shadow-2xl"
              style={{
                left: Math.min(patternTooltip.x + 14, (mainRef.current?.clientWidth ?? 600) - 230),
                top: Math.max(patternTooltip.y + (tooltip ? 130 : -20), 8),
                backgroundColor: '#0d1526',
                borderColor: c + '60',
                minWidth: 210,
                maxWidth: 280,
                backdropFilter: 'blur(8px)',
              }}
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="font-black text-sm" style={{ color: c }}>{icon} {patternTooltip.name}</span>
                <span className="tabular-nums" style={{ color: '#475569' }}>${patternTooltip.price.toFixed(2)}</span>
              </div>
              <div className="text-xs font-semibold uppercase tracking-wide mb-1" style={{ color: '#475569' }}>What it means</div>
              <p className="mb-2 leading-relaxed" style={{ color: '#94a3b8' }}>{patternTooltip.meaning}</p>
              <div className="text-xs font-semibold uppercase tracking-wide mb-1" style={{ color: '#475569' }}>Suggested action</div>
              <p className="leading-relaxed" style={{ color: c }}>{patternTooltip.action}</p>
              <div className="mt-2" style={{ color: '#334155' }}>Confidence {patternTooltip.confidence}% · {patternTooltip.date}</div>
            </div>
          )
        })()}
      </div>

      {/* Volume chart */}
      <div ref={volRef} style={{ borderTop: '1px solid rgba(255,255,255,0.04)' }} />

      {/* RSI panel */}
      {subData.length > 0 && indicators?.rsi && (
        <div style={{ borderTop: '1px solid rgba(255,255,255,0.04)' }}>
          <div className="px-4 pt-2 flex items-center gap-3 flex-wrap">
            <span className="text-xs font-semibold" style={{ color: '#94a3b8' }}>RSI (14)</span>
            {rsiLast != null && (
              <span className="text-xs font-bold" style={{ color: rsiColor }}>
                {rsiLast.toFixed(1)} · {tradingSignals?.rsi_signal ?? (rsiLast < 30 ? 'OVERSOLD' : rsiLast > 70 ? 'OVERBOUGHT' : 'NEUTRAL')}
              </span>
            )}
            {tradingSignals?.rsi_reversal_signal && (
              <span className="text-xs font-semibold px-2 py-0.5 rounded" style={{
                color: tradingSignals.rsi_reversal_signal.includes('OVERSOLD') || tradingSignals.rsi_reversal_signal.includes('SUPPORT') ? '#00e676' : '#ff1744',
                backgroundColor: tradingSignals.rsi_reversal_signal.includes('OVERSOLD') || tradingSignals.rsi_reversal_signal.includes('SUPPORT') ? '#00e67615' : '#ff174415',
              }}>
                {tradingSignals.rsi_reversal_signal}
              </span>
            )}
            {tradingSignals?.rsi_reversal_zone_low != null && (
              <span className="text-xs" style={{ color: '#334155' }}>
                zones: <span style={{ color: '#00e676' }}>{tradingSignals.rsi_reversal_zone_low}</span>
                {' / '}
                <span style={{ color: '#ff1744' }}>{tradingSignals.rsi_reversal_zone_high}</span>
                {tradingSignals.rsi_bullish_reversals != null && (
                  <span> · {tradingSignals.rsi_bullish_reversals}↑ {tradingSignals.rsi_bearish_reversals}↓ historical</span>
                )}
              </span>
            )}
          </div>
          <ResponsiveContainer width="100%" height={100}>
            <ComposedChart data={subData} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
              <XAxis dataKey="date" hide ticks={xTick} tick={{ fill: '#475569', fontSize: 10 }} />
              <YAxis domain={[0, 100]} hide width={32} tick={{ fill: '#475569', fontSize: 10 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1a2235', border: '1px solid #1a2235', borderRadius: 8, fontSize: 11 }}
                labelStyle={{ color: '#475569' }}
                itemStyle={{ color: '#00d4ff' }}
                formatter={(v: number) => [v?.toFixed(1), 'RSI']}
              />
              {/* Stock-specific reversal zones (solid) — override standard 30/70 (dashed) */}
              {tradingSignals?.rsi_reversal_zone_high != null
                ? <ReferenceLine y={tradingSignals.rsi_reversal_zone_high} stroke="#ff174450" strokeDasharray="4 2" />
                : <ReferenceLine y={70} stroke="#ff174430" strokeDasharray="3 3" />}
              <ReferenceLine y={50} stroke="#47556940" strokeDasharray="3 3" />
              {tradingSignals?.rsi_reversal_zone_low != null
                ? <ReferenceLine y={tradingSignals.rsi_reversal_zone_low} stroke="#00e67650" strokeDasharray="4 2" />
                : <ReferenceLine y={30} stroke="#00e67630" strokeDasharray="3 3" />}
              <Line
                type="monotone" dataKey="rsi" dot={false} stroke="#ffab00" strokeWidth={1.5}
                connectNulls isAnimationActive={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* MACD panel */}
      {subData.length > 0 && indicators?.macd && (
        <div style={{ borderTop: '1px solid rgba(255,255,255,0.04)' }}>
          <div className="px-4 pt-2 flex items-center gap-3">
            <span className="text-xs font-semibold" style={{ color: '#94a3b8' }}>MACD (12, 26, 9)</span>
            <LegendDot color="#00d4ff" label="MACD" />
            <LegendDot color="#ffab00" label="Signal" />
          </div>
          <ResponsiveContainer width="100%" height={110}>
            <ComposedChart data={subData} margin={{ top: 4, right: 12, left: 0, bottom: 4 }}>
              <XAxis dataKey="date" tick={{ fill: '#475569', fontSize: 10 }} ticks={xTick} />
              <YAxis hide width={32} tick={{ fill: '#475569', fontSize: 10 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1a2235', border: '1px solid #1a2235', borderRadius: 8, fontSize: 11 }}
                labelStyle={{ color: '#475569' }}
                formatter={(v: number, name: string) => [v?.toFixed(4), name]}
              />
              <ReferenceLine y={0} stroke="#47556960" />
              <Bar dataKey="hist" isAnimationActive={false}>
                {subData.map((d, i) => (
                  <Cell key={i} fill={(d.hist ?? 0) >= 0 ? '#00e67650' : '#ff174450'} />
                ))}
              </Bar>
              <Line type="monotone" dataKey="macd" dot={false} stroke="#00d4ff" strokeWidth={1.5} connectNulls isAnimationActive={false} name="MACD" />
              <Line type="monotone" dataKey="signal" dot={false} stroke="#ffab00" strokeWidth={1.5} connectNulls isAnimationActive={false} name="Signal" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Trade level pills */}
      {tradingSignals && (tradingSignals.stop_loss || tradingSignals.tp1) && (
        <div className="px-4 py-2.5 border-t flex flex-wrap items-center gap-2" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
          {(
            [
              tradingSignals.optimal_entry != null ? { label: 'ENTRY', value: tradingSignals.optimal_entry, color: '#00d4ff' } : null,
              tradingSignals.stop_loss != null ? { label: 'SL', value: tradingSignals.stop_loss, color: '#ff1744' } : null,
              tradingSignals.tp1 != null ? { label: 'TP1', value: tradingSignals.tp1, color: '#00e676' } : null,
              tradingSignals.tp2 != null ? { label: 'TP2', value: tradingSignals.tp2, color: '#00e676' } : null,
              tradingSignals.tp3 != null ? { label: 'TP3', value: tradingSignals.tp3, color: '#00e676' } : null,
            ] as Array<{ label: string; value: number; color: string } | null>
          ).filter((x): x is { label: string; value: number; color: string } => x !== null).map(({ label, value, color }) => (
            <div key={label} className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs" style={{ backgroundColor: `${color}12`, border: `1px solid ${color}35` }}>
              <span className="font-semibold" style={{ color: '#64748b' }}>{label}</span>
              <span className="font-bold tabular-nums font-mono" style={{ color }}>${value.toFixed(2)}</span>
            </div>
          ))}
          {tradingSignals.risk_reward != null && (
            <div className="ml-auto flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs" style={{ backgroundColor: '#00d4ff10', border: '1px solid #00d4ff30' }}>
              <span style={{ color: '#475569' }}>R/R</span>
              <span className="font-bold" style={{ color: '#00d4ff' }}>{tradingSignals.risk_reward.toFixed(1)}:1</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function LegendDot({ color, label, dot }: { color: string; label: string; dot?: boolean }) {
  return (
    <span className="flex items-center gap-1.5 text-xs" style={{ color: '#94a3b8' }}>
      {dot
        ? <span className="w-2 h-2 inline-block rounded-full" style={{ backgroundColor: color }} />
        : <span className="w-3 h-0.5 inline-block rounded" style={{ backgroundColor: color }} />
      }
      {label}
    </span>
  )
}
