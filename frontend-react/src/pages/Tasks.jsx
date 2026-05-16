import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import Layout from '../components/Layout.jsx'
import PageHeader from '../components/PageHeader.jsx'
import StatusBadge from '../components/StatusBadge.jsx'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const PRIORITY_COLORS = {
  critical: '#FF4D6D', high: '#F6AD55', medium: '#00D4FF', low: '#48BB78'
}
const PRIORITIES = ['low', 'medium', 'high', 'critical']
const STATUSES = ['pending', 'in_progress', 'completed']

// Dark datetime input style — applied everywhere
const darkDate = {
  width: '100%',
  background: '#0A0E1A',
  border: '1px solid #1E2D4D',
  borderRadius: 6,
  padding: '9px 12px',
  color: '#E2E8F0',
  fontFamily: 'monospace',
  fontSize: 13,
  marginBottom: 10,
  outline: 'none',
  boxSizing: 'border-box',
  colorScheme: 'dark',
  cursor: 'pointer'
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
  const [editTask, setEditTask] = useState(null)
  const [comments, setComments] = useState([])
  const [newComment, setNewComment] = useState('')
  const [msg, setMsg] = useState('')
  const [editMsg, setEditMsg] = useState('')
  const [saving, setSaving] = useState(false)

  const emptyForm = {
    title: '', description: '', priority: 'medium',
    deadline: '', assigned_to: '', document_id: ''
  }
  const [form, setForm] = useState(emptyForm)

  const fetchData = async () => {
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

  useEffect(() => { fetchData() }, [filterStatus, filterPriority])

  const fetchComments = async (taskId) => {
    const c = await apiGet(`/tasks/${taskId}/comments`)
    setComments(c || [])
  }

  const openTask = async (task) => {
    setSelectedTask(task)
    setEditTask({
      title: task.title || '',
      description: task.description || '',
      priority: task.priority || 'medium',
      status: task.status || 'pending',
      deadline: task.deadline ? task.deadline.slice(0, 16) : '',
      assigned_to: task.assigned_to?.toString() || '',
      document_id: task.document_id?.toString() || ''
    })
    setEditMsg('')
    setNewComment('')
    await fetchComments(task.id)
  }

  const createTask = async () => {
    if (!form.title.trim()) { setMsg('✗ Title is required'); return }
    const payload = { title: form.title, priority: form.priority }
    if (form.description) payload.description = form.description
    if (form.deadline) payload.deadline = new Date(form.deadline).toISOString()
    if (form.assigned_to) payload.assigned_to = parseInt(form.assigned_to)
    if (form.document_id) payload.document_id = parseInt(form.document_id)

    const res = await apiPost('/tasks/', payload)
    if (res.status === 200) {
      setMsg('✓ Task created successfully')
      setShowCreate(false)
      setForm(emptyForm)
      fetchData()
      setTimeout(() => setMsg(''), 3000)
    } else {
      setMsg('✗ ' + (res.data?.detail || 'Failed to create task'))
    }
  }

  const updateTask = async () => {
    if (!editTask.title.trim()) { setEditMsg('✗ Title required'); return }
    setSaving(true)
    const payload = {
      title: editTask.title,
      priority: editTask.priority,
      status: editTask.status,
    }
    if (editTask.description !== undefined) payload.description = editTask.description || null
    if (editTask.deadline) payload.deadline = new Date(editTask.deadline).toISOString()
    else payload.deadline = null
    if (editTask.assigned_to) payload.assigned_to = parseInt(editTask.assigned_to)
    else payload.assigned_to = null
    if (editTask.document_id) payload.document_id = parseInt(editTask.document_id)
    else payload.document_id = null

    const res = await apiPatch(`/tasks/${selectedTask.id}`, payload)
    setSaving(false)
    if (res.status === 200) {
      setEditMsg('✓ Saved successfully')
      setSelectedTask(prev => ({ ...prev, ...res.data }))
      fetchData()
      setTimeout(() => setEditMsg(''), 3000)
    } else {
      setEditMsg('✗ ' + (res.data?.detail || 'Update failed'))
    }
  }

  const deleteTask = async (taskId) => {
    if (!window.confirm('Delete this task? This cannot be undone.')) return
    await apiDelete(`/tasks/${taskId}`)
    setSelectedTask(null)
    fetchData()
  }

  const addComment = async () => {
    if (!newComment.trim()) return
    const res = await apiPost(`/tasks/${selectedTask.id}/comments`, { content: newComment.trim() })
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
    if (!id) return 'Unassigned'
    const u = users.find(u => u.id === parseInt(id))
    return u ? `${u.full_name}${u.designation ? ' · ' + u.designation : ''}` : `User #${id}`
  }

  const getDaysLeft = (deadline) => {
    if (!deadline) return null
    return Math.round((new Date(deadline) - new Date()) / 86400000)
  }

  const s = {
    card: {
      background: '#0F1628', border: '1px solid #1E2D4D',
      borderRadius: 10, padding: 20, marginBottom: 16
    },
    input: {
      width: '100%', background: '#0A0E1A', border: '1px solid #1E2D4D',
      borderRadius: 6, padding: '9px 12px', color: '#E2E8F0',
      fontFamily: 'monospace', fontSize: 13, marginBottom: 10,
      outline: 'none', boxSizing: 'border-box'
    },
    textarea: {
      width: '100%', background: '#0A0E1A', border: '1px solid #1E2D4D',
      borderRadius: 6, padding: '9px 12px', color: '#E2E8F0',
      fontFamily: 'monospace', fontSize: 13, marginBottom: 10,
      outline: 'none', boxSizing: 'border-box', resize: 'vertical', minHeight: 80
    },
    select: {
      width: '100%', background: '#0A0E1A', border: '1px solid #1E2D4D',
      borderRadius: 6, padding: '9px 12px', color: '#E2E8F0',
      fontFamily: 'monospace', fontSize: 13, marginBottom: 10,
      outline: 'none', boxSizing: 'border-box'
    },
    label: {
      fontSize: '0.65rem', color: '#4A5568', letterSpacing: 2,
      marginBottom: 5, display: 'block'
    },
    primaryBtn: {
      background: 'linear-gradient(135deg,#00D4FF,#0088AA)', color: '#0A0E1A',
      border: 'none', borderRadius: 6, padding: '9px 20px',
      cursor: 'pointer', fontFamily: 'monospace', fontSize: 12,
      fontWeight: 700, letterSpacing: 1
    },
    secondaryBtn: {
      background: '#1E2D4D', color: '#E2E8F0', border: 'none',
      borderRadius: 6, padding: '9px 16px', cursor: 'pointer',
      fontFamily: 'monospace', fontSize: 12, fontWeight: 700
    },
    dangerBtn: {
      background: '#FF4D6D22', color: '#FF4D6D',
      border: '1px solid #FF4D6D44', borderRadius: 6,
      padding: '9px 16px', cursor: 'pointer',
      fontFamily: 'monospace', fontSize: 12, fontWeight: 700
    },
    modal: {
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.8)', display: 'flex',
      alignItems: 'center', justifyContent: 'center', zIndex: 1000,
      padding: 20
    },
    modalCard: {
      background: '#0F1628', border: '1px solid #1E2D4D',
      borderRadius: 12, width: '100%', maxWidth: 800,
      maxHeight: '92vh', overflow: 'auto', padding: 28
    },
    filterBtn: (active) => ({
      background: active ? '#00D4FF22' : '#0F1628',
      color: active ? '#00D4FF' : '#4A5568',
      border: `1px solid ${active ? '#00D4FF44' : '#1E2D4D'}`,
      borderRadius: 6, padding: '6px 14px', cursor: 'pointer',
      fontFamily: 'monospace', fontSize: 11, fontWeight: 700, letterSpacing: 1
    }),
    sectionTitle: {
      fontSize: '0.65rem', color: '#4A5568',
      letterSpacing: 3, marginBottom: 14,
      paddingBottom: 8, borderBottom: '1px solid #1E2D4D'
    },
    toast: (ok) => ({
      color: ok ? '#48BB78' : '#FF4D6D',
      background: ok ? '#48BB7811' : '#FF4D6D11',
      border: `1px solid ${ok ? '#48BB7833' : '#FF4D6D33'}`,
      borderRadius: 6, padding: '10px 16px',
      marginBottom: 16, fontSize: 13
    })
  }

  return (
    <Layout>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <PageHeader title="◈ TASKS" subtitle="Manage and track audit tasks" />
        <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
          <button style={s.secondaryBtn} onClick={fetchData}>↻ REFRESH</button>
          {['admin', 'auditor'].includes(user?.role) && (
            <button style={s.primaryBtn}
              onClick={() => { setShowCreate(!showCreate); setMsg('') }}>
              ✚ CREATE TASK
            </button>
          )}
        </div>
      </div>

      {msg && <div style={s.toast(msg.startsWith('✓'))}>{msg}</div>}

      {/* Create Form */}
      {showCreate && (
        <div style={{ ...s.card, borderTop: '3px solid #00D4FF', marginBottom: 24 }}>
          <div style={s.sectionTitle}>✚ CREATE NEW TASK</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
            <div>
              <label style={s.label}>TITLE *</label>
              <input style={s.input} placeholder="Task title"
                value={form.title}
                onChange={e => setForm({ ...form, title: e.target.value })} />

              <label style={s.label}>DESCRIPTION</label>
              <textarea style={s.textarea} placeholder="Detailed description..."
                value={form.description}
                onChange={e => setForm({ ...form, description: e.target.value })} />

              <label style={s.label}>PRIORITY</label>
              <select style={s.select} value={form.priority}
                onChange={e => setForm({ ...form, priority: e.target.value })}>
                {PRIORITIES.map(p => (
                  <option key={p} value={p}>
                    {p === 'critical' ? '🔴' : p === 'high' ? '🟠' : p === 'medium' ? '🟡' : '🟢'} {p.charAt(0).toUpperCase() + p.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label style={s.label}>DEADLINE</label>
              <input
                style={darkDate}
                type="datetime-local"
                value={form.deadline}
                onChange={e => setForm({ ...form, deadline: e.target.value })}
              />

              <label style={s.label}>ASSIGN TO</label>
              <select style={s.select} value={form.assigned_to}
                onChange={e => setForm({ ...form, assigned_to: e.target.value })}>
                <option value="">Select user...</option>
                {users.map(u => (
                  <option key={u.id} value={u.id}>
                    {u.full_name} ({u.role})
                  </option>
                ))}
              </select>

              <label style={s.label}>LINK DOCUMENT (optional)</label>
              <select style={s.select} value={form.document_id}
                onChange={e => setForm({ ...form, document_id: e.target.value })}>
                <option value="">No document</option>
                {documents.map(d => (
                  <option key={d.id} value={d.id}>[{d.id}] {d.filename}</option>
                ))}
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 10, marginTop: 4 }}>
            <button style={s.primaryBtn} onClick={createTask}>✚ CREATE TASK →</button>
            <button style={s.secondaryBtn}
              onClick={() => { setShowCreate(false); setForm(emptyForm); setMsg('') }}>
              CANCEL
            </button>
          </div>
        </div>
      )}

      {/* Filters */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          <span style={{ color: '#4A5568', fontSize: 10, letterSpacing: 2, alignSelf: 'center' }}>STATUS</span>
          {['all', 'pending', 'in_progress', 'completed', 'overdue'].map(st => (
            <button key={st} style={s.filterBtn(filterStatus === st)}
              onClick={() => setFilterStatus(st)}>
              {st.replace('_', ' ').toUpperCase()}
            </button>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 6, marginLeft: 'auto', flexWrap: 'wrap' }}>
          <span style={{ color: '#4A5568', fontSize: 10, letterSpacing: 2, alignSelf: 'center' }}>PRIORITY</span>
          {['all', 'low', 'medium', 'high', 'critical'].map(p => (
            <button key={p} style={{
              ...s.filterBtn(filterPriority === p),
              color: filterPriority === p ? (PRIORITY_COLORS[p] || '#00D4FF') : '#4A5568',
              borderColor: filterPriority === p ? `${PRIORITY_COLORS[p] || '#00D4FF'}44` : '#1E2D4D',
              background: filterPriority === p ? `${PRIORITY_COLORS[p] || '#00D4FF'}22` : '#0F1628'
            }} onClick={() => setFilterPriority(p)}>
              {p.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Task count */}
      <div style={{ fontSize: '0.65rem', color: '#4A5568', letterSpacing: 3, marginBottom: 12 }}>
        {tasks.length} TASK{tasks.length !== 1 ? 'S' : ''} · CLICK ANY CARD TO VIEW & EDIT
      </div>

      {/* Task Grid */}
      {tasks.length === 0 ? (
        <div style={{ ...s.card, textAlign: 'center', padding: '60px 0' }}>
          <div style={{ fontSize: '2rem', marginBottom: 8 }}>◈</div>
          <div style={{ color: '#4A5568', letterSpacing: 2 }}>NO TASKS FOUND</div>
          <div style={{ color: '#1E2D4D', fontSize: 12, marginTop: 6 }}>
            {filterStatus !== 'all' || filterPriority !== 'all'
              ? 'Try changing filters'
              : 'Create your first task above'}
          </div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          {tasks.map(task => {
            const pc = PRIORITY_COLORS[task.priority] || '#718096'
            const daysLeft = getDaysLeft(task.deadline)
            return (
              <div key={task.id}
                style={{
                  background: '#0F1628', border: '1px solid #1E2D4D',
                  borderRadius: 10, padding: 18, borderLeft: `4px solid ${pc}`,
                  cursor: 'pointer', transition: 'all 0.2s'
                }}
                onClick={() => openTask(task)}
                onMouseEnter={e => {
                  e.currentTarget.style.borderLeftColor = '#00D4FF'
                  e.currentTarget.style.background = '#0F1A2E'
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.borderLeftColor = pc
                  e.currentTarget.style.background = '#0F1628'
                }}>

                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, alignItems: 'flex-start' }}>
                  <div style={{ color: '#E2E8F0', fontWeight: 600, fontSize: 14, maxWidth: '65%', lineHeight: 1.4 }}>
                    {task.title}
                  </div>
                  <StatusBadge status={task.status} />
                </div>

                {task.description && (
                  <div style={{ color: '#4A5568', fontSize: 12, marginBottom: 10, lineHeight: 1.5 }}>
                    {task.description.slice(0, 90)}{task.description.length > 90 ? '...' : ''}
                  </div>
                )}

                <div style={{ display: 'flex', gap: 12, fontSize: 11, color: '#4A5568', flexWrap: 'wrap', alignItems: 'center' }}>
                  <span style={{ color: pc, fontWeight: 700 }}>
                    {task.priority === 'critical' ? '🔴' : task.priority === 'high' ? '🟠' : task.priority === 'medium' ? '🟡' : '🟢'} {task.priority?.toUpperCase()}
                  </span>
                  {daysLeft !== null && (
                    <span style={{ color: daysLeft < 0 ? '#FF4D6D' : daysLeft <= 3 ? '#F6AD55' : '#48BB78', fontWeight: daysLeft <= 3 ? 700 : 400 }}>
                      ⏰ {daysLeft < 0 ? `${Math.abs(daysLeft)}d OVERDUE` : daysLeft === 0 ? 'DUE TODAY' : `${daysLeft}d left`}
                    </span>
                  )}
                  {task.assigned_to && (
                    <span>👤 {getUserName(task.assigned_to).split(' · ')[0]}</span>
                  )}
                  <span style={{ marginLeft: 'auto', color: '#1E2D4D', fontWeight: 700 }}>#{task.id}</span>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* ── Task Detail Modal ─────────────────────────────────── */}
      {selectedTask && editTask && (
        <div style={s.modal}
          onClick={e => e.target === e.currentTarget && setSelectedTask(null)}>
          <div style={s.modalCard}>

            {/* Modal Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
              <div style={{ borderLeft: `4px solid ${PRIORITY_COLORS[selectedTask.priority] || '#718096'}`, paddingLeft: 14 }}>
                <div style={{ color: '#E2E8F0', fontSize: '1.1rem', fontWeight: 700, lineHeight: 1.4 }}>
                  {selectedTask.title}
                </div>
                <div style={{ display: 'flex', gap: 8, marginTop: 6, alignItems: 'center', flexWrap: 'wrap' }}>
                  <StatusBadge status={selectedTask.status} />
                  <span style={{ color: '#4A5568', fontSize: 11 }}>Task #{selectedTask.id}</span>
                  <span style={{ color: '#4A5568', fontSize: 11 }}>Created {selectedTask.created_at?.slice(0, 10)}</span>
                </div>
              </div>
              <button onClick={() => setSelectedTask(null)} style={{
                background: '#1E2D4D', border: 'none', color: '#E2E8F0',
                cursor: 'pointer', fontSize: 14, borderRadius: 6,
                padding: '6px 12px', fontFamily: 'monospace'
              }}>✕ CLOSE</button>
            </div>

            {/* Edit Form */}
            <div style={{ background: '#0A0E1A', border: '1px solid #1E2D4D', borderRadius: 10, padding: 20, marginBottom: 20 }}>
              <div style={s.sectionTitle}>◈ EDIT TASK DETAILS</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>

                {/* Left column */}
                <div>
                  <label style={s.label}>TITLE *</label>
                  <input style={s.input} value={editTask.title}
                    onChange={e => setEditTask({ ...editTask, title: e.target.value })} />

                  <label style={s.label}>DESCRIPTION</label>
                  <textarea style={s.textarea} value={editTask.description}
                    placeholder="Add a description..."
                    onChange={e => setEditTask({ ...editTask, description: e.target.value })} />

                  <label style={s.label}>STATUS</label>
                  <select style={s.select} value={editTask.status}
                    onChange={e => setEditTask({ ...editTask, status: e.target.value })}>
                    {STATUSES.map(st => (
                      <option key={st} value={st}>
                        {st === 'completed' ? '✓ ' : st === 'in_progress' ? '⚡ ' : '○ '}
                        {st.replace('_', ' ').charAt(0).toUpperCase() + st.replace('_', ' ').slice(1)}
                      </option>
                    ))}
                  </select>

                  <label style={s.label}>PRIORITY</label>
                  <select style={s.select} value={editTask.priority}
                    onChange={e => setEditTask({ ...editTask, priority: e.target.value })}>
                    {PRIORITIES.map(p => (
                      <option key={p} value={p}>
                        {p === 'critical' ? '🔴' : p === 'high' ? '🟠' : p === 'medium' ? '🟡' : '🟢'} {p.charAt(0).toUpperCase() + p.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Right column */}
                <div>
                  <label style={s.label}>DEADLINE</label>
                  <input
                    style={darkDate}
                    type="datetime-local"
                    value={editTask.deadline}
                    onChange={e => setEditTask({ ...editTask, deadline: e.target.value })}
                  />
                  {editTask.deadline && (
                    <button
                      onClick={() => setEditTask({ ...editTask, deadline: '' })}
                      style={{
                        background: 'none', border: 'none', color: '#FF4D6D',
                        fontSize: 11, cursor: 'pointer', fontFamily: 'monospace',
                        marginTop: -6, marginBottom: 8, display: 'block'
                      }}>
                      ✕ Clear deadline
                    </button>
                  )}

                  <label style={s.label}>ASSIGN TO</label>
                  <select style={s.select} value={editTask.assigned_to || ''}
                    onChange={e => setEditTask({ ...editTask, assigned_to: e.target.value })}>
                    <option value="">Unassigned</option>
                    {users.map(u => (
                      <option key={u.id} value={u.id}>
                        {u.full_name} ({u.role})
                      </option>
                    ))}
                  </select>

                  <label style={s.label}>LINK DOCUMENT</label>
                  <select style={s.select} value={editTask.document_id || ''}
                    onChange={e => setEditTask({ ...editTask, document_id: e.target.value })}>
                    <option value="">No document</option>
                    {documents.map(d => (
                      <option key={d.id} value={d.id}>[{d.id}] {d.filename}</option>
                    ))}
                  </select>

                  {/* Task info box */}
                  <div style={{ background: '#0F1628', border: '1px solid #1E2D4D', borderRadius: 8, padding: 14 }}>
                    <div style={{ fontSize: '0.6rem', color: '#4A5568', letterSpacing: 2, marginBottom: 10 }}>TASK INFO</div>
                    {[
                      ['CREATED BY', getUserName(selectedTask.created_by)],
                      ['CREATED', selectedTask.created_at?.slice(0, 10)],
                      ['LAST UPDATED', selectedTask.updated_at?.slice(0, 10) || '—'],
                      ['CURRENT ASSIGNEE', getUserName(selectedTask.assigned_to)],
                    ].map(([label, value]) => (
                      <div key={label} style={{ marginBottom: 8 }}>
                        <div style={{ fontSize: '0.6rem', color: '#4A5568', letterSpacing: 1 }}>{label}</div>
                        <div style={{ color: '#E2E8F0', fontSize: 12, marginTop: 1 }}>{value}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {editMsg && <div style={{ ...s.toast(editMsg.startsWith('✓')), marginTop: 12, marginBottom: 0 }}>{editMsg}</div>}

              <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
                <button style={{ ...s.primaryBtn, opacity: saving ? 0.7 : 1 }}
                  onClick={updateTask} disabled={saving}>
                  {saving ? '⚡ SAVING...' : '✓ SAVE CHANGES'}
                </button>
                {user?.role === 'admin' && (
                  <button style={s.dangerBtn} onClick={() => deleteTask(selectedTask.id)}>
                    ✕ DELETE TASK
                  </button>
                )}
                <button style={{ ...s.secondaryBtn, marginLeft: 'auto' }}
                  onClick={() => setSelectedTask(null)}>
                  CLOSE
                </button>
              </div>
            </div>

            {/* Comments Section */}
            <div>
              <div style={s.sectionTitle}>
                ◈ COMMENTS ({comments.length})
              </div>

              {/* Comment list */}
              {comments.length === 0 ? (
                <div style={{
                  color: '#4A5568', fontSize: 13, textAlign: 'center',
                  padding: '20px', border: '1px dashed #1E2D4D',
                  borderRadius: 8, marginBottom: 12
                }}>
                  No comments yet — be the first to add one
                </div>
              ) : (
                <div style={{ marginBottom: 12 }}>
                  {comments.map(c => {
                    const isMine = c.user_id === user?.id
                    const commenter = users.find(u => u.id === c.user_id)
                    return (
                      <div key={c.id} style={{
                        background: isMine ? '#0D1F35' : '#0A0E1A',
                        border: `1px solid ${isMine ? '#00D4FF33' : '#1E2D4D'}`,
                        borderRadius: 8, padding: '12px 14px', marginBottom: 8,
                        borderLeft: `3px solid ${isMine ? '#00D4FF' : '#1E2D4D'}`
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, alignItems: 'center' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <div style={{
                              width: 24, height: 24, borderRadius: '50%',
                              background: isMine ? '#00D4FF22' : '#1E2D4D',
                              border: `1px solid ${isMine ? '#00D4FF44' : '#2D3F5E'}`,
                              display: 'flex', alignItems: 'center', justifyContent: 'center',
                              fontSize: 10, fontWeight: 700,
                              color: isMine ? '#00D4FF' : '#718096'
                            }}>
                              {commenter?.full_name?.[0]?.toUpperCase() || '?'}
                            </div>
                            <span style={{ color: isMine ? '#00D4FF' : '#E2E8F0', fontSize: 12, fontWeight: 700 }}>
                              {commenter?.full_name || `User #${c.user_id}`}
                            </span>
                            {isMine && (
                              <span style={{
                                color: '#48BB78', fontSize: 9, fontWeight: 700,
                                background: '#48BB7822', padding: '1px 6px',
                                borderRadius: 3, border: '1px solid #48BB7844'
                              }}>YOU</span>
                            )}
                            {commenter?.designation && (
                              <span style={{ color: '#4A5568', fontSize: 11 }}>{commenter.designation}</span>
                            )}
                          </div>
                          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                            <span style={{ color: '#4A5568', fontSize: 10 }}>
                              {c.created_at?.slice(0, 16).replace('T', ' ')}
                            </span>
                            {(isMine || user?.role === 'admin') && (
                              <button onClick={() => deleteComment(c.id)} style={{
                                background: '#FF4D6D22', border: '1px solid #FF4D6D33',
                                borderRadius: 4, color: '#FF4D6D',
                                cursor: 'pointer', fontSize: 10,
                                padding: '2px 6px', fontFamily: 'monospace'
                              }}>✕ DELETE</button>
                            )}
                          </div>
                        </div>
                        <div style={{ color: '#E2E8F0', fontSize: 13, lineHeight: 1.6, paddingLeft: 32 }}>
                          {c.content}
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}

              {/* Add comment */}
              <div style={{ display: 'flex', gap: 8 }}>
                <input
                  value={newComment}
                  onChange={e => setNewComment(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && !e.shiftKey && addComment()}
                  placeholder="Write a comment... (Enter to submit)"
                  style={{
                    flex: 1, background: '#0A0E1A', border: '1px solid #1E2D4D',
                    borderRadius: 6, padding: '10px 14px', color: '#E2E8F0',
                    fontFamily: 'monospace', fontSize: 13, outline: 'none'
                  }}
                />
                <button onClick={addComment} style={s.primaryBtn}>ADD →</button>
              </div>
            </div>

          </div>
        </div>
      )}
    </Layout>
  )
}
