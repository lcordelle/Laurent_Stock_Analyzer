import type { NewsArticle } from '../../lib/types'

const SENTIMENT_COLORS: Record<string, string> = {
  positive: '#00e676',
  negative: '#ff1744',
  neutral: '#ffab00',
}

interface NewsPanelProps {
  articles: NewsArticle[]
}

export default function NewsPanel({ articles }: NewsPanelProps) {
  if (articles.length === 0) {
    return (
      <div
        className="rounded-xl border p-5 flex items-center justify-center"
        style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)', minHeight: 200 }}
      >
        <p className="text-sm" style={{ color: '#475569' }}>No news available</p>
      </div>
    )
  }

  return (
    <div
      className="rounded-xl border p-5 flex flex-col gap-3"
      style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
      data-testid="news-panel"
    >
      <h3 className="text-sm font-semibold uppercase tracking-wide" style={{ color: '#94a3b8' }}>
        Latest News
      </h3>
      <div className="flex flex-col gap-3 overflow-y-auto" style={{ maxHeight: 400 }}>
        {articles.map((article, i) => {
          const sentimentColor = article.sentiment ? SENTIMENT_COLORS[article.sentiment.toLowerCase()] ?? '#475569' : '#475569'
          return (
            <div
              key={i}
              className="border-b pb-3 last:border-b-0 last:pb-0"
              style={{ borderColor: 'rgba(255,255,255,0.04)' }}
            >
              {article.url ? (
                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm font-semibold leading-snug hover:underline block"
                  style={{ color: '#e2e8f0' }}
                >
                  {article.title}
                </a>
              ) : (
                <p className="text-sm font-semibold leading-snug" style={{ color: '#e2e8f0' }}>
                  {article.title}
                </p>
              )}
              {article.summary && (
                <p
                  className="text-xs mt-1 leading-relaxed overflow-hidden"
                  style={{ color: '#94a3b8', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' } as React.CSSProperties}
                >
                  {article.summary}
                </p>
              )}
              <div className="flex items-center gap-2 mt-1.5">
                {article.published && (
                  <span className="text-xs" style={{ color: '#475569' }}>
                    {new Date(article.published).toLocaleDateString()}
                  </span>
                )}
                {article.sentiment && (
                  <span
                    className="text-xs font-semibold px-1.5 py-0.5 rounded capitalize"
                    style={{ color: sentimentColor, backgroundColor: `${sentimentColor}20` }}
                  >
                    {article.sentiment}
                  </span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
