import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuth } from './hooks/useAuth'
import TopNav from './components/layout/TopNav'
import Login from './pages/Login'
import Home from './pages/Home'
import Analysis from './pages/Analysis'
import Screener from './pages/Screener'
import Reports from './pages/Reports'
import Opportunities from './pages/Opportunities'
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
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/*" element={
            <AuthGate>
              <TopNav />
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/analysis" element={<Analysis />} />
                <Route path="/screener" element={<Screener />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="/opportunities" element={<Opportunities />} />
                <Route path="/watchlist" element={<Watchlist />} />
                <Route path="/penny-stocks" element={<PennyStocks />} />
                <Route path="/alerts" element={<Alerts />} />
              </Routes>
            </AuthGate>
          } />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
