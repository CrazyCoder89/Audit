import { useState, useRef, useEffect } from 'react'

export default function ChatPanel({ messages, onSend, onClose, userName }) {
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = () => {
    if (input.trim()) { onSend(input.trim()); setInput('') }
  }

  return (
    <div style={{
      height: '100%', display: 'flex', flexDirection: 'column',
      fontFamily: 'monospace'
    }}>
      <div style={{
        padding: '12px 16px', borderBottom: '1px solid #1E2D4D',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center'
      }}>
        <span style={{ color: '#00D4FF', fontSize: 12, fontWeight: 700, letterSpacing: 2 }}>
          ◈ MEETING CHAT
        </span>
        <button onClick={onClose} style={{
          background: 'none', border: 'none', color: '#4A5568',
          cursor: 'pointer', fontSize: 18
        }}>✕</button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: 12 }}>
        {messages.map((m, i) => (
          <div key={i} style={{ marginBottom: 10 }}>
            <div style={{ fontSize: 10, color: '#4A5568', marginBottom: 2 }}>
              <span style={{ color: '#00D4FF' }}>{m.user_name}</span>
              &nbsp;·&nbsp;{m.timestamp}
            </div>
            <div style={{
              background: '#0A0E1A', borderRadius: 8,
              padding: '8px 12px', fontSize: 12, color: '#E2E8F0',
              border: '1px solid #1E2D4D', lineHeight: 1.5
            }}>
              {m.message}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div style={{ padding: 12, borderTop: '1px solid #1E2D4D', display: 'flex', gap: 8 }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
          placeholder="Type a message..."
          style={{
            flex: 1, background: '#0A0E1A', border: '1px solid #1E2D4D',
            borderRadius: 6, padding: '8px 12px', color: '#E2E8F0',
            fontFamily: 'monospace', fontSize: 12, outline: 'none'
          }}
        />
        <button onClick={send} style={{
          background: '#00D4FF', color: '#0A0E1A', border: 'none',
          borderRadius: 6, padding: '8px 14px', cursor: 'pointer',
          fontWeight: 700, fontSize: 12
        }}>→</button>
      </div>
    </div>
  )
}


