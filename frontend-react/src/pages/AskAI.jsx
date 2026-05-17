import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import Layout from '../components/Layout.jsx'
import PageHeader from '../components/PageHeader.jsx'

export default function AskAI() {
  const { apiGet, apiPost } = useAuth()
  const [documents, setDocuments] = useState([])
  const [selectedDoc, setSelectedDoc] = useState('')
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef()

  // Load messages from localStorage — stored per document ID
  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem('askai_messages')
      return saved ? JSON.parse(saved) : {}
    } catch { return {} }
  })

  // Save to localStorage whenever messages change
  useEffect(() => {
    try {
      localStorage.setItem('askai_messages', JSON.stringify(messages))
    } catch (e) {
      console.error('localStorage save failed', e)
    }
  }, [messages])

  // Current document's messages
  const currentMessages = messages[selectedDoc] || []

  useEffect(() => {
    apiGet('/documents/').then(docs => {
      const processed = (docs || []).filter(d => d.status === 'processed')
      setDocuments(processed)
      if (processed.length > 0) setSelectedDoc(String(processed[0].id))
    })
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, selectedDoc])

  const ask = async () => {
    if (!question.trim() || !selectedDoc) return
    const q = question.trim()

    // Add user message
    setMessages(prev => ({
      ...prev,
      [selectedDoc]: [...(prev[selectedDoc] || []), { role: 'user', content: q }]
    }))
    setQuestion('')
    setLoading(true)

    const res = await apiPost(`/documents/${selectedDoc}/ask`, { question: q })

    if (res.status === 200) {
      setMessages(prev => ({
        ...prev,
        [selectedDoc]: [...(prev[selectedDoc] || []), {
          role: 'assistant',
          content: res.data.answer,
          sources: res.data.sources || []
        }]
      }))
    } else {
      setMessages(prev => ({
        ...prev,
        [selectedDoc]: [...(prev[selectedDoc] || []), {
          role: 'assistant',
          content: `✗ Error: ${res.data?.detail || 'Something went wrong'}`,
          sources: []
        }]
      }))
    }
    setLoading(false)
  }

  const clearChat = () => {
    setMessages(prev => {
      const updated = { ...prev, [selectedDoc]: [] }
      localStorage.setItem('askai_messages', JSON.stringify(updated))
      return updated
    })
  }

  const clearAllChats = () => {
    if (!window.confirm('Clear all chat history for all documents?')) return
    setMessages({})
    localStorage.removeItem('askai_messages')
  }

  const s = {
    card: {
      background: '#0F1628', border: '1px solid #1E2D4D',
      borderRadius: 10, padding: 20
    },
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
    },
    secondaryBtn: {
      background: '#1E2D4D', color: '#E2E8F0', border: 'none',
      borderRadius: 6, padding: '8px 14px', cursor: 'pointer',
      fontFamily: 'monospace', fontSize: 12, fontWeight: 700
    },
    dangerBtn: {
      background: '#FF4D6D22', color: '#FF4D6D',
      border: '1px solid #FF4D6D44', borderRadius: 6,
      padding: '8px 14px', cursor: 'pointer',
      fontFamily: 'monospace', fontSize: 12, fontWeight: 700
    }
  }

  return (
    <Layout>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <PageHeader title="◈ ASK AI" subtitle="Query your documents with AI-powered intelligence" />
        <button style={{ ...s.dangerBtn, marginTop: 8 }} onClick={clearAllChats}>
          ✕ CLEAR ALL HISTORY
        </button>
      </div>

      {documents.length === 0 ? (
        <div style={{ ...s.card, textAlign: 'center', padding: 60, borderTop: '3px solid #F6AD55' }}>
          <div style={{ fontSize: '2rem', marginBottom: 8 }}>◈</div>
          <div style={{ color: '#F6AD55', fontWeight: 700, letterSpacing: 2 }}>NO PROCESSED DOCUMENTS</div>
          <div style={{ color: '#4A5568', fontSize: 13, marginTop: 8 }}>
            Upload a PDF on the Documents page and wait for it to be processed
          </div>
        </div>
      ) : (
        <>
          {/* Document selector */}
          <div style={{ display: 'flex', gap: 12, marginBottom: 20, alignItems: 'center' }}>
            <select
              style={s.select}
              value={selectedDoc}
              onChange={e => setSelectedDoc(String(e.target.value))}>
              {documents.map(d => (
                <option key={d.id} value={String(d.id)}>
                  [{d.id}] {d.filename}
                </option>
              ))}
            </select>
            <button style={s.secondaryBtn} onClick={clearChat}>
              CLEAR CHAT
            </button>
          </div>

          {/* Chat message count */}
          {currentMessages.length > 0 && (
            <div style={{ fontSize: '0.65rem', color: '#4A5568', letterSpacing: 2, marginBottom: 8 }}>
              {Math.floor(currentMessages.length / 2)} QUESTION{currentMessages.length / 2 !== 1 ? 'S' : ''} IN HISTORY · STORED LOCALLY
            </div>
          )}

          {/* Chat window */}
          <div style={{
            ...s.card, minHeight: 400, marginBottom: 16,
            display: 'flex', flexDirection: 'column',
            maxHeight: '55vh', overflowY: 'auto'
          }}>
            {currentMessages.length === 0 && (
              <div style={{ textAlign: 'center', padding: 40, color: '#4A5568' }}>
                <div style={{ fontSize: '2rem', marginBottom: 8 }}>⚡</div>
                <div style={{ color: '#00D4FF', fontWeight: 700, marginBottom: 8, letterSpacing: 2 }}>
                  DOCUMENT LOADED
                </div>
                <div style={{ fontSize: 13 }}>Ask me anything about this document</div>
                <div style={{ fontSize: 11, marginTop: 8, color: '#1E2D4D' }}>
                  Chat history is saved automatically
                </div>
              </div>
            )}

            {currentMessages.map((m, i) => (
              <div key={i} style={{ marginBottom: 16 }}>
                {m.role === 'user' ? (
                  <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <div style={{
                      background: '#0D2035', border: '1px solid #00D4FF44',
                      borderRadius: '10px 10px 0 10px', padding: '10px 16px',
                      maxWidth: '70%', color: '#E2E8F0', fontSize: 13, lineHeight: 1.5
                    }}>
                      {m.content}
                    </div>
                  </div>
                ) : (
                  <div style={{ display: 'flex', gap: 10 }}>
                    <div style={{
                      width: 28, height: 28, borderRadius: '50%',
                      background: '#00D4FF22', border: '1px solid #00D4FF44',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 14, flexShrink: 0, marginTop: 4
                    }}>⚡</div>
                    <div style={{ maxWidth: '75%' }}>
                      <div style={{
                        background: '#0A0E1A', border: '1px solid #1E2D4D',
                        borderRadius: '10px 10px 10px 0', padding: '10px 16px',
                        color: '#E2E8F0', fontSize: 13, lineHeight: 1.6
                      }}>
                        {m.content}
                      </div>
                      {m.sources?.length > 0 && (
                        <details style={{ marginTop: 6 }}>
                          <summary style={{
                            color: '#4A5568', fontSize: 11,
                            cursor: 'pointer', userSelect: 'none'
                          }}>
                            ◈ View Sources ({m.sources.length})
                          </summary>
                          <div style={{ marginTop: 4 }}>
                            {m.sources.map((src, j) => (
                              <div key={j} style={{
                                background: '#0A0E1A', border: '1px solid #1E2D4D',
                                borderRadius: 6, padding: '6px 12px',
                                marginTop: 4, fontSize: 11,
                                display: 'flex', gap: 12, alignItems: 'center'
                              }}>
                                <span style={{ color: '#00D4FF' }}>📄 {src.source}</span>
                                <span style={{ color: '#4A5568' }}>Page {src.page}</span>
                                <span style={{ color: '#48BB78', fontWeight: 700 }}>
                                  {Math.round(src.relevance * 100)}% match
                                </span>
                              </div>
                            ))}
                          </div>
                        </details>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                <div style={{
                  width: 28, height: 28, borderRadius: '50%',
                  background: '#F6AD5522', border: '1px solid #F6AD5544',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 14
                }}>⚡</div>
                <div style={{
                  background: '#0A0E1A', border: '1px solid #1E2D4D',
                  borderRadius: '10px 10px 10px 0', padding: '10px 16px',
                  color: '#F6AD55', fontSize: 13
                }}>
                  Analyzing document...
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div style={{ display: 'flex', gap: 12 }}>
            <input
              style={s.input}
              value={question}
              onChange={e => setQuestion(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !loading && ask()}
              placeholder="Ask anything about this document..."
              disabled={loading}
            />
            <button
              style={{ ...s.btn, opacity: loading ? 0.6 : 1 }}
              onClick={ask}
              disabled={loading}>
              {loading ? '⚡...' : 'ASK →'}
            </button>
          </div>
        </>
      )}
    </Layout>
  )
}

