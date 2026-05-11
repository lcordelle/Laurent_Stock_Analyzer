export const fmt = {
  price: (v?: number) => v != null ? `$${v.toFixed(2)}` : '—',
  currency: (v?: number) => {
    if (v == null) return '—'
    if (v >= 1e6) return `$${(v/1e6).toFixed(2)}M`
    if (v >= 1e3) return `$${(v/1e3).toFixed(1)}K`
    return `$${v.toFixed(2)}`
  },
  pct: (v?: number) => v != null ? `${v.toFixed(2)}%` : '—',
  ratio: (v?: number) => v != null ? v.toFixed(2) : '—',
  mcap: (v?: number) => {
    if (!v) return '—'
    if (v >= 1e12) return `$${(v/1e12).toFixed(2)}T`
    if (v >= 1e9) return `$${(v/1e9).toFixed(2)}B`
    return `$${(v/1e6).toFixed(2)}M`
  },
  vol: (v?: number) => v != null ? v.toLocaleString() : '—',
}

export const scoreColor = (score: number) => {
  if (score >= 75) return '#00e676'
  if (score >= 55) return '#ffab00'
  return '#ff1744'
}

export const changeColor = (v?: number) => (v ?? 0) >= 0 ? '#00e676' : '#ff1744'
