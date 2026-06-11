import { useQuery } from '@tanstack/react-query'
import { newsApi, type NewsItem } from '../../services/api'

const MARKET_SOURCES = new Set(['MarketWatch', 'CNBC', 'Reuters Biz', 'Investopedia', 'Yahoo Finance', 'MARKET'])
const ROW_H = 26

function sentimentColor(s: NewsItem['sentiment']): string {
  if (s === 'positive') return '#00e676'
  if (s === 'negative') return '#ff1744'
  return '#94a3b8'
}

function TickerItem({ item }: { item: NewsItem }) {
  const color = sentimentColor(item.sentiment)
  return (
    <span className="inline-flex items-center gap-2 shrink-0" style={{ paddingRight: '40px' }}>
      <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: color }} />
      <span className="font-semibold uppercase tracking-wider shrink-0"
        style={{ color: '#475569', fontSize: '10px' }}>
        {item.source}
      </span>
      <span style={{ color, fontSize: '11px' }}>
        {item.title}
      </span>
    </span>
  )
}

interface TickerRowProps {
  label: string
  labelBg: string
  items: NewsItem[]
  durSec: number
  animName: string
  borderBottom?: boolean
}

function TickerRow({ label, labelBg, items, durSec, animName, borderBottom }: TickerRowProps) {
  return (
    <div className="flex overflow-hidden"
      style={{
        height: `${ROW_H}px`,
        borderBottom: borderBottom ? '1px solid rgba(255,255,255,0.04)' : undefined,
      }}
    >
      {/* Row label */}
      <div className="shrink-0 flex items-center justify-center px-3"
        style={{
          backgroundColor: labelBg,
          minWidth: '72px',
          borderRight: '1px solid rgba(0,0,0,0.25)',
        }}
      >
        <span style={{ color: '#0a0e1a', fontSize: '9px', fontWeight: 900, letterSpacing: '0.1em' }}>
          {label}
        </span>
      </div>

      {/* Scrolling strip */}
      <div className="flex-1 overflow-hidden" style={{ height: `${ROW_H}px` }}>
        <style>{`
          @keyframes ${animName} {
            0%   { transform: translateX(0); }
            100% { transform: translateX(-50%); }
          }
          .${animName}-track {
            display: flex;
            align-items: center;
            white-space: nowrap;
            animation: ${animName} ${durSec}s linear infinite;
            height: ${ROW_H}px;
            padding-left: 14px;
          }
          .${animName}-track:hover {
            animation-play-state: paused;
          }
        `}</style>
        <div className={`${animName}-track`}>
          {[...items, ...items].map((item, i) => (
            <TickerItem key={i} item={item} />
          ))}
        </div>
      </div>
    </div>
  )
}

const LOADING_MARKET: NewsItem[] = [
  { title: 'Loading market headlines… MarketWatch · CNBC · Yahoo Finance', source: 'MARKET', url: '', published_at: '', sentiment: 'neutral' },
  { title: 'Fetching live equity and macro news…', source: 'MARKET', url: '', published_at: '', sentiment: 'neutral' },
]
const LOADING_WORLD: NewsItem[] = [
  { title: 'Loading world news… BBC · Sky News · Al Jazeera · The Guardian', source: 'WORLD', url: '', published_at: '', sentiment: 'neutral' },
  { title: 'Fetching geopolitical and breaking news…', source: 'WORLD', url: '', published_at: '', sentiment: 'neutral' },
]

export default function NewsTicker() {
  const { data, isError } = useQuery({
    queryKey: ['market-news'],
    queryFn: newsApi.market,
    staleTime: 5 * 60_000,
    refetchInterval: 5 * 60_000,
    retry: 2,
  })

  if (isError && !data?.items?.length) return null

  const all = data?.items ?? []
  const marketItems = all.filter(i => MARKET_SOURCES.has(i.source))
  const worldItems  = all.filter(i => !MARKET_SOURCES.has(i.source))

  const row1 = marketItems.length ? marketItems : LOADING_MARKET
  const row2 = worldItems.length  ? worldItems  : LOADING_WORLD

  const dur1 = row1 === LOADING_MARKET ? 14 : Math.max(20, row1.length * 3)
  const dur2 = row2 === LOADING_WORLD  ? 16 : Math.max(20, row2.length * 3.5) // slight offset

  return (
    <div
      className="fixed bottom-0 left-0 right-0 z-50 flex flex-col"
      style={{
        backgroundColor: '#060a14',
        borderTop: '1px solid rgba(255,255,255,0.07)',
        height: `${ROW_H * 2}px`,
      }}
    >
      <TickerRow
        label="MARKETS"
        labelBg="#00d4ff"
        items={row1}
        durSec={dur1}
        animName="ticker-markets"
        borderBottom
      />
      <TickerRow
        label="WORLD"
        labelBg="#ff6b35"
        items={row2}
        durSec={dur2}
        animName="ticker-world"
      />
    </div>
  )
}
