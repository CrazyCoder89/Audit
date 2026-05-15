import Layout from '../components/Layout.jsx'
import PageHeader from '../components/PageHeader.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { useState, useEffect } from 'react'
import axios from 'axios'
const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
export default function Meetings() {
  const { apiGet, authHeaders, user } = useAuth()
  const [meetings, setMeetings] = useState([])
  const [title, setTitle] = useState('')
  const [joinCode, setJoinCode] = useState('')
  const [msg, setMsg] = useState('')
  const [loading, setLoading] = useState(false)

  const fetch = async () => {
    const data = await apiGet('/meetings/')
    setMeetings(data || [])
  }

  useEffect(() => { fetch() }, [])

  const createMeeting = async () => {
    if (!title.trim()) { setMsg('✗ Enter meeting title'); return }
    setLoading(true)
    try {
      const res = await axios.post('${BASE}/meetings/',
        { title },
        { headers: authHeaders() }
      )
      const roomCode = res.data.room_code
      const meetingId = res.data.id
      // Store token for meeting app
      localStorage.setItem('auditsys_token', localStorage.getItem('token'))
      localStorage.setItem('auditsys_user', localStorage.getItem('user'))
      // Open meeting in new tab
      window.open(`https://auditsys-meeting.vercel.app/room/${roomCode}`, '_blank')
      setTitle('')
      fetch()
    } catch (e) {
      setMsg('✗ Failed to create meeting')
    }
    setLoading(false)
  }

  const joinMeeting = async () => {
    if (!joinCode.trim()) { setMsg('✗ Enter room code'); return }
    try {
      const res = await axios.get(
        `${BASE}/meetings/${joinCode.toUpperCase()}`,
        { headers: authHeaders() }
      )
      if (res.data.status === 'ended') {
        setMsg('✗ This meeting has already ended')
        return
      }
      localStorage.setItem('auditsys_token', localStorage.getItem('token'))
      localStorage.setItem('auditsys_user', localStorage.getItem('user'))
      window.open(`https://auditsys-meeting.vercel.app/room/${joinCode.toUpperCase()}`, '_blank')
      setJoinCode('')
    } catch {
      setMsg('✗ Meeting not found')
    }
  }

  const STATUS_COLORS = { waiting: '#F6AD55', active: '#48BB78', ended: '#718096' }

  const s = {
    card: { background: '#0F1628', border: '1px solid #1E2D4D', borderRadius: 10, padding: 24, marginBottom: 20 },
    input: {
      width: '100%', background: '#0A0E1A', border: '1px solid #1E2D4D',
      borderRadius: 6, padding: '10px 14px', color: '#E2E8F0',
      fontFamily: 'monospace', fontSize: 13, outline: 'none',
      boxSizing: 'border-box', marginBottom: 12
    },
    btn: (color = '#00D4FF') => ({
      background: `linear-gradient(135deg,${color},${color}99)`,
      color: color === '#00D4FF' ? '#0A0E1A' : 'white',
      border: 'none', borderRadius: 6, padding: '10px 24px',
      fontWeight: 700, cursor: 'pointer', fontFamily: 'monospace',
      fontSize: 13, letterSpacing: 1, width: '100%'
    })
  }

  return (
    <Layout>
      <PageHeader title="◈ MEETINGS" subtitle="Create and join compliance review meetings" />

      {msg && (
        <div style={{
          color: msg.startsWith('✓') ? '#48BB78' : '#FF4D6D',
          background: msg.startsWith('✓') ? '#48BB7811' : '#FF4D6D11',
          border: `1px solid ${msg.startsWith('✓') ? '#48BB7833' : '#FF4D6D33'}`,
          borderRadius: 6, padding: '10px 16px', marginBottom: 16, fontSize: 13
        }}>{msg}</div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 24 }}>
        {/* Create */}
        <div style={{ ...s.card, borderTop: '3px solid #00D4FF' }}>
          <div style={{ fontSize: '0.65rem', color: '#4A5568', letterSpacing: 3, marginBottom: 16 }}>
            ✚ CREATE NEW MEETING
          </div>
          <input style={s.input} placeholder="Meeting title e.g. Q3 Compliance Review"
            value={title} onChange={e => setTitle(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && createMeeting()} />
          <button style={s.btn()} onClick={createMeeting} disabled={loading}>
            {loading ? 'CREATING...' : '⚡ START MEETING →'}
          </button>
        </div>

        {/* Join */}
        <div style={{ ...s.card, borderTop: '3px solid #48BB78' }}>
          <div style={{ fontSize: '0.65rem', color: '#4A5568', letterSpacing: 3, marginBottom: 16 }}>
            ◈ JOIN EXISTING MEETING
          </div>
          <input style={s.input} placeholder="Enter room code e.g. A1B2C3D4"
            value={joinCode} onChange={e => setJoinCode(e.target.value.toUpperCase())}
            onKeyDown={e => e.key === 'Enter' && joinMeeting()} />
          <button style={s.btn('#48BB78')} onClick={joinMeeting}>
            JOIN MEETING →
          </button>
        </div>
      </div>

      {/* Recent Meetings */}
      <div style={s.card}>
        <div style={{ fontSize: '0.65rem', color: '#4A5568', letterSpacing: 3, marginBottom: 16 }}>
          ◉ RECENT MEETINGS
        </div>

        {meetings.length === 0 ? (
          <div style={{ color: '#4A5568', fontSize: 13, textAlign: 'center', padding: '20px 0' }}>
            No meetings yet
          </div>
        ) : (
          meetings.map(m => {
            const sc = STATUS_COLORS[m.status] || '#718096'
            return (
              <div key={m.id} style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                background: '#0A0E1A', border: '1px solid #1E2D4D', borderRadius: 8,
                padding: '12px 16px', marginBottom: 8, borderLeft: '3px solid #00D4FF'
              }}>
                <div>
                  <div style={{ color: '#E2E8F0', fontWeight: 600, marginBottom: 4 }}>{m.title}</div>
                  <div style={{ fontSize: 11, color: '#4A5568' }}>
                    Code: <span style={{ color: '#00D4FF', fontWeight: 700 }}>{m.room_code}</span>
                    &nbsp;·&nbsp;
                    <span style={{ color: sc, fontWeight: 700 }}>{m.status?.toUpperCase()}</span>
                    &nbsp;·&nbsp;{m.created_at?.slice(0, 10)}
                  </div>
                </div>
                {m.status !== 'ended' && (
                  <button onClick={() => {
                    localStorage.setItem('auditsys_token', localStorage.getItem('token'))
                    localStorage.setItem('auditsys_user', localStorage.getItem('user'))
                    window.open(`https://auditsys-meeting.vercel.app/room/${m.room_code}`, '_blank')
                  }} style={{
                    background: '#00D4FF22', color: '#00D4FF',
                    border: '1px solid #00D4FF44', borderRadius: 6,
                    padding: '6px 16px', cursor: 'pointer',
                    fontFamily: 'monospace', fontSize: 11, fontWeight: 700
                  }}>JOIN →</button>
                )}
              </div>
            )
          })
        )}
      </div>
    </Layout>
  )
}


