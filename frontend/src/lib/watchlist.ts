const WL_KEY = 'vf_watchlist'
const PF_KEY = 'vf_portfolio'

export interface PortfolioEntry {
  ticker: string
  shares: number
}

export const INITIAL_PORTFOLIO: PortfolioEntry[] = [
  { ticker: 'NTNX', shares: 140 }, { ticker: 'CVLT', shares: 90 },
  { ticker: 'SOUN', shares: 600 }, { ticker: 'RR', shares: 777 },
  { ticker: 'QUBT', shares: 1145 }, { ticker: 'TTD', shares: 100 },
  { ticker: 'LAC', shares: 185 }, { ticker: 'PHUN', shares: 250 },
  { ticker: 'IDAI', shares: 210 }, { ticker: 'INTZ', shares: 1000 },
  { ticker: 'VERI', shares: 400 }, { ticker: 'ZENA', shares: 600 },
  { ticker: 'NIO', shares: 240 }, { ticker: 'GSOL', shares: 100 },
  { ticker: 'NNOX', shares: 300 }, { ticker: 'DVLT', shares: 1800 },
  { ticker: 'KULR', shares: 100 }, { ticker: 'CXAI', shares: 1000 },
  { ticker: 'TLRY', shares: 24.5 }, { ticker: 'CETX', shares: 53.3333 },
  { ticker: 'BNZI', shares: 150 }, { ticker: 'ARBK', shares: 1 },
  { ticker: 'DFLI', shares: 2.7 }, { ticker: 'HUBC', shares: 0.1667 },
  { ticker: 'AMD', shares: 40 }, { ticker: 'MU', shares: 20 },
  { ticker: 'CRWV', shares: 35 }, { ticker: 'RGTI', shares: 250 },
  { ticker: 'QTUM', shares: 50 }, { ticker: 'APLD', shares: 100 },
  { ticker: 'QCOM', shares: 15 }, { ticker: 'RKLB', shares: 54 },
  { ticker: 'SERV', shares: 200 }, { ticker: 'HOOD', shares: 50 },
  { ticker: 'GDX', shares: 50 }, { ticker: 'INOD', shares: 75 },
  { ticker: 'PANW', shares: 30 }, { ticker: 'IAUM', shares: 50 },
  { ticker: 'TSM', shares: 15 }, { ticker: 'SE', shares: 50 },
  { ticker: 'NOW', shares: 90 }, { ticker: 'P', shares: 50 },
  { ticker: 'INTU', shares: 15 }, { ticker: 'HIVE', shares: 1600 },
  { ticker: 'BLNK', shares: 900 }, { ticker: 'QBTS', shares: 190 },
  { ticker: 'IONQ', shares: 100 }, { ticker: 'NNE', shares: 265 },
  { ticker: 'SMCI', shares: 320 }, { ticker: 'OKLO', shares: 92 },
  { ticker: 'HYDR', shares: 40 }, { ticker: 'COIN', shares: 125 },
  { ticker: 'PLTR', shares: 100 },
]

// ── Watchlist helpers ─────────────────────────────────────────────────────────

export function getWatchlist(): string[] {
  try { return JSON.parse(localStorage.getItem(WL_KEY) ?? '[]') } catch { return [] }
}

export function addToWatchlist(ticker: string): void {
  const list = getWatchlist()
  if (!list.includes(ticker))
    localStorage.setItem(WL_KEY, JSON.stringify([...list, ticker]))
}

export function removeFromWatchlist(ticker: string): void {
  localStorage.setItem(WL_KEY, JSON.stringify(getWatchlist().filter(t => t !== ticker)))
}

export function isInWatchlist(ticker: string): boolean {
  return getWatchlist().includes(ticker)
}

// ── Portfolio helpers ─────────────────────────────────────────────────────────

export function getPortfolio(): PortfolioEntry[] {
  try {
    const raw = localStorage.getItem(PF_KEY)
    if (!raw) return []
    return JSON.parse(raw)
  } catch { return [] }
}

export function setPortfolio(entries: PortfolioEntry[]): void {
  localStorage.setItem(PF_KEY, JSON.stringify(entries))
}

export function addToPortfolio(ticker: string, shares = 0): void {
  const list = getPortfolio()
  if (!list.find(e => e.ticker === ticker))
    setPortfolio([...list, { ticker, shares }])
}

export function removeFromPortfolio(ticker: string): void {
  setPortfolio(getPortfolio().filter(e => e.ticker !== ticker))
}

export function seedPortfolioIfEmpty(): void {
  if (getPortfolio().length === 0) setPortfolio(INITIAL_PORTFOLIO)
}
