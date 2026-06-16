import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useEffect } from 'react'
import { useAuth } from './hooks/useAuth'

// Detect stale cached bundles and force a hard reload when the server has a newer one.
function StaleBundleGuard() {
  useEffect(() => {
    const currentScript = Array.from(document.scripts).find(s => s.src.includes('/assets/index-'))
    if (!currentScript) return
    const currentBundle = currentScript.src.split('/').pop()
    fetch('/api/bundle-version', { cache: 'no-store' })
      .then(r => r.json())
      .then(({ bundle }: { bundle: string }) => {
        if (bundle !== currentBundle) window.location.reload()
      })
      .catch(() => {/* network error — stay silent */})
  }, [])
  return null
}
import TopNav from './components/layout/TopNav'
import NewsTicker from './components/layout/NewsTicker'
import Login from './pages/Login'
import Home from './pages/Home'
import Analysis from './pages/Analysis'
import Radar from './pages/Radar'
import Reports from './pages/Reports'
import Watchlist from './pages/Watchlist'
import PennyStocks from './pages/PennyStocks'
import Alerts from './pages/Alerts'
import './index.css'

const qc = new QueryClient({ defaultOptions: { queries: { retry: 1, staleTime: 5 * 60 * 1000 } } })

function AuthGate({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <StaleBundleGuard />
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/*" element={
            <AuthGate>
              <TopNav />
              {/* 78px bottom clearance for three-row ticker (3 × 26px) */}
              <div style={{ paddingBottom: '78px' }}>
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/analysis" element={<Analysis />} />
                <Route path="/radar" element={<Radar />} />
                <Route path="/screener" element={<Navigate to="/radar" replace />} />
                <Route path="/opportunities" element={<Navigate to="/radar" replace />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="/watchlist" element={<Watchlist />} />
                <Route path="/penny-stocks" element={<PennyStocks />} />
                <Route path="/alerts" element={<Alerts />} />
              </Routes>
              </div>
              <NewsTicker />
            </AuthGate>
          } />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
