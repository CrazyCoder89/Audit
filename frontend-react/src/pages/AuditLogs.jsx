import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import Layout from '../components/Layout.jsx'
import PageHeader from '../components/PageHeader.jsx'
import axios from 'axios'

const ACTION_COLORS = {
  'user.login': '#48BB78', 'user.login_failed': '#FF4D6D',
  'user.register': '#00D4FF', 'document.upload': '#00D4FF',
  'document.view': '#718096', 'document.ask': '#F6AD55',
  'document.delete': '#FF4D6D', 'document.download': '#9F7AEA',
  'task.create': '#48BB78', 'task.update': '#F6AD55', 'task.delete': '#FF4D6D',
}

export default function AuditLogs() {
  const { apiGet, authHeaders, user } = useAuth()
  const [logs, setLogs] = useState([])
  const [filterAction, setFilterAction] = useState('all')
  const [filterResource, setFilterResource] = useState('all')
  const [limit, setLimit] = useState(50)

  useEffect(() => {
    const params = { limit }
    if (filterAction !== 'all') params.action = filterAction
    if (filterResource !== 'all') params.resource_type = filterResource
    apiGet('/audit/', params).then(data => setLogs(data || []))
  }, [filterAction, filterResource, limit])

  const exportCSV = async () => {
    const res = await axios.get('http://localhost:8000/audit/export',
      { headers: authHeaders(), responseType: 'blob' })
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = 'audit_logs.csv'
    a.click()
  }

  if (!['admin', 'auditor'].includes(user?.role)) {
    return <Layout><div style={{ color: '#FF4D6D', padding: 40 }}>✗ Access denied</div></Layout>
  }

  const s = {
    card: { background: '#0F1628', border: '1px solid #1E2D4D', borderRadius: 10, padding: 20 },
    select: {
      background: '#0F1628', border: '1px solid #1E2D4D', borderRadius: 6,
      padding: '7px 12px', color: '#E2E8F0', fontFamily: 'monospace',
      fontSize: 12, outline: 'none'
    }
  }

  return (
    <Layout>
      <PageHeader title="◈ AUDIT LOGS" subtitle="Complete compliance trail of all system actions" />

      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap', alignItems: 'center' }}>
        <select style={s.select} value={filterAction} onChange={e => setFilterAction(e.target.value)}>
          <option value="all">All Actions</option>
          {['user.login', 'user.login_failed', 'user.register', 'document.upload',
            'document.view', 'document.ask', 'document.download', 'document.delete',
            'task.create', 'task.update', 'task.delete'].map(a => (
            <option key={a} value={a}>{a}</option>
          ))}
        </select>
        <select style={s.select} value={filterResource} onChange={e => setFilterResource(e.target.value)}>
          <option value="all">All Resources</option>
          {['user', 'document', 'task'].map(r => <option key={r} value={r}>{r}</option>)}
        </select>
        <select style={s.select} value={limit} onChange={e => setLimit(Number(e.target.value))}>
          {[25, 50, 100, 200].map(l => <option key={l} value={l}>Show {l}</option>)}
        </select>
        {user?.role === 'admin' && (
          <button onClick={exportCSV} style={{
            background: 'linear-gradient(135deg,#00D4FF,#0088AA)', color: '#0A0E1A',
            border: 'none', borderRadius: 6, padding: '7px 16px', cursor: 'pointer',
            fontFamily: 'monospace', fontSize: 12, fontWeight: 700, letterSpacing: 1
          }}>⬇ EXPORT CSV</button>
        )}
        <span style={{ color: '#4A5568', fontSize: 12, marginLeft: 'auto' }}>
          {logs.length} records
        </span>
      </div>

      {/* Table */}
      <div style={s.card}>
        {/* Header */}
        <div style={{
          display: 'grid', gridTemplateColumns: '0.5fr 1fr 1.5fr 1fr 1fr 1fr',
          padding: '8px 16px', fontSize: '0.65rem', color: '#4A5568',
          letterSpacing: 2, borderBottom: '1px solid #1E2D4D', marginBottom: 8
        }}>
          {['ID', 'USER', 'ACTION', 'RESOURCE', 'IP', 'TIMESTAMP'].map(h => (
            <span key={h}>{h}</span>
          ))}
        </div>

        {logs.map(log => {
          const color = ACTION_COLORS[log.action] || '#718096'
          const resource = log.resource_type && log.resource_id
            ? `${log.resource_type}#${log.resource_id}` : log.resource_type || '—'
          return (
            <div key={log.id} style={{
              display: 'grid', gridTemplateColumns: '0.5fr 1fr 1.5fr 1fr 1fr 1fr',
              padding: '10px 16px', background: '#0A0E1A', borderRadius: 6,
              marginBottom: 4, borderLeft: `3px solid ${color}`, fontSize: 12
            }}>
              <span style={{ color: '#4A5568' }}>#{log.id}</span>
              <span style={{ color: '#E2E8F0' }}>user:{log.user_id || 'sys'}</span>
              <span style={{ color, fontWeight: 700 }}>{log.action}</span>
              <span style={{ color: '#4A5568' }}>{resource}</span>
              <span style={{ color: '#4A5568' }}>{log.ip_address || '—'}</span>
              <span style={{ color: '#4A5568', fontFamily: 'monospace' }}>
                {log.created_at?.slice(0, 19).replace('T', ' ')}
              </span>
            </div>
          )
        })}

        {logs.length === 0 && (
          <div style={{ textAlign: 'center', color: '#4A5568', padding: '40px 0' }}>No logs found</div>
        )}
      </div>
    </Layout>
  )
}



