import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'

const NAV_LINKS = [
  { to: '/', label: 'Dashboard' },
  { to: '/analysis', label: 'Analysis' },
  { to: '/opportunities', label: '⚡ Opportunities' },
  { to: '/watchlist', label: '★ Watchlist' },
  { to: '/penny-stocks', label: '💎 Penny Buys' },
  { to: '/ai-predictor', label: '🤖 AI Predictor' },
  { to: '/batch', label: 'Batch' },
  { to: '/screener', label: 'Screener' },
  { to: '/reports', label: 'Reports' },
]

export default function TopNav() {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const { logout } = useAuth()

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

      <button
        onClick={handleLogout}
        className="px-3 py-1.5 text-xs font-medium rounded border transition-colors hover:bg-white/5"
        style={{ color: '#94a3b8', borderColor: 'rgba(255,255,255,0.1)' }}
        data-testid="logout-btn"
      >
        Logout
      </button>
    </nav>
  )
}
