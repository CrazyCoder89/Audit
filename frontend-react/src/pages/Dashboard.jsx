import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import Layout from '../components/Layout.jsx'
import PageHeader from '../components/PageHeader.jsx'
import MetricCard from '../components/MetricCard.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis,
  LineChart, Line, Tooltip, ResponsiveContainer
} from 'recharts'
import axios from 'axios'
const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const COLORS = {
  pending: '#F6AD55', in_progress: '#00D4FF',
  completed: '#48BB78', overdue: '#FF4D6D',
  financial: '#48BB78', legal: '#F6AD55',
  compliance: '#00D4FF', hr: '#9F7AEA', unknown: '#718096'
}

const ACTION_COLORS = {
  'user.login': '#48BB78', 'user.register': '#00D4FF',
  'user.login_failed': '#FF4D6D', 'document.upload': '#00D4FF',
  'document.ask': '#F6AD55', 'document.view': '#718096',
  'document.delete': '#FF4D6D', 'task.create': '#48BB78',
  'task.update': '#F6AD55', 'task.delete': '#FF4D6D',
  'document.download': '#9F7AEA'
}

export default function Dashboard() {
  const { apiGet, user, authHeaders } = useAuth()
  const [documents, setDocuments] = useState([])
  const [tasks, setTasks] = useState([])
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(false)

  const fetchAll = async () => {
    const [docs, tks, ls] = await Promise.all([
      apiGet('/documents/'),
      apiGet('/tasks/'),
      apiGet('/audit/', { limit: 50 })
    ])
    setDocuments(docs || [])
    setTasks(tks || [])
    setLogs(ls || [])
    setLoading(false)
  }

  const downloadReport = async () => {
  try {
    const res = await axios.get('${BASE}/reports/compliance',
      { headers: authHeaders(), responseType: 'blob' }
    )
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `compliance_report_${new Date().toISOString().slice(0,10)}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error('Report generation failed', e)
    alert('Failed to generate report. Make sure you are logged in as Admin or Auditor.')
  }
}
  useEffect(() => { fetchAll() }, [])

  useEffect(() => {
    if (!autoRefresh) return
    const interval = setInterval(fetchAll, 30000)
    return () => clearInterval(interval)
  }, [autoRefresh])

  // ── Computed stats ──────────────────────────────────────────────────────
  const totalDocs = documents.length
  const processedDocs = documents.filter(d => d.status === 'processed').length
  const totalTasks = tasks.length
  const completedTasks = tasks.filter(t => t.status === 'completed').length
  const overdueTasks = tasks.filter(t => t.status === 'overdue').length
  const pendingTasks = tasks.filter(t => t.status === 'pending').length
  const inProgressTasks = tasks.filter(t => t.status === 'in_progress').length

  // Compliance score
  const docScore = totalDocs > 0 ? (processedDocs / totalDocs) * 40 : 0
  const taskScore = totalTasks > 0 ? (completedTasks / totalTasks) * 40 : 0
  const overduePenalty = Math.min(overdueTasks * 5, 20)
  const complianceScore = Math.max(0, Math.min(100, Math.round(docScore + taskScore + 20 - overduePenalty)))
  const scoreColor = complianceScore >= 80 ? '#48BB78' : complianceScore >= 60 ? '#F6AD55' : '#FF4D6D'
  const scoreLabel = complianceScore >= 80 ? 'COMPLIANT' : complianceScore >= 60 ? 'AT RISK' : 'NON-COMPLIANT'

  // Chart data
  const taskPieData = [
    { name: 'Completed', value: completedTasks },
    { name: 'In Progress', value: inProgressTasks },
    { name: 'Pending', value: pendingTasks },
    { name: 'Overdue', value: overdueTasks },
  ].filter(d => d.value > 0)

  const catCounts = documents.reduce((acc, d) => {
    acc[d.category] = (acc[d.category] || 0) + 1
    return acc
  }, {})
  const catBarData = Object.entries(catCounts).map(([name, count]) => ({ name, count }))

  const dateCounts = logs.reduce((acc, l) => {
    const date = l.created_at?.slice(0, 10)
    if (date) acc[date] = (acc[date] || 0) + 1
    return acc
  }, {})
  const lineData = Object.entries(dateCounts)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, count]) => ({ date: date.slice(5), count }))

  // Recent docs
  const recentDocs = [...documents]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 5)

  // Upcoming deadlines
  const now = new Date()
  const upcomingTasks = tasks
    .filter(t => t.deadline && t.status !== 'completed')
    .sort((a, b) => new Date(a.deadline) - new Date(b.deadline))
    .slice(0, 5)

  const s = {
    grid2: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 },
    grid3: { display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginBottom: 20 },
    grid4: { display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 16, marginBottom: 20 },
    card: {
      background: '#0F1628', border: '1px solid #1E2D4D',
      borderRadius: 10, padding: 20
    },
    cardTitle: { fontSize: '0.65rem', color: '#4A5568', letterSpacing: 3, marginBottom: 16 },
  }

  if (loading) return (
    <Layout>
      <div style={{ color: '#00D4FF', textAlign: 'center', paddingTop: 100, fontFamily: 'monospace' }}>
        Loading dashboard...
      </div>
    </Layout>
  )

  return (
    <Layout>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
          <PageHeader title="◈ DASHBOARD" subtitle="Real-time compliance intelligence overview" />
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 8, flexWrap: 'wrap' }}>
            <label style={{ color: '#4A5568', fontSize: 12, fontFamily: 'monospace', cursor: 'pointer' }}>
              <input type="checkbox" checked={autoRefresh}
                onChange={e => setAutoRefresh(e.target.checked)}
                style={{ marginRight: 6 }} />
              AUTO REFRESH
            </label>
            <button onClick={fetchAll} style={{
              background: '#1E2D4D', border: 'none', borderRadius: 6,
              color: '#00D4FF', padding: '6px 14px', cursor: 'pointer',
              fontFamily: 'monospace', fontSize: 12
            }}>↻ REFRESH</button>
            <button onClick={downloadReport} style={{
              background: 'linear-gradient(135deg,#00D4FF,#0088AA)',
              color: '#0A0E1A', border: 'none', borderRadius: 6,
              padding: '7px 16px', cursor: 'pointer',
              fontFamily: 'monospace', fontSize: 12, fontWeight: 700, letterSpacing: 1
            }}>⬇ COMPLIANCE REPORT</button>
          </div>
        </div>

      {/* Top row — compliance score + metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr 1fr 1fr 1fr', gap: 16, marginBottom: 20 }}>
        {/* Compliance Score */}
        <div style={{ ...s.card, borderTop: `3px solid ${scoreColor}`, display: 'flex', alignItems: 'center', gap: 20 }}>
          <svg viewBox="0 0 36 36" width={80} height={80}>
            <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none" stroke="#1E2D4D" strokeWidth="3" />
            <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              fill="none" stroke={scoreColor} strokeWidth="3"
              strokeDasharray={`${complianceScore}, 100`} strokeLinecap="round" />
            <text x="18" y="20.5" textAnchor="middle"
              style={{ fontSize: 7, fontFamily: 'monospace', fill: scoreColor, fontWeight: 700 }}>
              {complianceScore}%
            </text>
          </svg>
          <div>
            <div style={{ fontSize: '0.65rem', color: '#4A5568', letterSpacing: 3 }}>COMPLIANCE SCORE</div>
            <div style={{ color: scoreColor, fontWeight: 700, fontSize: '1.1rem', marginTop: 4, letterSpacing: 2 }}>
              {scoreLabel}
            </div>
            <div style={{ color: '#4A5568', fontSize: '0.65rem', marginTop: 2 }}>
              {overdueTasks} overdue · {documents.filter(d => d.status === 'failed').length} failed
            </div>
          </div>
        </div>

        <MetricCard label="DOCUMENTS" value={totalDocs} delta={`${processedDocs} processed`} color="#00D4FF" />
        <MetricCard label="TOTAL TASKS" value={totalTasks} delta={`${pendingTasks} pending`} color="#F6AD55" />
        <MetricCard label="COMPLETED" value={completedTasks} delta="tasks done" color="#48BB78" />
        <MetricCard label="OVERDUE" value={overdueTasks} delta="need attention" color={overdueTasks > 0 ? '#FF4D6D' : '#48BB78'} />
      </div>

      {/* Charts row */}
      <div style={s.grid3}>
        {/* Task Donut */}
        <div style={{ ...s.card, borderTop: '3px solid #00D4FF' }}>
          <div style={s.cardTitle}>TASK STATUS</div>
          {taskPieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={taskPieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80}
                  dataKey="value" paddingAngle={2}>
                  {taskPieData.map((entry, i) => (
                    <Cell key={i} fill={COLORS[entry.name.toLowerCase().replace(' ', '_')] || '#718096'} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: '#0F1628', border: '1px solid #1E2D4D', borderRadius: 6, fontFamily: 'monospace', fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          ) : <div style={{ color: '#4A5568', textAlign: 'center', paddingTop: 60 }}>No tasks yet</div>}
        </div>

        {/* Category Bar */}
        <div style={{ ...s.card, borderTop: '3px solid #F6AD55' }}>
          <div style={s.cardTitle}>DOCUMENT CATEGORIES</div>
          {catBarData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={catBarData}>
                <XAxis dataKey="name" tick={{ fill: '#4A5568', fontSize: 10, fontFamily: 'monospace' }} />
                <YAxis tick={{ fill: '#4A5568', fontSize: 10 }} />
                <Tooltip contentStyle={{ background: '#0F1628', border: '1px solid #1E2D4D', borderRadius: 6, fontFamily: 'monospace', fontSize: 12 }} />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {catBarData.map((entry, i) => (
                    <Cell key={i} fill={COLORS[entry.name] || '#718096'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : <div style={{ color: '#4A5568', textAlign: 'center', paddingTop: 60 }}>No documents yet</div>}
        </div>

        {/* Activity Line */}
        <div style={{ ...s.card, borderTop: '3px solid #48BB78' }}>
          <div style={s.cardTitle}>ACTIVITY TIMELINE</div>
          {lineData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={lineData}>
                <XAxis dataKey="date" tick={{ fill: '#4A5568', fontSize: 9, fontFamily: 'monospace' }} />
                <YAxis tick={{ fill: '#4A5568', fontSize: 10 }} />
                <Tooltip contentStyle={{ background: '#0F1628', border: '1px solid #1E2D4D', borderRadius: 6, fontFamily: 'monospace', fontSize: 12 }} />
                <Line type="monotone" dataKey="count" stroke="#00D4FF" strokeWidth={2}
                  dot={{ fill: '#00D4FF', r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : <div style={{ color: '#4A5568', textAlign: 'center', paddingTop: 60 }}>No activity yet</div>}
        </div>
      </div>

      {/* Bottom row */}
      <div style={s.grid3}>
        {/* Task Progress */}
        <div style={{ ...s.card, borderTop: '3px solid #F6AD55' }}>
          <div style={s.cardTitle}>TASK PROGRESS</div>
          {[
            { label: 'COMPLETED', count: completedTasks, color: '#48BB78' },
            { label: 'IN PROGRESS', count: inProgressTasks, color: '#00D4FF' },
            { label: 'PENDING', count: pendingTasks, color: '#F6AD55' },
            { label: 'OVERDUE', count: overdueTasks, color: '#FF4D6D' },
          ].map(({ label, count, color }) => {
            const pct = totalTasks > 0 ? Math.round((count / totalTasks) * 100) : 0
            return (
              <div key={label} style={{ marginBottom: 14 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                  <span style={{ color: '#E2E8F0', fontSize: '0.75rem' }}>{label}</span>
                  <span style={{ color, fontSize: '0.75rem', fontWeight: 700 }}>{count} ({pct}%)</span>
                </div>
                <div style={{ background: '#1E2D4D', borderRadius: 3, height: 6 }}>
                  <div style={{ background: `linear-gradient(90deg,${color},${color}88)`, width: `${pct}%`, height: 6, borderRadius: 3 }} />
                </div>
              </div>
            )
          })}
        </div>

        {/* Upcoming Deadlines */}
        <div style={{ ...s.card, borderTop: '3px solid #9F7AEA' }}>
          <div style={s.cardTitle}>UPCOMING DEADLINES</div>
          {upcomingTasks.length === 0
            ? <div style={{ color: '#4A5568', fontSize: 13 }}>No upcoming deadlines</div>
            : upcomingTasks.map(t => {
              const dl = new Date(t.deadline)
              const daysLeft = Math.round((dl - now) / (1000 * 60 * 60 * 24))
              const dlColor = daysLeft < 0 ? '#FF4D6D' : daysLeft <= 3 ? '#F6AD55' : '#48BB78'
              return (
                <div key={t.id} style={{ display: 'flex', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid #0A0E1A' }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: dlColor, marginRight: 10, flexShrink: 0 }} />
                  <div style={{ flex: 1, overflow: 'hidden' }}>
                    <div style={{ color: '#E2E8F0', fontSize: '0.75rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{t.title}</div>
                    <div style={{ color: '#4A5568', fontSize: '0.65rem' }}>{t.deadline?.slice(0, 10)}</div>
                  </div>
                  <div style={{ color: dlColor, fontSize: '0.65rem', fontWeight: 700, marginLeft: 8, whiteSpace: 'nowrap' }}>
                    {daysLeft < 0 ? `${Math.abs(daysLeft)}d overdue` : daysLeft === 0 ? 'TODAY' : `${daysLeft}d left`}
                  </div>
                </div>
              )
            })}
        </div>

        {/* Recent Documents */}
        <div style={{ ...s.card, borderTop: '3px solid #00D4FF' }}>
          <div style={s.cardTitle}>RECENT DOCUMENTS</div>
          {recentDocs.length === 0
            ? <div style={{ color: '#4A5568', fontSize: 13 }}>No documents yet</div>
            : recentDocs.map(d => {
              const catColor = COLORS[d.category] || '#718096'
              const statusColor = d.status === 'processed' ? '#48BB78' : d.status === 'failed' ? '#FF4D6D' : '#F6AD55'
              return (
                <div key={d.id} style={{ padding: '8px 0', borderBottom: '1px solid #0A0E1A' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ color: '#E2E8F0', fontSize: '0.75rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '70%' }}>
                      📄 {d.filename}
                    </div>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: statusColor, flexShrink: 0 }} />
                  </div>
                  <div style={{ display: 'flex', gap: 8, marginTop: 3 }}>
                    <span style={{ color: catColor, fontSize: '0.65rem', fontWeight: 700 }}>{d.category?.toUpperCase()}</span>
                    <span style={{ color: '#4A5568', fontSize: '0.65rem' }}>{d.created_at?.slice(0, 10)}</span>
                  </div>
                </div>
              )
            })}
        </div>
      </div>

      {/* Live Activity Feed */}
      <div style={{ ...s.card, borderTop: '3px solid #48BB78' }}>
        <div style={s.cardTitle}>LIVE ACTIVITY FEED</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
          {logs.slice(0, 10).map(log => {
            const color = ACTION_COLORS[log.action] || '#718096'
            const resource = log.resource_type && log.resource_id
              ? `${log.resource_type}#${log.resource_id}` : log.resource_type || ''
            return (
              <div key={log.id} style={{
                display: 'flex', alignItems: 'center', padding: '7px 12px',
                background: '#0A0E1A', borderRadius: 6, borderLeft: `3px solid ${color}`
              }}>
                <div style={{ flex: 1 }}>
                  <span style={{ color: '#E2E8F0', fontSize: '0.75rem', fontWeight: 600 }}>{log.action}</span>
                  {resource && <span style={{ color: '#4A5568', fontSize: '0.7rem', marginLeft: 6 }}>{resource}</span>}
                </div>
                <div style={{ color: '#4A5568', fontSize: '0.65rem', whiteSpace: 'nowrap' }}>
                  {log.created_at?.slice(11, 16)}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      <div style={{ textAlign: 'right', color: '#1E2D4D', fontSize: '0.65rem', letterSpacing: 2, marginTop: 12 }}>
        LAST UPDATED: {new Date().toLocaleString()}
      </div>
    </Layout>
  )
}




