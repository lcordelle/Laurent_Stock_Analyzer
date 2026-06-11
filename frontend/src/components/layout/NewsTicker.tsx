import { useQuery } from '@tanstack/react-query'
import { newsApi, type NewsItem } from '../../services/api'

function sentimentColor(s: NewsItem['sentiment']): string {
  if (s === 'positive') return '#00e676'
  if (s === 'negative') return '#ff1744'
  return '#94a3b8'
}

function TickerItem({ item }: { item: NewsItem }) {
  const color = sentimentColor(item.sentiment)
  return (
    <span className="inline-flex items-center gap-2 pr-10 shrink-0">
      <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: color }} />
      <span className="text-xs font-semibold uppercase tracking-wider shrink-0" style={{ color: '#475569' }}>
        {item.source}
      </span>
      <span className="text-xs" style={{ color }}>
        {item.title}
      </span>
    </span>
  )
}

const LOADING_ITEMS: NewsItem[] = [
  { title: 'Loading market news…', source: 'MARKET', url: '', published_at: '', sentiment: 'neutral' },
  { title: 'Fetching live headlines from MarketWatch · CNBC · Reuters · Yahoo Finance', source: 'MARKET', url: '', published_at: '', sentiment: 'neutral' },
]

export default function NewsTicker() {
  const { data, isError } = useQuery({
    queryKey: ['market-news'],
    queryFn: newsApi.market,
    staleTime: 5 * 60_000,
    refetchInterval: 5 * 60_000,
    retry: 2,
  })

  const items = data?.items?.length ? data.items : isError ? [] : LOADING_ITEMS
  // Hide entirely only on hard error
  if (isError && !data?.items?.length) return null

  // Target ~120 px/s: each item ≈ 350 px wide → 350/120 ≈ 3s per item
  const durationSec = items === LOADING_ITEMS ? 12 : Math.max(20, items.length * 3)

  return (
    <div
      className="fixed bottom-0 left-0 right-0 z-50 flex items-center overflow-hidden"
      style={{
        backgroundColor: '#060a14',
        borderTop: '1px solid rgba(255,255,255,0.06)',
        height: '28px',
      }}
    >
      {/* Label */}
      <div
        className="shrink-0 flex items-center gap-1.5 px-3 h-full"
        style={{
          backgroundColor: '#00d4ff',
          borderRight: '1px solid rgba(0,0,0,0.3)',
        }}
      >
        <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
        <span className="text-xs font-black tracking-widest uppercase" style={{ color: '#0a0e1a' }}>
          LIVE
        </span>
      </div>

      {/* Scrolling content */}
      <div className="flex-1 overflow-hidden" style={{ height: '28px' }}>
        <style>{`
          @keyframes ticker-scroll {
            0%   { transform: translateX(0); }
            100% { transform: translateX(-50%); }
          }
          .ticker-track {
            display: flex;
            align-items: center;
            white-space: nowrap;
            animation: ticker-scroll ${durationSec}s linear infinite;
            height: 28px;
            padding-left: 16px;
          }
          .ticker-track:hover {
            animation-play-state: paused;
          }
        `}</style>
        <div className="ticker-track">
          {[...items, ...items].map((item, i) => (
            <TickerItem key={i} item={item} />
          ))}
        </div>
      </div>
    </div>
  )
}
