import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import Layout from '../components/Layout.jsx'
import PageHeader from '../components/PageHeader.jsx'
import MetricCard from '../components/MetricCard.jsx'

export default function Admin() {
  const { apiGet, user } = useAuth()
  const [documents, setDocuments] = useState([])
  const [tasks, setTasks] = useState([])
  const [logs, setLogs] = useState([])

  useEffect(() => {
    Promise.all([
      apiGet('/documents/'),
      apiGet('/tasks/'),
      apiGet('/audit/', { limit: 500 })
    ]).then(([docs, tks, ls]) => {
      setDocuments(docs || [])
      setTasks(tks || [])
      setLogs(ls || [])
    })
  }, [])

  if (user?.role !== 'admin') {
    return <Layout><div style={{ color: '#FF4D6D', padding: 40 }}>✗ Access denied — Admin only</div></Layout>
  }

  const actionCounts = logs.reduce((acc, l) => {
    acc[l.action] = (acc[l.action] || 0) + 1
    return acc
  }, {})
  const total = logs.length || 1

  const ACTION_COLORS = {
    'user.login': '#48BB78', 'user.login_failed': '#FF4D6D',
    'document.upload': '#00D4FF', 'document.ask': '#F6AD55',
    'task.create': '#48BB78', 'task.update': '#F6AD55',
    'document.delete': '#FF4D6D', 'task.delete': '#FF4D6D'
  }

  const s = {
    card: { background: '#0F1628', border: '1px solid #1E2D4D', borderRadius: 10, padding: 20, marginBottom: 20 }
  }

  return (
    <Layout>
      <PageHeader title="◈ ADMIN PANEL" subtitle="System administration and overview" />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 16, marginBottom: 20 }}>
        <MetricCard label="TOTAL DOCUMENTS" value={documents.length} color="#00D4FF" />
        <MetricCard label="TOTAL TASKS" value={tasks.length} color="#F6AD55" />
        <MetricCard label="AUDIT EVENTS" value={logs.length} color="#48BB78" />
        <MetricCard label="FAILED DOCS" value={documents.filter(d => d.status === 'failed').length} color="#FF4D6D" />
      </div>

      {/* Activity breakdown */}
      <div style={{ ...s.card, borderTop: '3px solid #00D4FF' }}>
        <div style={{ fontSize: '0.65rem', color: '#4A5568', letterSpacing: 3, marginBottom: 16 }}>SYSTEM ACTIVITY BREAKDOWN</div>
        {Object.entries(actionCounts)
          .sort((a, b) => b[1] - a[1])
          .map(([action, count]) => {
            const pct = Math.round((count / total) * 100)
            const color = ACTION_COLORS[action] || '#718096'
            return (
              <div key={action} style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ color, fontSize: 12, fontWeight: 700 }}>{action}</span>
                  <span style={{ color: '#E2E8F0', fontSize: 12 }}>{count} ({pct}%)</span>
                </div>
                <div style={{ background: '#1E2D4D', borderRadius: 2, height: 4 }}>
                  <div style={{ background: color, width: `${pct}%`, height: 4, borderRadius: 2 }} />
                </div>
              </div>
            )
          })}
      </div>

      {/* Recent docs */}
      <div style={{ ...s.card, borderTop: '3px solid #F6AD55' }}>
        <div style={{ fontSize: '0.65rem', color: '#4A5568', letterSpacing: 3, marginBottom: 16 }}>RECENT DOCUMENTS</div>
        {documents.slice(-5).reverse().map(doc => {
          const statusColor = doc.status === 'processed' ? '#48BB78' : doc.status === 'failed' ? '#FF4D6D' : '#F6AD55'
          return (
            <div key={doc.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #0A0E1A', fontSize: 13 }}>
              <span style={{ color: '#E2E8F0' }}>📄 {doc.filename?.slice(0, 50)}</span>
              <span style={{ color: statusColor, fontWeight: 700 }}>{doc.status?.toUpperCase()}</span>
            </div>
          )
        })}
      </div>
    </Layout>
  )
}
