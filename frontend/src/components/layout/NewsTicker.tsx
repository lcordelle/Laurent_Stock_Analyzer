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

export default function NewsTicker() {
  const { data } = useQuery({
    queryKey: ['market-news'],
    queryFn: newsApi.market,
    staleTime: 5 * 60_000,
    refetchInterval: 5 * 60_000,
  })

  const items = data?.items ?? []
  if (items.length === 0) return null

  // Duration scales with item count so speed stays constant (~80px/s at 40 chars/item)
  const durationSec = Math.max(30, items.length * 8)

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
        className="shrink-0 flex items-center gap-1.5 px-3 h-full z-10"
        style={{
          backgroundColor: '#00d4ff',
          borderRight: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
        <span className="text-xs font-black tracking-widest uppercase" style={{ color: '#0a0e1a' }}>
          LIVE
        </span>
      </div>

      {/* Scrolling content */}
      <div className="flex-1 overflow-hidden relative" style={{ height: '28px' }}>
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
          }
          .ticker-track:hover {
            animation-play-state: paused;
          }
        `}</style>
        <div className="ticker-track">
          {/* Duplicate content so second copy fills the gap seamlessly */}
          {[...items, ...items].map((item, i) => (
            <TickerItem key={i} item={item} />
          ))}
        </div>
      </div>
    </div>
  )
}
