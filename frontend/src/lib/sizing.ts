export interface SizingInput {
  equity: number
  maxRiskPct: number      // e.g. 1 = 1%
  conviction: number      // 0..10
  entry: number | null
  stop: number | null
}
export interface SizingResult {
  ok: boolean
  reason?: string
  riskPct: number
  riskDollars: number
  shares: number
  positionDollars: number
  pctOfEquity: number
  capped: boolean
}

export function computeSizing(i: SizingInput): SizingResult {
  const base = { riskPct: 0, riskDollars: 0, shares: 0, positionDollars: 0, pctOfEquity: 0, capped: false }
  if (!i.equity || i.equity <= 0) return { ok: false, reason: 'Set account size', ...base }
  if (i.entry == null || i.stop == null) return { ok: false, reason: 'No valid stop — size manually', ...base }
  const stopDist = Math.abs(i.entry - i.stop)
  if (stopDist <= 0) return { ok: false, reason: 'No valid stop — size manually', ...base }
  const riskPct = i.maxRiskPct * (Math.max(0, Math.min(10, i.conviction)) / 10)
  const riskDollars = i.equity * (riskPct / 100)
  let shares = Math.floor(riskDollars / stopDist)
  let positionDollars = shares * i.entry
  let capped = false
  if (positionDollars > i.equity) {          // no leverage
    shares = Math.floor(i.equity / i.entry)
    positionDollars = shares * i.entry
    capped = true
  }
  return {
    ok: shares > 0,
    reason: shares > 0 ? undefined : 'Risk too small for one share',
    riskPct, riskDollars, shares, positionDollars,
    pctOfEquity: i.equity ? (positionDollars / i.equity) * 100 : 0,
    capped,
  }
}
