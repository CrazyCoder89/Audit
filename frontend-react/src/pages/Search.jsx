import { useState } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import Layout from '../components/Layout.jsx'
import PageHeader from '../components/PageHeader.jsx'
import StatusBadge from '../components/StatusBadge.jsx'

const CAT_COLORS = { financial: '#48BB78', legal: '#F6AD55', compliance: '#00D4FF', hr: '#9F7AEA', unknown: '#718096' }
const PRI_COLORS = { critical: '#FF4D6D', high: '#F6AD55', medium: '#00D4FF', low: '#48BB78' }

export default function Search() {
  const { apiGet } = useAuth()
  const [query, setQuery] = useState('')
  const [docs, setDocs] = useState([])
  const [tasks, setTasks] = useState([])
  const [searched, setSearched] = useState(false)

  const search = async () => {
    if (!query.trim()) return
    const [d, t] = await Promise.all([
      apiGet('/documents/search/query', { q: query }),
      apiGet('/tasks/search/query', { q: query })
    ])
    setDocs(d || [])
    setTasks(t || [])
    setSearched(true)
  }

  const highlight = (text, q, color) => {
    if (!text || !q) return text
    const parts = text.split(new RegExp(`(${q})`, 'gi'))
    return parts.map((part, i) =>
      part.toLowerCase() === q.toLowerCase()
        ? <mark key={i} style={{ background: `${color}22`, color, padding: '0 2px' }}>{part}</mark>
        : part
    )
  }

  const s = {
    card: { background: '#0F1628', border: '1px solid #1E2D4D', borderRadius: 10, padding: 20 },
    input: {
      flex: 1, background: '#0F1628', border: '2px solid #1E2D4D', borderRadius: 8,
      padding: '12px 16px', color: '#E2E8F0', fontFamily: 'monospace',
      fontSize: 14, outline: 'none'
    },
    btn: {
      background: 'linear-gradient(135deg,#00D4FF,#0088AA)', color: '#0A0E1A',
      border: 'none', borderRadius: 8, padding: '12px 24px',
      fontWeight: 700, cursor: 'pointer', fontFamily: 'monospace',
      fontSize: 13, letterSpacing: 1
    },
    resultCard: (color) => ({
      background: '#0A0E1A', border: '1px solid #1E2D4D',
      borderRadius: 8, padding: '12px 16px', marginBottom: 8,
      borderLeft: `3px solid ${color}`
    })
  }

  return (
    <Layout>
      <PageHeader title="◈ SEARCH" subtitle="Search across all documents and tasks" />

      <div style={{ display: 'flex', gap: 12, marginBottom: 32 }}>
        <input style={s.input} value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && search()}
          placeholder="Search documents, tasks, categories, priorities..." />
        <button style={s.btn} onClick={search}>SEARCH →</button>
      </div>

      {!searched ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: '#4A5568' }}>
          <div style={{ fontSize: '3rem', marginBottom: 12 }}>◈</div>
          <div style={{ letterSpacing: 2 }}>TYPE TO SEARCH ACROSS DOCUMENTS AND TASKS</div>
        </div>
      ) : (
        <>
          <div style={{ color: '#4A5568', fontSize: 12, letterSpacing: 2, marginBottom: 20 }}>
            {docs.length + tasks.length} RESULTS — {docs.length} DOCUMENTS · {tasks.length} TASKS
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            {/* Documents */}
            <div>
              <div style={{ fontSize: '0.7rem', color: '#00D4FF', letterSpacing: 3, marginBottom: 10 }}>
                ▪ DOCUMENTS ({docs.length})
              </div>
              {docs.length === 0
                ? <div style={{ ...s.card, color: '#4A5568', textAlign: 'center' }}>No documents found</div>
                : docs.map(d => (
                  <div key={d.id} style={s.resultCard(CAT_COLORS[d.category] || '#718096')}>
                    <div style={{ color: '#E2E8F0', fontSize: 13, fontWeight: 600, marginBottom: 6 }}>
                      📄 {highlight(d.filename, query, '#00D4FF')}
                    </div>
                    <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                      <span style={{ color: CAT_COLORS[d.category], fontSize: 11, fontWeight: 700 }}>{d.category?.toUpperCase()}</span>
                      <StatusBadge status={d.status} />
                      <span style={{ color: '#4A5568', fontSize: 11 }}>{Math.round(d.file_size / 1024)} KB</span>
                    </div>
                  </div>
                ))}
            </div>

            {/* Tasks */}
            <div>
              <div style={{ fontSize: '0.7rem', color: '#F6AD55', letterSpacing: 3, marginBottom: 10 }}>
                ▪ TASKS ({tasks.length})
              </div>
              {tasks.length === 0
                ? <div style={{ ...s.card, color: '#4A5568', textAlign: 'center' }}>No tasks found</div>
                : tasks.map(t => (
                  <div key={t.id} style={s.resultCard(PRI_COLORS[t.priority] || '#718096')}>
                    <div style={{ color: '#E2E8F0', fontSize: 13, fontWeight: 600, marginBottom: 4 }}>
                      {highlight(t.title, query, '#F6AD55')}
                    </div>
                    {t.description && (
                      <div style={{ color: '#4A5568', fontSize: 12, marginBottom: 6 }}>
                        {highlight(t.description.slice(0, 80), query, '#F6AD55')}
                        {t.description.length > 80 ? '...' : ''}
                      </div>
                    )}
                    <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                      <span style={{ color: PRI_COLORS[t.priority], fontSize: 11, fontWeight: 700 }}>{t.priority?.toUpperCase()}</span>
                      <StatusBadge status={t.status} />
                      {t.deadline && <span style={{ color: '#4A5568', fontSize: 11 }}>⏰ {t.deadline.slice(0, 10)}</span>}
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </>
      )}
    </Layout>
  )
}

