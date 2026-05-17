import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

export default function Lobby() {
  const navigate = useNavigate()
  const [token, setToken] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loggedIn, setLoggedIn] = useState(false)
  const [user, setUser] = useState(null)
  const [meetingTitle, setMeetingTitle] = useState('')
  const [joinCode, setJoinCode] = useState('')
  const [meetings, setMeetings] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const t = localStorage.getItem('auditsys_token')
    const u = localStorage.getItem('auditsys_user')
    if (t && u) {
      setToken(t)
      setUser(JSON.parse(u))
      setLoggedIn(true)
      fetchMeetings(t)
    }
  }, [])

  const login = async (emailVal, passwordVal) => {
    setLoading(true)
    setError('')
    try {
      const res = await axios.post(
        `${API}/auth/login`,
        { email: emailVal, password: passwordVal },
        { headers: { 'Content-Type': 'application/json' } }
      )
      const t = res.data.access_token
      const me = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${t}` }
      })

      // ✅ Fixed: use auditsys_ prefix keys
      localStorage.setItem('auditsys_token', t)
      localStorage.setItem('auditsys_user', JSON.stringify(me.data))

      setToken(t)
      setUser(me.data)
      setLoggedIn(true)
      fetchMeetings(t)
      setLoading(false)
      return { success: true }
    } catch (e) {
      setLoading(false)
      const errMsg = e.response?.data?.detail || 'Invalid credentials'
      setError(errMsg)
      return { success: false, error: errMsg }
    }
  }

  const fetchMeetings = async (t) => {
    try {
      const res = await axios.get(`${API}/meetings/`,
        { headers: { Authorization: `Bearer ${t}` } })
      setMeetings(res.data)
    } catch {}
  }

  const createMeeting = async () => {
    if (!meetingTitle.trim()) return
    setLoading(true)
    setError('')
    try {
      const res = await axios.post(`${API}/meetings/`,
        { title: meetingTitle },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      navigate(`/room/${res.data.room_code}`, {
        state: { token, user, meetingId: res.data.id }
      })
    } catch (e) {
      if (e.response?.status === 401) {
        setError('Session expired. Please log out and log in again.')
      } else {
        setError('Failed to create meeting. Try again.')
      }
    }
    setLoading(false)
  }

  const joinMeeting = async () => {
    if (!joinCode.trim()) return
    setError('')
    try {
      const res = await axios.get(`${API}/meetings/${joinCode.toUpperCase()}`,
        { headers: { Authorization: `Bearer ${token}` } })
      if (res.data.status === 'ended') {
        setError('This meeting has already ended and cannot be joined.')
        return
      }
      navigate(`/room/${joinCode.toUpperCase()}`, {
        state: { token, user, meetingId: res.data.id }
      })
    } catch {
      setError('Meeting not found. Check the room code and try again.')
    }
  }

  const logout = () => {
    localStorage.clear()
    setLoggedIn(false)
    setToken('')
    setUser(null)
    setError('')
  }

  const styles = {
    app: {
      minHeight: '100vh', background: '#0A0E1A', color: '#E2E8F0',
      fontFamily: "'JetBrains Mono', monospace",
      backgroundImage: 'linear-gradient(rgba(0,212,255,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(0,212,255,0.02) 1px, transparent 1px)',
      backgroundSize: '50px 50px'
    },
    nav: {
      background: '#0F1628', borderBottom: '1px solid #1E2D4D',
      padding: '14px 32px', display: 'flex',
      justifyContent: 'space-between', alignItems: 'center'
    },
    logo: { color: '#00D4FF', fontSize: '1.3rem', fontWeight: 700, letterSpacing: 3 },
    container: { maxWidth: 900, margin: '0 auto', padding: '40px 20px' },
    card: {
      background: '#0F1628', border: '1px solid #1E2D4D',
      borderRadius: 10, padding: 24, marginBottom: 20
    },
    input: {
      width: '100%', background: '#0A0E1A', border: '1px solid #1E2D4D',
      borderRadius: 6, padding: '10px 14px', color: '#E2E8F0',
      fontFamily: 'monospace', fontSize: 14, marginBottom: 12,
      outline: 'none', boxSizing: 'border-box'
    },
    btn: {
      background: 'linear-gradient(135deg, #00D4FF, #0088AA)',
      color: '#0A0E1A', border: 'none', borderRadius: 6,
      padding: '10px 24px', fontWeight: 700, cursor: 'pointer',
      fontFamily: 'monospace', letterSpacing: 2, fontSize: 13
    },
    btnRed: {
      background: 'linear-gradient(135deg, #FF4D6D, #AA0033)',
      color: 'white', border: 'none', borderRadius: 6,
      padding: '8px 18px', fontWeight: 700, cursor: 'pointer',
      fontFamily: 'monospace', fontSize: 12
    },
    label: { fontSize: '0.7rem', color: '#4A5568', letterSpacing: 3, marginBottom: 8, display: 'block' },
    error: { color: '#FF4D6D', fontSize: 13, marginBottom: 12 },
    meetingCard: {
      background: '#0A0E1A', border: '1px solid #1E2D4D',
      borderRadius: 8, padding: '12px 16px', marginBottom: 8,
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      borderLeft: '3px solid #00D4FF'
    }
  }

  if (!loggedIn) {
    return (
      <div style={styles.app}>
        <div style={styles.nav}>
          <div style={styles.logo}>⚡ AUDITSYS MEET</div>
        </div>
        <div style={styles.container}>
          <div style={{ textAlign: 'center', marginBottom: 40 }}>
            <div style={{ fontSize: '3rem' }}>⚡</div>
            <h1 style={{ color: '#E2E8F0', letterSpacing: 4 }}>AUDITSYS MEET</h1>
            <p style={{ color: '#4A5568' }}>Sign in with your AuditSys account</p>
          </div>
          <div style={{ ...styles.card, maxWidth: 400, margin: '0 auto', borderTop: '3px solid #00D4FF' }}>
            <span style={styles.label}>EMAIL</span>
            <input
              style={styles.input}
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && login(email, password)}
            />
            <span style={styles.label}>PASSWORD</span>
            <input
              style={styles.input}
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={e => setPassword(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && login(email, password)}
            />
            {error && <div style={styles.error}>✗ {error}</div>}
            <button
              style={{ ...styles.btn, width: '100%' }}
              onClick={() => login(email, password)}
              disabled={loading}>
              {loading ? 'SIGNING IN...' : 'SIGN IN →'}
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.app}>
      <div style={styles.nav}>
        <div style={styles.logo}>⚡ AUDITSYS MEET</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span style={{ color: '#4A5568', fontSize: 13 }}>
            {user?.full_name} · <span style={{ color: '#00D4FF' }}>{user?.role}</span>
          </span>
          <button style={styles.btnRed} onClick={logout}>LOGOUT</button>
        </div>
      </div>

      <div style={styles.container}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 32 }}>

          {/* Create Meeting */}
          <div style={{ ...styles.card, borderTop: '3px solid #00D4FF' }}>
            <div style={{ ...styles.label, marginBottom: 16 }}>✚ CREATE NEW MEETING</div>
            <span style={styles.label}>MEETING TITLE</span>
            <input
              style={styles.input}
              placeholder="e.g. Q3 Compliance Review"
              value={meetingTitle}
              onChange={e => setMeetingTitle(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && createMeeting()}
            />
            {error && <div style={styles.error}>✗ {error}</div>}
            <button
              style={{ ...styles.btn, width: '100%' }}
              onClick={createMeeting}
              disabled={loading}>
              {loading ? 'CREATING...' : '⚡ START MEETING →'}
            </button>
          </div>

          {/* Join Meeting */}
          <div style={{ ...styles.card, borderTop: '3px solid #48BB78' }}>
            <div style={{ ...styles.label, marginBottom: 16 }}>◈ JOIN EXISTING MEETING</div>
            <span style={styles.label}>ROOM CODE</span>
            <input
              style={styles.input}
              placeholder="e.g. A1B2C3D4"
              value={joinCode}
              onChange={e => setJoinCode(e.target.value.toUpperCase())}
              onKeyDown={e => e.key === 'Enter' && joinMeeting()}
            />
            <button
              style={{ ...styles.btn, width: '100%', background: 'linear-gradient(135deg, #48BB78, #2D8A50)' }}
              onClick={joinMeeting}>
              JOIN MEETING →
            </button>
          </div>
        </div>

        {/* Recent Meetings */}
        <div style={styles.card}>
          <div style={{ ...styles.label, marginBottom: 16 }}>◉ RECENT MEETINGS</div>
          {meetings.length === 0 && (
            <p style={{ color: '#4A5568', fontSize: 13 }}>No meetings yet</p>
          )}
          {meetings.map(m => (
            <div key={m.id} style={styles.meetingCard}>
              <div>
                <div style={{ color: '#E2E8F0', fontWeight: 600 }}>{m.title}</div>
                <div style={{ color: '#4A5568', fontSize: 12, marginTop: 2 }}>
                  Code: <span style={{ color: '#00D4FF' }}>{m.room_code}</span>
                  &nbsp;·&nbsp;
                  <span style={{
                    color: m.status === 'active' ? '#48BB78' : m.status === 'ended' ? '#718096' : '#F6AD55'
                  }}>{m.status.toUpperCase()}</span>
                  &nbsp;·&nbsp;{m.created_at?.slice(0, 10)}
                </div>
              </div>
              {m.status !== 'ended' ? (
                <button style={styles.btn} onClick={() =>
                  navigate(`/room/${m.room_code}`, {
                    state: { token, user, meetingId: m.id }
                  })}>
                  JOIN
                </button>
              ) : (
                <span style={{
                  color: '#718096', fontSize: 11, fontFamily: 'monospace',
                  background: '#1E2D4D', padding: '4px 10px', borderRadius: 4
                }}>
                  ENDED
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

