import { useState, useEffect } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import Layout from '../components/Layout.jsx'
import PageHeader from '../components/PageHeader.jsx'
import axios from 'axios'

const ROLE_COLORS = { admin: '#FF4D6D', auditor: '#00D4FF', viewer: '#48BB78', guest: '#718096' }
const DEPARTMENTS = ['', 'Finance & Accounting', 'Legal & Compliance', 'Human Resources',
  'Information Technology', 'Operations', 'Risk Management', 'Internal Audit', 'Executive Management', 'Other']

export default function Users() {
  const { apiGet, authHeaders, user } = useAuth()
  const [users, setUsers] = useState([])
  const [filterRole, setFilterRole] = useState('all')
  const [filterStatus, setFilterStatus] = useState('all')
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ full_name: '', email: '', password: '', role: 'viewer', designation: '', department: '' })
  const [msg, setMsg] = useState('')

  const fetch = async () => {
    const data = await apiGet('/auth/users')
    setUsers(data || [])
  }

  useEffect(() => { fetch() }, [])

  const filteredUsers = users.filter(u => {
    if (filterRole !== 'all' && u.role !== filterRole) return false
    if (filterStatus === 'active' && !u.is_active) return false
    if (filterStatus === 'inactive' && u.is_active) return false
    return true
  })

  const createUser = async () => {
    if (!form.full_name || !form.email || !form.password) { setMsg('✗ Fill required fields'); return }
    try {
      const res = await axios.post('http://localhost:8000/auth/users', form,
        { headers: authHeaders() })
      if (res.status === 200) { setMsg('✓ User created'); setShowCreate(false); fetch() }
    } catch (e) {
      const detail = e.response?.data?.detail
      setMsg('✗ ' + (Array.isArray(detail) ? detail[0].msg : detail || 'Failed'))
    }
  }

  const updateUser = async (userId, data) => {
    await axios.patch(`http://localhost:8000/auth/users/${userId}`, data,
      { headers: authHeaders() })
    fetch()
  }

  if (user?.role !== 'admin') {
    return <Layout><div style={{ color: '#FF4D6D', padding: 40 }}>✗ Access denied — Admin only</div></Layout>
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
      fontSize: 12, outline: 'none'
    },
    btn: (color = '#00D4FF') => ({
      background: `${color}22`, color, border: `1px solid ${color}44`,
      borderRadius: 6, padding: '6px 14px', cursor: 'pointer',
      fontFamily: 'monospace', fontSize: 11, fontWeight: 700
    })
  }

  return (
    <Layout>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <PageHeader title="◈ USER MANAGEMENT" subtitle="Create, manage, and organize your team" />
        <button onClick={() => setShowCreate(!showCreate)} style={{
          background: 'linear-gradient(135deg,#00D4FF,#0088AA)', color: '#0A0E1A',
          border: 'none', borderRadius: 6, padding: '8px 18px', cursor: 'pointer',
          fontFamily: 'monospace', fontSize: 12, fontWeight: 700, marginTop: 8
        }}>✚ CREATE USER</button>
      </div>

      {msg && <div style={{ color: msg.startsWith('✓') ? '#48BB78' : '#FF4D6D', marginBottom: 12, fontSize: 13 }}>{msg}</div>}

      {/* Create form */}
      {showCreate && (
        <div style={{ ...s.card, borderTop: '3px solid #00D4FF' }}>
          <div style={{ fontSize: '0.65rem', color: '#4A5568', letterSpacing: 3, marginBottom: 16 }}>CREATE NEW USER</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
            <div>
              <input style={s.input} placeholder="Full Name *" value={form.full_name}
                onChange={e => setForm({ ...form, full_name: e.target.value })} />
              <input style={s.input} placeholder="Email *" type="email" value={form.email}
                onChange={e => setForm({ ...form, email: e.target.value })} />
            </div>
            <div>
              <input style={s.input} placeholder="Password *" type="password" value={form.password}
                onChange={e => setForm({ ...form, password: e.target.value })} />
              <input style={s.input} placeholder="Designation" value={form.designation}
                onChange={e => setForm({ ...form, designation: e.target.value })} />
            </div>
            <div>
              <select style={{ ...s.select, width: '100%', marginBottom: 10 }} value={form.role}
                onChange={e => setForm({ ...form, role: e.target.value })}>
                {['viewer', 'auditor', 'admin'].map(r => <option key={r} value={r}>{r}</option>)}
              </select>
              <select style={{ ...s.select, width: '100%' }} value={form.department}
                onChange={e => setForm({ ...form, department: e.target.value })}>
                {DEPARTMENTS.map(d => <option key={d} value={d}>{d || 'Select department...'}</option>)}
              </select>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
            <button onClick={createUser} style={{
              background: 'linear-gradient(135deg,#00D4FF,#0088AA)', color: '#0A0E1A',
              border: 'none', borderRadius: 6, padding: '8px 20px', cursor: 'pointer',
              fontFamily: 'monospace', fontSize: 12, fontWeight: 700
            }}>CREATE →</button>
            <button onClick={() => setShowCreate(false)} style={s.btn('#718096')}>CANCEL</button>
          </div>
        </div>
      )}

      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        <select style={s.select} value={filterRole} onChange={e => setFilterRole(e.target.value)}>
          <option value="all">All Roles</option>
          {['admin', 'auditor', 'viewer', 'guest'].map(r => <option key={r} value={r}>{r}</option>)}
        </select>
        <select style={s.select} value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
        <span style={{ color: '#4A5568', fontSize: 12, marginLeft: 'auto', alignSelf: 'center' }}>
          {filteredUsers.length} users
        </span>
      </div>

      {/* User cards */}
      {filteredUsers.map(u => {
        const color = ROLE_COLORS[u.role] || '#718096'
        const isMe = u.id === user?.id
        return (
          <div key={u.id} style={{
            ...s.card, borderLeft: `4px solid ${color}`,
            opacity: u.is_active ? 1 : 0.6
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                <div style={{
                  width: 44, height: 44, borderRadius: '50%',
                  background: `${color}22`, border: `2px solid ${color}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '1.1rem', fontWeight: 700, color, flexShrink: 0
                }}>{u.full_name?.[0]?.toUpperCase()}</div>
                <div>
                  <div style={{ color: '#E2E8F0', fontWeight: 600 }}>
                    {u.full_name}
                    {isMe && <span style={{ color: '#F6AD55', fontSize: 10, marginLeft: 6, fontWeight: 700 }}>YOU</span>}
                  </div>
                  <div style={{ color: '#4A5568', fontSize: 12 }}>{u.email}</div>
                  <div style={{ color: '#718096', fontSize: 11, marginTop: 1 }}>
                    {u.designation}{u.designation && u.department ? ' · ' : ''}{u.department || 'Unassigned'}
                  </div>
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ background: `${color}22`, color, fontSize: '0.6rem', padding: '2px 8px', borderRadius: 4, fontWeight: 700, letterSpacing: 2, border: `1px solid ${color}44` }}>
                  {u.role?.toUpperCase()}
                </span>
                <div style={{ color: u.is_active ? '#48BB78' : '#FF4D6D', fontSize: 11, marginTop: 4, fontWeight: 700 }}>
                  ● {u.is_active ? 'ACTIVE' : 'INACTIVE'}
                </div>
                <div style={{ color: '#4A5568', fontSize: 11 }}>ID #{u.id}</div>
              </div>
            </div>

            {!isMe && (
              <div style={{ display: 'flex', gap: 8, marginTop: 14, flexWrap: 'wrap' }}>
                <select style={{ ...s.select, fontSize: 11 }}
                  value={u.role} onChange={e => updateUser(u.id, { role: e.target.value })}>
                  {['viewer', 'auditor', 'admin'].map(r => <option key={r} value={r}>{r}</option>)}
                </select>
                <select style={{ ...s.select, fontSize: 11 }}
                  value={u.department || ''} onChange={e => updateUser(u.id, { department: e.target.value || null })}>
                  {DEPARTMENTS.map(d => <option key={d} value={d}>{d || 'No department'}</option>)}
                </select>
                <button onClick={() => updateUser(u.id, { is_active: !u.is_active })} style={s.btn(u.is_active ? '#FF4D6D' : '#48BB78')}>
                  {u.is_active ? '⏸ DEACTIVATE' : '▶ ACTIVATE'}
                </button>
              </div>
            )}
          </div>
        )
      })}
    </Layout>
  )
}

