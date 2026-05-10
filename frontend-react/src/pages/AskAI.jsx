import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import Layout from '../components/Layout.jsx'
import PageHeader from '../components/PageHeader.jsx'

export default function AskAI() {
  const { apiGet, apiPost } = useAuth()
  const [documents, setDocuments] = useState([])
  const [selectedDoc, setSelectedDoc] = useState('')
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef()

  useEffect(() => {
    apiGet('/documents/').then(docs => {
      const processed = (docs || []).filter(d => d.status === 'processed')
      setDocuments(processed)
      if (processed.length > 0) setSelectedDoc(processed[0].id)
    })
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const ask = async () => {
    if (!question.trim() || !selectedDoc) return
    const q = question.trim()
    setMessages(prev => [...prev, { role: 'user', content: q }])
    setQuestion('')
    setLoading(true)
    const res = await apiPost(`/documents/${selectedDoc}/ask`, { question: q })
    if (res.status === 200) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res.data.answer,
        sources: res.data.sources || []
      }])
    } else {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${res.data?.detail || 'Something went wrong'}`,
        sources: []
      }])
    }
    setLoading(false)
  }

  const s = {
    card: { background: '#0F1628', border: '1px solid #1E2D4D', borderRadius: 10, padding: 20 },
    input: {
      flex: 1, background: '#0F1628', border: '1px solid #1E2D4D',
      borderRadius: 6, padding: '10px 14px', color: '#E2E8F0',
      fontFamily: 'monospace', fontSize: 13, outline: 'none'
    },
    select: {
      background: '#0F1628', border: '1px solid #1E2D4D', borderRadius: 6,
      padding: '8px 14px', color: '#E2E8F0', fontFamily: 'monospace',
      fontSize: 13, outline: 'none', flex: 1
    },
    btn: {
      background: 'linear-gradient(135deg,#00D4FF,#0088AA)', color: '#0A0E1A',
      border: 'none', borderRadius: 6, padding: '10px 20px',
      fontWeight: 700, cursor: 'pointer', fontFamily: 'monospace',
      fontSize: 13, letterSpacing: 1
    }
  }

  return (
    <Layout>
      <PageHeader title="◈ ASK AI" subtitle="Query your documents with AI-powered intelligence" />

      {documents.length === 0 ? (
        <div style={{ ...s.card, textAlign: 'center', padding: 60, borderTop: '3px solid #F6AD55' }}>
          <div style={{ fontSize: '2rem', marginBottom: 8 }}>◈</div>
          <div style={{ color: '#F6AD55', fontWeight: 700, letterSpacing: 2 }}>NO PROCESSED DOCUMENTS</div>
          <div style={{ color: '#4A5568', fontSize: 13, marginTop: 8 }}>Upload and process a PDF first</div>
        </div>
      ) : (
        <>
          {/* Doc selector */}
          <div style={{ display: 'flex', gap: 12, marginBottom: 20, alignItems: 'center' }}>
            <select style={s.select} value={selectedDoc}
              onChange={e => { setSelectedDoc(e.target.value); setMessages([]) }}>
              {documents.map(d => (
                <option key={d.id} value={d.id}>[{d.id}] {d.filename}</option>
              ))}
            </select>
            <button style={{ ...s.btn, background: '#1E2D4D', color: '#E2E8F0' }}
              onClick={() => setMessages([])}>CLEAR</button>
          </div>

          {/* Chat */}
          <div style={{ ...s.card, minHeight: 400, marginBottom: 16, display: 'flex', flexDirection: 'column' }}>
            {messages.length === 0 && (
              <div style={{ textAlign: 'center', padding: 40, color: '#4A5568' }}>
                <div style={{ color: '#00D4FF', fontWeight: 700, marginBottom: 8 }}>DOCUMENT LOADED</div>
                <div style={{ fontSize: 13 }}>Ask me anything about this document</div>
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} style={{ marginBottom: 16 }}>
                {m.role === 'user' ? (
                  <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <div style={{
                      background: '#0D2035', border: '1px solid #00D4FF44',
                      borderRadius: '10px 10px 0 10px', padding: '10px 16px',
                      maxWidth: '70%', color: '#E2E8F0', fontSize: 13
                    }}>{m.content}</div>
                  </div>
                ) : (
                  <div style={{ display: 'flex', gap: 10 }}>
                    <span style={{ color: '#00D4FF', fontSize: '1.2rem' }}>⚡</span>
                    <div>
                      <div style={{
                        background: '#0A0E1A', border: '1px solid #1E2D4D',
                        borderRadius: '10px 10px 10px 0', padding: '10px 16px',
                        color: '#E2E8F0', fontSize: 13, lineHeight: 1.6, maxWidth: '75%'
                      }}>{m.content}</div>
                      {m.sources?.length > 0 && (
                        <details style={{ marginTop: 6 }}>
                          <summary style={{ color: '#4A5568', fontSize: 11, cursor: 'pointer' }}>
                            ◈ View Sources ({m.sources.length})
                          </summary>
                          {m.sources.map((src, j) => (
                            <div key={j} style={{
                              background: '#0A0E1A', border: '1px solid #1E2D4D',
                              borderRadius: 6, padding: '6px 12px', marginTop: 4, fontSize: 11
                            }}>
                              <span style={{ color: '#00D4FF' }}>📄 {src.source}</span>
                              <span style={{ color: '#4A5568', marginLeft: 8 }}>Page {src.page}</span>
                              <span style={{ color: '#48BB78', marginLeft: 8 }}>{Math.round(src.relevance * 100)}% relevant</span>
                            </div>
                          ))}
                        </details>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div style={{ color: '#F6AD55', fontSize: 13 }}>⚡ Analyzing document...</div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div style={{ display: 'flex', gap: 12 }}>
            <input style={s.input} value={question}
              onChange={e => setQuestion(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && ask()}
              placeholder="What are the main compliance requirements in this document?" />
            <button style={s.btn} onClick={ask} disabled={loading}>ASK →</button>
          </div>
        </>
      )}
    </Layout>
  )
}




