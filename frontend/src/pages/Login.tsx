import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(username, password)
      navigate('/')
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status
      if (status === 401) {
        setError('Wrong username or password. Check for autofilled credentials and try again.')
      } else if (!status) {
        setError('Cannot reach server. Check that the backend is running and try again.')
      } else {
        setError(`Login failed (error ${status}). Please try again.`)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center"
      style={{ backgroundColor: '#0a0e1a' }}
    >
      <div
        className="w-full max-w-sm rounded-2xl border p-8"
        style={{ backgroundColor: '#111827', borderColor: 'rgba(255,255,255,0.06)' }}
      >
        <div className="flex flex-col items-center gap-3 mb-8">
          <div
            className="flex items-center justify-center w-12 h-12 rounded-xl text-lg font-bold"
            style={{ backgroundColor: '#00d4ff', color: '#0a0e1a' }}
          >
            VF
          </div>
          <div className="text-center">
            <h1 className="text-xl font-bold" style={{ color: '#e2e8f0' }}>Stock Analyzer</h1>
            <p className="text-sm mt-1" style={{ color: '#475569' }}>VirtualFusion AI Platform</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4" data-testid="login-form">
          <div>
            <label htmlFor="username" className="block text-xs font-medium mb-1.5" style={{ color: '#94a3b8' }}>
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              className="w-full rounded-lg px-3 py-2.5 text-sm outline-none transition-all focus:ring-1"
              style={{
                backgroundColor: '#1a2235',
                border: '1px solid rgba(255,255,255,0.08)',
                color: '#e2e8f0',
              }}
              placeholder="Enter username"
              required
              data-testid="username-input"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-xs font-medium mb-1.5" style={{ color: '#94a3b8' }}>
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="w-full rounded-lg px-3 py-2.5 text-sm outline-none transition-all"
              style={{
                backgroundColor: '#1a2235',
                border: '1px solid rgba(255,255,255,0.08)',
                color: '#e2e8f0',
              }}
              placeholder="Enter password"
              required
              data-testid="password-input"
            />
          </div>

          {error && (
            <p
              className="text-xs px-3 py-2 rounded-lg"
              style={{ color: '#ff1744', backgroundColor: 'rgba(255,23,68,0.1)' }}
              role="alert"
            >
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-lg text-sm font-semibold transition-opacity disabled:opacity-60"
            style={{
              background: 'linear-gradient(135deg, #00d4ff, #0088cc)',
              color: '#0a0e1a',
            }}
            data-testid="login-btn"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  )
}
