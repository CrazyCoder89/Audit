import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import Layout from '../components/Layout.jsx'
import PageHeader from '../components/PageHeader.jsx'
import StatusBadge from '../components/StatusBadge.jsx'

const PRIORITY_COLORS = {
  critical: '#FF4D6D', high: '#F6AD55', medium: '#00D4FF', low: '#48BB78'
}

export default function Tasks() {
  const { apiGet, apiPost, apiPatch, apiDelete, user } = useAuth()
  const [tasks, setTasks] = useState([])
  const [users, setUsers] = useState([])
  const [documents, setDocuments] = useState([])
  const [filterStatus, setFilterStatus] = useState('all')
  const [filterPriority, setFilterPriority] = useState('all')
  const [showCreate, setShowCreate] = useState(false)
  const [selectedTask, setSelectedTask] = useState(null)
  const [comments, setComments] = useState([])
  const [newComment, setNewComment] = useState('')
  const [form, setForm] = useState({
    title: '', description: '', priority: 'medium',
    deadline: '', assigned_to: '', document_id: ''
  })
  const [msg, setMsg] = useState('')

  const fetch = async () => {
    const params = {}
    if (filterStatus !== 'all') params.status = filterStatus
    if (filterPriority !== 'all') params.priority = filterPriority
    const [tks, us, docs] = await Promise.all([
      apiGet('/tasks/', params),
      apiGet('/auth/users'),
      apiGet('/documents/')
    ])
    setTasks(tks || [])
    setUsers(us || [])
    setDocuments((docs || []).filter(d => d.status === 'processed'))
  }

  useEffect(() => { fetch() }, [filterStatus, filterPriority])

  const fetchComments = async (taskId) => {
    const c = await apiGet(`/tasks/${taskId}/comments`)
    setComments(c || [])
  }

  const openTask = async (task) => {
    setSelectedTask(task)
    await fetchComments(task.id)
  }

  const createTask = async () => {
    const payload = { ...form }
    if (!payload.title.trim()) { setMsg('Title required'); return }
    if (payload.assigned_to) payload.assigned_to = parseInt(payload.assigned_to)
    else delete payload.assigned_to
    if (payload.document_id) payload.document_id = parseInt(payload.document_id)
    else delete payload.document_id
    if (!payload.deadline) delete payload.deadline
    const res = await apiPost('/tasks/', payload)
    if (res.status === 200) {
      setMsg('✓ Task created')
      setShowCreate(false)
      setForm({ title: '', description: '', priority: 'medium', deadline: '', assigned_to: '', document_id: '' })
      fetch()
    } else {
      setMsg('✗ ' + (res.data?.detail || 'Failed'))
    }
  }

  const updateStatus = async (taskId, status) => {
    await apiPatch(`/tasks/${taskId}`, { status })
    fetch()
    if (selectedTask?.id === taskId) setSelectedTask({ ...selectedTask, status })
  }

  const deleteTask = async (taskId) => {
    if (!window.confirm('Delete this task?')) return
    await apiDelete(`/tasks/${taskId}`)
    setSelectedTask(null)
    fetch()
  }

  const addComment = async () => {
    if (!newComment.trim()) return
    const res = await apiPost(`/tasks/${selectedTask.id}/comments`, { content: newComment })
    if (res.status === 200) {
      setNewComment('')
      fetchComments(selectedTask.id)
    }
  }

  const deleteComment = async (commentId) => {
    await apiDelete(`/tasks/${selectedTask.id}/comments/${commentId}`)
    fetchComments(selectedTask.id)
  }

  const getUserName = (id) => {
    const u = users.find(u => u.id === id)
    return u ? `${u.full_name}${u.designation ? ' · ' + u.designation : ''}` : `User #${id}`
  }

  const s = {
    card: { background: '#0F1628', border: '1px solid #1E2D4D', borderRadius: 10, padding: 20, marginBottom: 16 },
    input: {
      width: '100%', background: '#0A0E1A', border: '1px solid #1E2D4D',
      borderRadius: 6, padding: '8px 12px', color: '#E2E8F0',
      fontFamily: 'monospace', fontSize: 13, marginBottom: 10,
      outline: 'none', boxSizing: 'border-box'
    },
    select: {
      background: '#0A0E1A', border: '1px solid #1E2D4D', borderRadius: 6,
      padding: '8px 12px', color: '#E2E8F0', fontFamily: 'monospace',
      fontSize: 13, outline: 'none', marginBottom: 10, width: '100%', boxSizing: 'border-box'
    },
    btn: (color = '#00D4FF') => ({
      background: `linear-gradient(135deg,${color},${color}99)`,
      color: color === '#00D4FF' ? '#0A0E1A' : 'white',
      border: 'none', borderRadius: 6, padding: '8px 18px',
      cursor: 'pointer', fontFamily: 'monospace', fontSize: 12,
      fontWeight: 700, letterSpacing: 1
    }),
    modal: {
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.7)', display: 'flex',
      alignItems: 'center', justifyContent: 'center', zIndex: 1000
    },
    modalCard: {
      background: '#0F1628', border: '1px solid #1E2D4D', borderRadius: 12,
      width: '90%', maxWidth: 700, maxHeight: '90vh', overflow: 'auto', padding: 28
    }
  }

  return (
    <Layout>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <PageHeader title="◈ TASKS" subtitle="Manage and track audit tasks" />
        {['admin', 'auditor'].includes(user?.role) && (
          <button style={{ ...s.btn(), marginTop: 8 }} onClick={() => setShowCreate(!showCreate)}>
            ✚ CREATE TASK
          </button>
        )}
      </div>

      {msg && <div style={{ color: msg.startsWith('✓') ? '#48BB78' : '#FF4D6D', marginBottom: 12, fontSize: 13 }}>{msg}</div>}

      {/* Create Form */}
      {showCreate && (
        <div style={{ ...s.card, borderTop: '3px solid #00D4FF' }}>
          <div style={{ fontSize: '0.65rem', color: '#4A5568', letterSpacing: 3, marginBottom: 16 }}>CREATE NEW TASK</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div>
              <input style={s.input} placeholder="Task title *" value={form.title}
                onChange={e => setForm({ ...form, title: e.target.value })} />
              <textarea style={{ ...s.input, height: 80, resize: 'vertical' }}
                placeholder="Description..." value={form.description}
                onChange={e => setForm({ ...form, description: e.target.value })} />
              <select style={s.select} value={form.priority}
                onChange={e => setForm({ ...form, priority: e.target.value })}>
                <option value="low">Low Priority</option>
                <option value="medium">Medium Priority</option>
                <option value="high">High Priority</option>
                <option value="critical">Critical Priority</option>
              </select>
            </div>
            <div>
              <input style={s.input} type="datetime-local" value={form.deadline}
                onChange={e => setForm({ ...form, deadline: e.target.value })} />
              <select style={s.select} value={form.assigned_to}
                onChange={e => setForm({ ...form, assigned_to: e.target.value })}>
                <option value="">Assign to user...</option>
                {users.map(u => <option key={u.id} value={u.id}>{u.full_name} ({u.role})</option>)}
              </select>
              <select style={s.select} value={form.document_id}
                onChange={e => setForm({ ...form, document_id: e.target.value })}>
                <option value="">Link document (optional)...</option>
                {documents.map(d => <option key={d.id} value={d.id}>[{d.id}] {d.filename}</option>)}
              </select>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button style={s.btn()} onClick={createTask}>CREATE TASK →</button>
            <button style={s.btn('#1E2D4D')} onClick={() => setShowCreate(false)}>CANCEL</button>
          </div>
        </div>
      )}

      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        {['all', 'pending', 'in_progress', 'completed', 'overdue'].map(s => (
          <button key={s} onClick={() => setFilterStatus(s)} style={{
            background: filterStatus === s ? '#00D4FF22' : '#0F1628',
            color: filterStatus === s ? '#00D4FF' : '#4A5568',
            border: `1px solid ${filterStatus === s ? '#00D4FF44' : '#1E2D4D'}`,
            borderRadius: 6, padding: '6px 14px', cursor: 'pointer',
            fontFamily: 'monospace', fontSize: 11, fontWeight: 700, letterSpacing: 1
          }}>{s.replace('_', ' ').toUpperCase()}</button>
        ))}
      </div>

      {/* Task Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        {tasks.map(task => {
          const pc = PRIORITY_COLORS[task.priority] || '#718096'
          return (
            <div key={task.id} style={{
              background: '#0F1628', border: '1px solid #1E2D4D',
              borderRadius: 10, padding: 18, borderLeft: `4px solid ${pc}`,
              cursor: 'pointer', transition: 'border-color 0.2s'
            }} onClick={() => openTask(task)}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <div style={{ color: '#E2E8F0', fontWeight: 600, fontSize: 14, maxWidth: '65%' }}>{task.title}</div>
                <StatusBadge status={task.status} />
              </div>
              <div style={{ color: '#4A5568', fontSize: 12, marginBottom: 10, lineHeight: 1.5 }}>
                {task.description?.slice(0, 80)}{task.description?.length > 80 ? '...' : ''}
              </div>
              <div style={{ display: 'flex', gap: 12, fontSize: 11, color: '#4A5568' }}>
                <span style={{ color: pc, fontWeight: 700 }}>▪ {task.priority?.toUpperCase()}</span>
                {task.deadline && <span>⏰ {task.deadline.slice(0, 10)}</span>}
                {task.assigned_to && <span>👤 {getUserName(task.assigned_to).split(' · ')[0]}</span>}
              </div>
            </div>
          )
        })}
      </div>

      {tasks.length === 0 && (
        <div style={{ textAlign: 'center', color: '#4A5568', padding: '60px 0' }}>
          <div style={{ fontSize: '2rem', marginBottom: 8 }}>◈</div>
          No tasks found
        </div>
      )}

      {/* Task Detail Modal */}
      {selectedTask && (
        <div style={s.modal} onClick={e => e.target === e.currentTarget && setSelectedTask(null)}>
          <div style={s.modalCard}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
              <div style={{ borderLeft: `4px solid ${PRIORITY_COLORS[selectedTask.priority]}`, paddingLeft: 16 }}>
                <div style={{ color: '#E2E8F0', fontSize: '1.1rem', fontWeight: 700 }}>{selectedTask.title}</div>
                <div style={{ display: 'flex', gap: 8, marginTop: 6, alignItems: 'center' }}>
                  <StatusBadge status={selectedTask.status} />
                  <span style={{ color: PRIORITY_COLORS[selectedTask.priority], fontSize: 11, fontWeight: 700, letterSpacing: 2 }}>
                    {selectedTask.priority?.toUpperCase()} PRIORITY
                  </span>
                </div>
              </div>
              <button onClick={() => setSelectedTask(null)} style={{
                background: 'none', border: 'none', color: '#4A5568',
                cursor: 'pointer', fontSize: 20
              }}>✕</button>
            </div>

            {/* Details */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
              <div style={{ background: '#0A0E1A', border: '1px solid #1E2D4D', borderRadius: 8, padding: 16 }}>
                <div style={{ fontSize: '0.65rem', color: '#4A5568', letterSpacing: 2, marginBottom: 12 }}>TASK INFO</div>
                {[
                  ['TASK ID', `#${selectedTask.id}`],
                  ['DEADLINE', selectedTask.deadline?.slice(0, 16).replace('T', ' ') || 'No deadline'],
                  ['CREATED', selectedTask.created_at?.slice(0, 10)],
                  ['DOCUMENT', selectedTask.document_id ? `Doc #${selectedTask.document_id}` : 'None'],
                ].map(([label, value]) => (
                  <div key={label} style={{ marginBottom: 10 }}>
                    <div style={{ fontSize: '0.65rem', color: '#4A5568' }}>{label}</div>
                    <div style={{ color: '#E2E8F0', fontSize: 13 }}>{value}</div>
                  </div>
                ))}
              </div>
              <div style={{ background: '#0A0E1A', border: '1px solid #1E2D4D', borderRadius: 8, padding: 16 }}>
                <div style={{ fontSize: '0.65rem', color: '#4A5568', letterSpacing: 2, marginBottom: 12 }}>PEOPLE</div>
                <div style={{ marginBottom: 10 }}>
                  <div style={{ fontSize: '0.65rem', color: '#4A5568' }}>ASSIGNED TO</div>
                  <div style={{ color: '#00D4FF', fontSize: 13, fontWeight: 600 }}>
                    👤 {selectedTask.assigned_to ? getUserName(selectedTask.assigned_to) : 'Unassigned'}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '0.65rem', color: '#4A5568' }}>CREATED BY</div>
                  <div style={{ color: '#E2E8F0', fontSize: 13 }}>
                    👤 {getUserName(selectedTask.created_by)}
                  </div>
                </div>
              </div>
            </div>

            {/* Description */}
            <div style={{ background: '#0A0E1A', border: '1px solid #1E2D4D', borderRadius: 8, padding: 16, marginBottom: 20 }}>
              <div style={{ fontSize: '0.65rem', color: '#4A5568', letterSpacing: 2, marginBottom: 8 }}>DESCRIPTION</div>
              <div style={{ color: '#E2E8F0', fontSize: 13, lineHeight: 1.7 }}>
                {selectedTask.description || 'No description provided.'}
              </div>
            </div>

            {/* Update Status */}
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontSize: '0.65rem', color: '#4A5568', letterSpacing: 2, marginBottom: 8 }}>UPDATE STATUS</div>
              <div style={{ display: 'flex', gap: 8 }}>
                {['pending', 'in_progress', 'completed'].map(st => (
                  <button key={st} onClick={() => updateStatus(selectedTask.id, st)} style={{
                    background: selectedTask.status === st ? '#00D4FF22' : '#0A0E1A',
                    color: selectedTask.status === st ? '#00D4FF' : '#4A5568',
                    border: `1px solid ${selectedTask.status === st ? '#00D4FF44' : '#1E2D4D'}`,
                    borderRadius: 6, padding: '6px 14px', cursor: 'pointer',
                    fontFamily: 'monospace', fontSize: 11, fontWeight: 700
                  }}>{st.replace('_', ' ').toUpperCase()}</button>
                ))}
                {user?.role === 'admin' && (
                  <button onClick={() => deleteTask(selectedTask.id)} style={{
                    background: '#FF4D6D22', color: '#FF4D6D',
                    border: '1px solid #FF4D6D44', borderRadius: 6,
                    padding: '6px 14px', cursor: 'pointer',
                    fontFamily: 'monospace', fontSize: 11, fontWeight: 700, marginLeft: 'auto'
                  }}>✕ DELETE</button>
                )}
              </div>
            </div>

            {/* Comments */}
            <div>
              <div style={{ fontSize: '0.65rem', color: '#4A5568', letterSpacing: 2, marginBottom: 12 }}>◈ COMMENTS</div>
              {comments.length === 0 ? (
                <div style={{ color: '#4A5568', fontSize: 13, textAlign: 'center', padding: '16px 0',
                              border: '1px dashed #1E2D4D', borderRadius: 8, marginBottom: 12 }}>
                  No comments yet
                </div>
              ) : (
                comments.map(c => {
                  const isMine = c.user_id === user?.id
                  const commenter = users.find(u => u.id === c.user_id)
                  return (
                    <div key={c.id} style={{
                      background: '#0A0E1A', border: `1px solid ${isMine ? '#00D4FF44' : '#1E2D4D'}`,
                      borderRadius: 8, padding: '10px 14px', marginBottom: 8
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                        <div>
                          <span style={{ color: '#00D4FF', fontSize: 12, fontWeight: 700 }}>
                            {commenter?.full_name || `User #${c.user_id}`}
                          </span>
                          {isMine && <span style={{ color: '#48BB78', fontSize: 10, marginLeft: 6, fontWeight: 700 }}>YOU</span>}
                          {commenter?.designation && (
                            <span style={{ color: '#4A5568', fontSize: 10, marginLeft: 6 }}>{commenter.designation}</span>
                          )}
                        </div>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                          <span style={{ color: '#4A5568', fontSize: 11 }}>{c.created_at?.slice(0, 16).replace('T', ' ')}</span>
                          {(isMine || user?.role === 'admin') && (
                            <button onClick={() => deleteComment(c.id)} style={{
                              background: 'none', border: 'none', color: '#FF4D6D',
                              cursor: 'pointer', fontSize: 12
                            }}>✕</button>
                          )}
                        </div>
                      </div>
                      <div style={{ color: '#E2E8F0', fontSize: 13, lineHeight: 1.5 }}>{c.content}</div>
                    </div>
                  )
                })
              )}
              <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                <input value={newComment} onChange={e => setNewComment(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && addComment()}
                  placeholder="Write a comment..."
                  style={{
                    flex: 1, background: '#0A0E1A', border: '1px solid #1E2D4D',
                    borderRadius: 6, padding: '8px 12px', color: '#E2E8F0',
                    fontFamily: 'monospace', fontSize: 13, outline: 'none'
                  }} />
                <button onClick={addComment} style={{
                  background: '#00D4FF', color: '#0A0E1A', border: 'none',
                  borderRadius: 6, padding: '8px 16px', cursor: 'pointer',
                  fontWeight: 700, fontFamily: 'monospace', fontSize: 13
                }}>ADD →</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </Layout>
  )
}



