import { useState } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import Layout from '../components/Layout.jsx'
import PageHeader from '../components/PageHeader.jsx'
import axios from 'axios'
const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const ROLE_COLORS = { admin: '#FF4D6D', auditor: '#00D4FF', viewer: '#48BB78', guest: '#718096' }

export default function Profile() {
  const { user, apiPatch, authHeaders } = useAuth()
  const [form, setForm] = useState({
    full_name: user?.full_name || '',
    designation: user?.designation || '',
    department: user?.department || ''
  })
  const [passForm, setPassForm] = useState({ current_password: '', new_password: '', confirm: '' })
  const [msg, setMsg] = useState('')
  const [passMsg, setPassMsg] = useState('')
  const color = ROLE_COLORS[user?.role] || '#718096'

  const saveProfile = async () => {
    const res = await apiPatch('/auth/me', form)
    if (res.status === 200) setMsg('✓ Profile updated')
    else setMsg('✗ ' + (res.data?.detail || 'Failed'))
  }

  const changePassword = async () => {
    if (!passForm.current_password || !passForm.new_password) { setPassMsg('Fill all fields'); return }
    if (passForm.new_password !== passForm.confirm) { setPassMsg('✗ Passwords do not match'); return }
    if (passForm.new_password.length < 6) { setPassMsg('✗ Min 6 characters'); return }
    try {
      const res = await axios.post('${BASE}/auth/me/change-password',
        { current_password: passForm.current_password, new_password: passForm.new_password },
        { headers: authHeaders() })
      setPassMsg('✓ Password changed')
      setPassForm({ current_password: '', new_password: '', confirm: '' })
    } catch (e) {
      setPassMsg('✗ ' + (e.response?.data?.detail || 'Failed'))
    }
  }

  const s = {
    card: { background: '#0F1628', border: '1px solid #1E2D4D', borderRadius: 10, padding: 24, marginBottom: 20 },
    input: {
      width: '100%', background: '#0A0E1A', border: '1px solid #1E2D4D',
      borderRadius: 6, padding: '10px 14px', color: '#E2E8F0',
      fontFamily: 'monospace', fontSize: 13, marginBottom: 12,
      outline: 'none', boxSizing: 'border-box'
    },
    label: { fontSize: '0.65rem', color: '#4A5568', letterSpacing: 3, marginBottom: 6, display: 'block' },
    btn: {
      background: 'linear-gradient(135deg,#00D4FF,#0088AA)', color: '#0A0E1A',
      border: 'none', borderRadius: 6, padding: '10px 24px',
      fontWeight: 700, cursor: 'pointer', fontFamily: 'monospace', fontSize: 13
    }
  }

  return (
    <Layout>
      <PageHeader title="◈ MY PROFILE" subtitle="Manage your account and personal details" />

      {/* Avatar card */}
      <div style={{ ...s.card, borderTop: `3px solid ${color}`, display: 'flex', alignItems: 'center', gap: 24 }}>
        <div style={{
          width: 70, height: 70, borderRadius: '50%',
          background: `${color}22`, border: `2px solid ${color}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '1.8rem', fontWeight: 700, color, flexShrink: 0
        }}>
          {user?.full_name?.[0]?.toUpperCase()}
        </div>
        <div>
          <div style={{ color: '#E2E8F0', fontSize: '1.2rem', fontWeight: 700 }}>{user?.full_name}</div>
          <div style={{ color: '#4A5568', fontSize: 13, marginTop: 2 }}>{user?.email}</div>
          <div style={{ display: 'flex', gap: 10, marginTop: 8, alignItems: 'center' }}>
            <span style={{
              background: `${color}22`, color, fontSize: '0.6rem',
              padding: '2px 8px', borderRadius: 4, fontWeight: 700,
              letterSpacing: 2, border: `1px solid ${color}44`
            }}>{user?.role?.toUpperCase()}</span>
            {user?.designation && <span style={{ color: '#718096', fontSize: 13 }}>{user.designation}</span>}
            {user?.department && <span style={{ color: '#4A5568', fontSize: 13 }}>· {user.department}</span>}
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Edit profile */}
        <div style={s.card}>
          <div style={{ fontSize: '0.65rem', color: '#4A5568', letterSpacing: 3, marginBottom: 20 }}>EDIT PROFILE</div>
          <label style={s.label}>FULL NAME</label>
          <input style={s.input} value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} />
          <label style={s.label}>DESIGNATION</label>
          <input style={s.input} placeholder="e.g. Senior Auditor" value={form.designation} onChange={e => setForm({ ...form, designation: e.target.value })} />
          <label style={s.label}>DEPARTMENT</label>
          <input style={s.input} placeholder="e.g. Finance & Compliance" value={form.department} onChange={e => setForm({ ...form, department: e.target.value })} />
          <label style={s.label}>EMAIL (read-only)</label>
          <input style={{ ...s.input, opacity: 0.5, cursor: 'not-allowed' }} value={user?.email} disabled />
          {msg && <div style={{ color: msg.startsWith('✓') ? '#48BB78' : '#FF4D6D', fontSize: 13, marginBottom: 10 }}>{msg}</div>}
          <button style={s.btn} onClick={saveProfile}>SAVE CHANGES →</button>
        </div>

        {/* Change password */}
        <div style={s.card}>
          <div style={{ fontSize: '0.65rem', color: '#4A5568', letterSpacing: 3, marginBottom: 20 }}>CHANGE PASSWORD</div>
          <label style={s.label}>CURRENT PASSWORD</label>
          <input style={s.input} type="password" value={passForm.current_password}
            onChange={e => setPassForm({ ...passForm, current_password: e.target.value })} />
          <label style={s.label}>NEW PASSWORD</label>
          <input style={s.input} type="password" placeholder="Min 6 characters" value={passForm.new_password}
            onChange={e => setPassForm({ ...passForm, new_password: e.target.value })} />
          <label style={s.label}>CONFIRM NEW PASSWORD</label>
          <input style={s.input} type="password" value={passForm.confirm}
            onChange={e => setPassForm({ ...passForm, confirm: e.target.value })} />
          {passMsg && <div style={{ color: passMsg.startsWith('✓') ? '#48BB78' : '#FF4D6D', fontSize: 13, marginBottom: 10 }}>{passMsg}</div>}
          <button style={s.btn} onClick={changePassword}>CHANGE PASSWORD →</button>
        </div>
      </div>
    </Layout>
  )
}



