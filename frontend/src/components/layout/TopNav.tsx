import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../../hooks/useAuth'
import { marketPulseApi } from '../../services/api'

const NAV_LINKS = [
  { to: '/', label: 'Dashboard' },
  { to: '/analysis', label: 'Analysis' },
  { to: '/radar', label: '⚡ Radar' },
  { to: '/watchlist', label: '★ Watchlist' },
  { to: '/penny-stocks', label: '💎 Penny Buys' },
  { to: '/alerts', label: '🔔 Alerts' },
  { to: '/reports', label: 'Reports' },
]

export default function TopNav() {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const { logout } = useAuth()

  const { data: regime } = useQuery({
    queryKey: ['market-regime'],
    queryFn: marketPulseApi.marketBreadth,
    staleTime: 5 * 60_000,
    refetchInterval: 5 * 60_000,
  })

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <nav
      className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 h-14 border-b"
      style={{ backgroundColor: '#0a0e1a', borderColor: 'rgba(255,255,255,0.05)' }}
      data-testid="top-nav"
    >
      <div className="flex items-center gap-3">
        <div
          className="flex items-center justify-center w-8 h-8 rounded text-xs font-bold"
          style={{ backgroundColor: '#00d4ff', color: '#0a0e1a' }}
        >
          VF
        </div>
        <span className="text-sm font-semibold" style={{ color: '#e2e8f0' }}>
          Stock Analyzer
        </span>
      </div>

      <div className="flex items-center gap-1">
        {NAV_LINKS.map(({ to, label }) => {
          const isActive = to === '/' ? pathname === '/' : pathname.startsWith(to)
          return (
            <Link
              key={to}
              to={to}
              className="px-4 py-1.5 text-sm font-medium transition-colors"
              style={{
                color: isActive ? '#00d4ff' : '#94a3b8',
                borderBottom: isActive ? '2px solid #00d4ff' : '2px solid transparent',
              }}
            >
              {label}
            </Link>
          )
        })}
      </div>

      <div className="flex items-center gap-3 shrink-0">
        {regime?.regime && regime.regime !== 'Unknown' && (
          <div
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold"
            style={{
              backgroundColor: regime.color + '18',
              border: `1px solid ${regime.color}40`,
            }}
            title={regime.description ?? ''}
          >
            <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: regime.color }} />
            <span style={{ color: regime.color }}>{regime.regime}</span>
            {regime.vix != null && (
              <span style={{ color: '#475569' }}>VIX {regime.vix}</span>
            )}
            {regime.spy_change != null && (
              <span style={{ color: regime.spy_change >= 0 ? '#00e676' : '#ff1744' }}>
                SPY {regime.spy_change >= 0 ? '+' : ''}{regime.spy_change.toFixed(1)}%
              </span>
            )}
          </div>
        )}
        <button
          onClick={handleLogout}
          className="px-3 py-1.5 text-xs font-medium rounded border transition-colors hover:bg-white/5"
          style={{ color: '#94a3b8', borderColor: 'rgba(255,255,255,0.1)' }}
          data-testid="logout-btn"
        >
          Logout
        </button>
      </div>
    </nav>
  )
}
