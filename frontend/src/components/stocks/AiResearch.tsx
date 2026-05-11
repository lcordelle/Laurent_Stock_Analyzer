import { useState } from 'react'
import { Sparkles, Send, ChevronDown, ChevronUp, Loader2 } from 'lucide-react'
import api from '../../services/api'
import type { FullStockAnalysis } from '../../lib/types'

interface Props {
  ticker: string
  data: FullStockAnalysis
}

interface Message {
  role: 'user' | 'ai'
  text: string
}

const SUGGESTED = [
  'Is this a good buy at current price?',
  'What are the main risks?',
  'How does the valuation compare to peers?',
  'When would you take profits?',
  'What catalysts could move this stock?',
  'Summarise the bull and bear case',
]

export function AiResearch({ ticker, data }: Props) {
  const [expanded, setExpanded] = useState(false)
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function submit(question: string) {
    const q = question.trim()
    if (!q || loading) return
    setInput('')
    setError(null)
    setMessages(prev => [...prev, { role: 'user', text: q }])
    setLoading(true)
    try {
      const res = await api.post('/ai/research', { ticker, question: q, context: data })
      const answer: string = res.data?.answer ?? res.data?.response ?? JSON.stringify(res.data)
      setMessages(prev => [...prev, { role: 'ai', text: answer }])
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Request failed'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  function handleSuggestion(q: string) {
    setInput(q)
    submit(q)
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') submit(input)
  }

  return (
    <div
      style={{
        backgroundColor: '#111827',
        border: '1px solid rgba(0,212,255,0.2)',
        borderRadius: '0.75rem',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <button
        onClick={() => setExpanded(v => !v)}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.875rem 1.25rem',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          color: '#e2e8f0',
        }}
      >
        <Sparkles size={16} style={{ color: '#00d4ff', flexShrink: 0 }} />
        <span style={{ fontWeight: 600, fontSize: '0.875rem', flex: 1, textAlign: 'left' }}>
          AI Research Assistant
        </span>
        {expanded
          ? <ChevronUp size={16} style={{ color: '#94a3b8' }} />
          : <ChevronDown size={16} style={{ color: '#94a3b8' }} />
        }
      </button>

      {expanded && (
        <div style={{ padding: '0 1.25rem 1.25rem' }}>

          {/* Suggested chips */}
          {messages.length === 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1rem' }}>
              {SUGGESTED.map(q => (
                <button
                  key={q}
                  onClick={() => handleSuggestion(q)}
                  disabled={loading}
                  style={{
                    fontSize: '0.7rem',
                    padding: '0.3rem 0.625rem',
                    borderRadius: '9999px',
                    border: '1px solid rgba(0,212,255,0.3)',
                    backgroundColor: 'rgba(0,212,255,0.06)',
                    color: '#00d4ff',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    opacity: loading ? 0.5 : 1,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {q}
                </button>
              ))}
            </div>
          )}

          {/* Message history */}
          {messages.length > 0 && (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.75rem',
                marginBottom: '1rem',
                maxHeight: '22rem',
                overflowY: 'auto',
              }}
            >
              {messages.map((msg, i) => (
                <div
                  key={i}
                  style={{
                    display: 'flex',
                    justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  }}
                >
                  <div
                    style={{
                      maxWidth: '80%',
                      padding: '0.625rem 0.875rem',
                      borderRadius: msg.role === 'user' ? '1rem 1rem 0.25rem 1rem' : '1rem 1rem 1rem 0.25rem',
                      backgroundColor: msg.role === 'user' ? 'rgba(0,212,255,0.18)' : '#1a2235',
                      color: msg.role === 'user' ? '#00d4ff' : '#e2e8f0',
                      fontSize: '0.8125rem',
                      lineHeight: '1.5',
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {msg.text}
                  </div>
                </div>
              ))}

              {loading && (
                <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                  <div
                    style={{
                      padding: '0.625rem 0.875rem',
                      borderRadius: '1rem 1rem 1rem 0.25rem',
                      backgroundColor: '#1a2235',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.375rem',
                      color: '#94a3b8',
                      fontSize: '0.8125rem',
                    }}
                  >
                    <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} />
                    Thinking…
                  </div>
                </div>
              )}

              {error && (
                <div
                  role="alert"
                  style={{
                    fontSize: '0.75rem',
                    color: '#ff1744',
                    backgroundColor: 'rgba(255,23,68,0.08)',
                    border: '1px solid rgba(255,23,68,0.2)',
                    borderRadius: '0.5rem',
                    padding: '0.5rem 0.75rem',
                  }}
                >
                  {error}
                </div>
              )}
            </div>
          )}

          {/* Suggested chips (after messages) */}
          {messages.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.75rem' }}>
              {SUGGESTED.map(q => (
                <button
                  key={q}
                  onClick={() => handleSuggestion(q)}
                  disabled={loading}
                  style={{
                    fontSize: '0.65rem',
                    padding: '0.25rem 0.5rem',
                    borderRadius: '9999px',
                    border: '1px solid rgba(0,212,255,0.2)',
                    backgroundColor: 'rgba(0,212,255,0.04)',
                    color: '#94a3b8',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    opacity: loading ? 0.5 : 1,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {q}
                </button>
              ))}
            </div>
          )}

          {/* Input row */}
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
              placeholder={`Ask anything about ${ticker}…`}
              style={{
                flex: 1,
                backgroundColor: '#0a0e1a',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: '0.5rem',
                padding: '0.5rem 0.75rem',
                fontSize: '0.8125rem',
                color: '#e2e8f0',
                outline: 'none',
                opacity: loading ? 0.6 : 1,
              }}
            />
            <button
              onClick={() => submit(input)}
              disabled={loading || !input.trim()}
              aria-label="Send question"
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '2.25rem',
                height: '2.25rem',
                borderRadius: '0.5rem',
                border: 'none',
                backgroundColor: loading || !input.trim() ? 'rgba(0,212,255,0.15)' : '#00d4ff',
                color: loading || !input.trim() ? '#475569' : '#0a0e1a',
                cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
                flexShrink: 0,
              }}
            >
              {loading
                ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} />
                : <Send size={14} />
              }
            </button>
          </div>
        </div>
      )}

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
