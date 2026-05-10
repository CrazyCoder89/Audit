import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import Layout from '../components/Layout.jsx'
import PageHeader from '../components/PageHeader.jsx'
import axios from 'axios'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Cell
} from 'recharts'

const SEVERITY_COLORS = { CRITICAL: '#FF4D6D', HIGH: '#F6AD55', MEDIUM: '#00D4FF', LOW: '#48BB78' }
const SEVERITY_ICONS = { CRITICAL: '🔴', HIGH: '🟠', MEDIUM: '🟡', LOW: '🟢' }

export default function Analytics() {
  const { apiGet, authHeaders, user } = useAuth()
  const [tab, setTab] = useState('heatmap')
  const [activityData, setActivityData] = useState(null)
  const [riskData, setRiskData] = useState(null)
  const [anomalyData, setAnomalyData] = useState(null)
  const [documents, setDocuments] = useState([])
  const [selectedDocId, setSelectedDocId] = useState('')
  const [suggestions, setSuggestions] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!['admin', 'auditor'].includes(user?.role)) return
    apiGet('/analytics/user-activity').then(setActivityData)
    apiGet('/documents/').then(docs => {
      const processed = (docs || []).filter(d => d.status === 'processed')
      setDocuments(processed)
      if (processed.length > 0) setSelectedDocId(processed[0].id)
    })
  }, [])

  const runRisk = async () => {
    setLoading(true)
    setRiskData(await apiGet('/analytics/document-risk'))
    setLoading(false)
  }

  const runAnomaly = async () => {
    setLoading(true)
    setAnomalyData(await apiGet('/analytics/anomalies'))
    setLoading(false)
  }

  const runSuggestions = async () => {
    if (!selectedDocId) return
    setLoading(true)
    try {
      const res = await axios.post(
        `http://localhost:8000/analytics/suggest-tasks/${selectedDocId}`, {},
        { headers: authHeaders() }
      )
      setSuggestions(res.data)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  const createTask = async (task, days) => {
    const deadline = new Date(Date.now() + days * 86400000).toISOString()
    await axios.post('http://localhost:8000/tasks/',
      { title: task.title, description: task.description, priority: task.priority, deadline, document_id: parseInt(selectedDocId) },
      { headers: authHeaders() }
    )
    alert('✓ Task created successfully')
  }

  if (!['admin', 'auditor'].includes(user?.role)) {
    return <Layout><div style={{ color: '#FF4D6D', padding: 40 }}>✗ Access denied</div></Layout>
  }

  const s = {
    card: { background: '#0F1628', border: '1px solid #1E2D4D', borderRadius: 10, padding: 20, marginBottom: 16 },
    tab: (active) => ({
      padding: '10px 20px', cursor: 'pointer', fontFamily: 'monospace',
      fontSize: 12, fontWeight: 700, letterSpacing: 1, border: 'none',
      background: active ? '#00D4FF22' : 'transparent',
      color: active ? '#00D4FF' : '#4A5568',
      borderBottom: active ? '2px solid #00D4FF' : '2px solid transparent'
    }),
    btn: {
      background: 'linear-gradient(135deg,#00D4FF,#0088AA)', color: '#0A0E1A',
      border: 'none', borderRadius: 6, padding: '8px 20px',
      fontWeight: 700, cursor: 'pointer', fontFamily: 'monospace', fontSize: 12
    }
  }

  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
  const heatmap = activityData?.heatmap || []
  const maxVal = Math.max(...heatmap.flat(), 1)

  return (
    <Layout>
      <PageHeader title="◈ ANALYTICS" subtitle="User activity intelligence and document risk assessment" />

      {/* Tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid #1E2D4D', marginBottom: 24 }}>
        {[
          ['heatmap', '◈ USER ACTIVITY'],
          ['risk', '◈ DOCUMENT RISK'],
          ['suggestions', '◈ AI TASK SUGGESTIONS'],
          ['anomaly', '◈ ANOMALY DETECTION']
        ].map(([key, label]) => (
          <button key={key} style={s.tab(tab === key)} onClick={() => setTab(key)}>{label}</button>
        ))}
      </div>

      {/* Tab 1 — Activity Heatmap */}
      {tab === 'heatmap' && activityData && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 16, marginBottom: 20 }}>
            {[
              ['TOTAL ACTIONS (30D)', activityData.total_actions_30d, '#00D4FF'],
              ['MOST ACTIVE', activityData.most_active_user?.name || '—', '#F6AD55'],
              ['PEAK HOUR', activityData.peak_hour_label, '#48BB78'],
              ['USERS TRACKED', activityData.user_activity?.length, '#9F7AEA'],
            ].map(([label, value, color]) => (
              <div key={label} style={{ ...s.card, borderTop: `3px solid ${color}` }}>
                <div style={{ fontSize: '0.65rem', color: '#4A5568', letterSpacing: 3, marginBottom: 8 }}>{label}</div>
                <div style={{ fontSize: '1.5rem', fontWeight: 700, color, fontFamily: 'monospace' }}>{value}</div>
              </div>
            ))}
          </div>

          {/* Heatmap grid */}
          <div style={s.card}>
            <div style={{ fontSize: '0.65rem', color: '#4A5568', letterSpacing: 3, marginBottom: 16 }}>ACTIVITY HEATMAP — LAST 30 DAYS</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'auto repeat(24,1fr)', gap: 3 }}>
              <div />
              {Array.from({ length: 24 }, (_, h) => (
                <div key={h} style={{ color: '#4A5568', fontSize: 9, textAlign: 'center' }}>
                  {h % 6 === 0 ? `${h}h` : ''}
                </div>
              ))}
              {heatmap.map((row, di) => (
                <>
                  <div key={`d${di}`} style={{ color: '#4A5568', fontSize: 10, paddingRight: 6, display: 'flex', alignItems: 'center' }}>
                    {days[di]}
                  </div>
                  {row.map((val, hi) => {
                    const intensity = val / maxVal
                    return (
                      <div key={`${di}-${hi}`} title={`${days[di]} ${hi}:00 — ${val} actions`} style={{
                        height: 14, borderRadius: 2,
                        background: val === 0 ? '#0A0E1A' : `rgba(0,212,255,${0.1 + intensity * 0.9})`
                      }} />
                    )
                  })}
                </>
              ))}
            </div>
          </div>

          {/* User breakdown */}
          <div style={s.card}>
            <div style={{ fontSize: '0.65rem', color: '#4A5568', letterSpacing: 3, marginBottom: 16 }}>USER ACTIVITY BREAKDOWN</div>
            {activityData.user_activity?.map(u => {
              const maxA = Math.max(...activityData.user_activity.map(x => x.total_actions), 1)
              const pct = Math.round((u.total_actions / maxA) * 100)
              const top = Object.entries(u.action_breakdown || {}).sort((a, b) => b[1] - a[1]).slice(0, 3)
              return (
                <div key={u.user_id} style={{ marginBottom: 14 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                    <span style={{ color: '#E2E8F0', fontSize: 13 }}>👤 {u.name}</span>
                    <span style={{ color: '#00D4FF', fontSize: 13, fontWeight: 700 }}>{u.total_actions} actions</span>
                  </div>
                  <div style={{ background: '#1E2D4D', borderRadius: 3, height: 5, marginBottom: 4 }}>
                    <div style={{ background: 'linear-gradient(90deg,#00D4FF,#0088AA)', width: `${pct}%`, height: 5, borderRadius: 3 }} />
                  </div>
                  <div style={{ color: '#4A5568', fontSize: 11 }}>
                    {top.map(([a, c]) => `${a}: ${c}`).join(' · ')}
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}

      {/* Tab 2 — Risk */}
      {tab === 'risk' && (
        <>
          <div style={{ ...s.card, borderLeft: '3px solid #F6AD55', marginBottom: 20 }}>
            <div style={{ color: '#F6AD55', fontWeight: 700, fontSize: 12, letterSpacing: 2 }}>AI-POWERED RISK ASSESSMENT</div>
            <div style={{ color: '#4A5568', fontSize: 13, marginTop: 4 }}>Each document scored 0-100 by Groq AI based on category and compliance factors</div>
          </div>
          {!riskData ? (
            <button style={s.btn} onClick={runRisk} disabled={loading}>
              {loading ? '⚡ ANALYZING...' : '⚡ RUN RISK ANALYSIS'}
            </button>
          ) : (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,1fr)', gap: 12, marginBottom: 20 }}>
                {[
                  ['AVG SCORE', riskData.summary?.avg_risk_score, '#F6AD55'],
                  ['CRITICAL', riskData.summary?.critical, '#FF4D6D'],
                  ['HIGH', riskData.summary?.high, '#F6AD55'],
                  ['MEDIUM', riskData.summary?.medium, '#00D4FF'],
                  ['LOW', riskData.summary?.low, '#48BB78'],
                ].map(([label, value, color]) => (
                  <div key={label} style={{ ...s.card, borderTop: `3px solid ${color}`, textAlign: 'center' }}>
                    <div style={{ fontSize: '0.6rem', color: '#4A5568', letterSpacing: 2, marginBottom: 6 }}>{label}</div>
                    <div style={{ fontSize: '1.8rem', fontWeight: 700, color, fontFamily: 'monospace' }}>{value}</div>
                  </div>
                ))}
              </div>

              {/* Bar chart */}
              {riskData.documents?.length > 0 && (
                <div style={{ ...s.card, marginBottom: 20 }}>
                  <div style={{ fontSize: '0.65rem', color: '#4A5568', letterSpacing: 3, marginBottom: 16 }}>RISK SCORES</div>
                  <ResponsiveContainer width="100%" height={Math.max(200, riskData.documents.length * 35)}>
                    <BarChart data={riskData.documents} layout="vertical">
                      <XAxis type="number" domain={[0, 100]} tick={{ fill: '#4A5568', fontSize: 10 }} />
                      <YAxis type="category" dataKey="filename" tick={{ fill: '#4A5568', fontSize: 9 }}
                        width={150} tickFormatter={v => v.length > 20 ? v.slice(0, 20) + '...' : v} />
                      <Tooltip contentStyle={{ background: '#0F1628', border: '1px solid #1E2D4D', borderRadius: 6, fontFamily: 'monospace', fontSize: 11 }} />
                      <Bar dataKey="risk_score" radius={[0, 4, 4, 0]}>
                        {riskData.documents.map((d, i) => (
                          <Cell key={i} fill={SEVERITY_COLORS[d.risk_level] || '#718096'} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {riskData.documents?.map(doc => {
                const color = SEVERITY_COLORS[doc.risk_level] || '#718096'
                return (
                  <div key={doc.document_id} style={{ ...s.card, borderLeft: `4px solid ${color}` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                      <div>
                        <div style={{ color: '#E2E8F0', fontWeight: 600 }}>📄 {doc.filename}</div>
                        <div style={{ color: '#4A5568', fontSize: 11, marginTop: 2 }}>
                          {doc.category?.toUpperCase()} · {doc.status?.toUpperCase()}
                        </div>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '1.8rem', fontWeight: 700, color, fontFamily: 'monospace', lineHeight: 1 }}>{doc.risk_score}</div>
                        <span style={{ background: `${color}22`, color, fontSize: '0.6rem', padding: '2px 8px', borderRadius: 4, fontWeight: 700, border: `1px solid ${color}44` }}>
                          {doc.risk_level}
                        </span>
                      </div>
                    </div>
                    <div style={{ background: '#1E2D4D', borderRadius: 3, height: 4, marginBottom: 10 }}>
                      <div style={{ background: `linear-gradient(90deg,${color},${color}88)`, width: `${doc.risk_score}%`, height: 4, borderRadius: 3 }} />
                    </div>
                    <div style={{ color: '#E2E8F0', fontSize: 12, marginBottom: 4 }}>⚠ {doc.primary_risk}</div>
                    <div style={{ color: '#4A5568', fontSize: 11, marginBottom: 4 }}>{doc.factors?.join(' · ')}</div>
                    <div style={{ color: '#48BB78', fontSize: 12 }}>✓ {doc.recommendation}</div>
                  </div>
                )
              })}
            </>
          )}
        </>
      )}

      {/* Tab 3 — Task Suggestions */}
      {tab === 'suggestions' && (
        <>
          <div style={{ ...s.card, borderLeft: '3px solid #48BB78', marginBottom: 20 }}>
            <div style={{ color: '#48BB78', fontWeight: 700, fontSize: 12, letterSpacing: 2 }}>AI TASK SUGGESTIONS</div>
            <div style={{ color: '#4A5568', fontSize: 13, marginTop: 4 }}>Select a document and AI will suggest 5 specific audit tasks</div>
          </div>

          <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
            <select value={selectedDocId} onChange={e => setSelectedDocId(e.target.value)} style={{
              flex: 1, background: '#0F1628', border: '1px solid #1E2D4D', borderRadius: 6,
              padding: '8px 14px', color: '#E2E8F0', fontFamily: 'monospace', fontSize: 13, outline: 'none'
            }}>
              {documents.map(d => <option key={d.id} value={d.id}>[{d.id}] {d.filename}</option>)}
            </select>
            <button style={s.btn} onClick={runSuggestions} disabled={loading}>
              {loading ? '⚡ ANALYZING...' : '⚡ SUGGEST TASKS'}
            </button>
          </div>

          {suggestions?.suggestions?.map((task, i) => {
            const pc = SEVERITY_COLORS[task.priority?.toUpperCase()] || '#00D4FF'
            return (
              <div key={i} style={{ ...s.card, borderLeft: `4px solid ${pc}` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <div style={{ color: '#E2E8F0', fontWeight: 600, maxWidth: '75%' }}>{task.title}</div>
                  <div style={{ textAlign: 'right' }}>
                    <span style={{ background: `${pc}22`, color: pc, fontSize: '0.6rem', padding: '2px 8px', borderRadius: 4, fontWeight: 700, border: `1px solid ${pc}44` }}>
                      {task.priority?.toUpperCase()}
                    </span>
                    <div style={{ color: '#4A5568', fontSize: 11, marginTop: 4 }}>⏰ {task.suggested_deadline_days}d deadline</div>
                  </div>
                </div>
                <div style={{ color: '#4A5568', fontSize: 12, lineHeight: 1.6, marginBottom: 12 }}>{task.description}</div>
                <button onClick={() => createTask(task, task.suggested_deadline_days)} style={{
                  background: '#48BB7822', color: '#48BB78', border: '1px solid #48BB7844',
                  borderRadius: 6, padding: '6px 14px', cursor: 'pointer',
                  fontFamily: 'monospace', fontSize: 11, fontWeight: 700
                }}>✚ CREATE THIS TASK</button>
              </div>
            )
          })}
        </>
      )}

      {/* Tab 4 — Anomaly Detection */}
      {tab === 'anomaly' && (
        <>
          <div style={{ ...s.card, borderLeft: '3px solid #FF4D6D', marginBottom: 20 }}>
            <div style={{ color: '#FF4D6D', fontWeight: 700, fontSize: 12, letterSpacing: 2 }}>ANOMALY DETECTION ENGINE</div>
            <div style={{ color: '#4A5568', fontSize: 13, marginTop: 4 }}>AI + rule-based analysis of last 7 days of audit logs</div>
          </div>

          {!anomalyData ? (
            <button style={s.btn} onClick={runAnomaly} disabled={loading}>
              {loading ? '⚡ SCANNING...' : '⚡ RUN ANOMALY SCAN'}
            </button>
          ) : (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5,1fr)', gap: 12, marginBottom: 20 }}>
                {[
                  ['LOGS SCANNED', anomalyData.analyzed_logs, '#00D4FF'],
                  ['ANOMALIES', anomalyData.total, anomalyData.total > 0 ? '#FF4D6D' : '#48BB78'],
                  ['CRITICAL', anomalyData.critical, '#FF4D6D'],
                  ['HIGH', anomalyData.high, '#F6AD55'],
                  ['MEDIUM', anomalyData.medium, '#00D4FF'],
                ].map(([label, value, color]) => (
                  <div key={label} style={{ ...s.card, borderTop: `3px solid ${color}`, textAlign: 'center' }}>
                    <div style={{ fontSize: '0.6rem', color: '#4A5568', letterSpacing: 2, marginBottom: 6 }}>{label}</div>
                    <div style={{ fontSize: '1.8rem', fontWeight: 700, color, fontFamily: 'monospace' }}>{value}</div>
                  </div>
                ))}
              </div>

              {anomalyData.anomalies?.length === 0 ? (
                <div style={{ ...s.card, textAlign: 'center', padding: 40, borderTop: '3px solid #48BB78' }}>
                  <div style={{ fontSize: '2rem', marginBottom: 8 }}>✓</div>
                  <div style={{ color: '#48BB78', fontWeight: 700, letterSpacing: 2 }}>NO ANOMALIES DETECTED</div>
                  <div style={{ color: '#4A5568', fontSize: 13, marginTop: 6 }}>System activity appears normal</div>
                </div>
              ) : (
                anomalyData.anomalies?.map((anomaly, i) => {
                  const color = SEVERITY_COLORS[anomaly.severity] || '#718096'
                  const icon = SEVERITY_ICONS[anomaly.severity] || '⚪'
                  const detailRows = anomaly.details?.map(d => Object.entries(d).map(([k, v]) => `${k}: ${v}`).join(' · ')).join('\n')
                  return (
                    <div key={i} style={{ ...s.card, borderLeft: `4px solid ${color}` }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                        <div>
                          <div style={{ color: '#E2E8F0', fontWeight: 600 }}>
                            {icon} {anomaly.title}
                            {anomaly.ai_detected && (
                              <span style={{ background: '#9F7AEA22', color: '#9F7AEA', fontSize: '0.6rem', padding: '2px 8px', borderRadius: 4, fontWeight: 700, border: '1px solid #9F7AEA44', marginLeft: 8 }}>
                                AI DETECTED
                              </span>
                            )}
                          </div>
                          <div style={{ color: '#4A5568', fontSize: 11, marginTop: 2 }}>{anomaly.type?.replace(/_/g, ' ')}</div>
                        </div>
                        <span style={{ background: `${color}22`, color, fontSize: '0.65rem', padding: '3px 10px', borderRadius: 4, fontWeight: 700, border: `1px solid ${color}44`, whiteSpace: 'nowrap', height: 'fit-content' }}>
                          {anomaly.severity}
                        </span>
                      </div>
                      <div style={{ color: '#E2E8F0', fontSize: 12, lineHeight: 1.6, marginBottom: 8 }}>{anomaly.description}</div>
                      <div style={{ color: '#48BB78', fontSize: 12, marginBottom: detailRows ? 10 : 0 }}>✓ {anomaly.recommendation}</div>
                      {detailRows && (
                        <details>
                          <summary style={{ color: '#4A5568', fontSize: 11, cursor: 'pointer' }}>◈ View Details</summary>
                          <div style={{ background: '#0A0E1A', borderRadius: 6, padding: '8px 12px', marginTop: 8, fontSize: 11, color: '#A0AEC0', lineHeight: 1.8 }}>
                            {detailRows}
                          </div>
                        </details>
                      )}
                    </div>
                  )
                })
              )}
            </>
          )}
        </>
      )}
    </Layout>
  )
}



