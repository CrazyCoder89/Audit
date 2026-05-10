import { useState } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import { useNavigate } from 'react-router-dom'
import { Eye, EyeOff } from 'lucide-react'

export default function Login() {
  const { login, loading } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [tab, setTab] = useState('login')
  const [regData, setRegData] = useState({
    full_name: '', email: '', password: '',
    designation: '', role: 'viewer'
  })
  const [regError, setRegError] = useState('')
  const [regSuccess, setRegSuccess] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  const handleLogin = async () => {
    if (!email || !password) { setError('Enter credentials'); return }
    setError('')
    const result = await login(email, password)
    if (result.success) navigate('/')
    else setError(result.error)
  }

  const handleRegister = async () => {
    setRegError('')
    setRegSuccess('')
    if (!regData.full_name || !regData.email || !regData.password) {
      setRegError('Fill in all required fields'); return
    }
    try {
      const res = await fetch('http://localhost:8000/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(regData)
      })
      const data = await res.json()
      if (res.ok) setRegSuccess('Account created — sign in above')
      else setRegError(Array.isArray(data.detail) ? data.detail[0].msg : data.detail)
    } catch {
      setRegError('Server error')
    }
  }

  const s = {
    page: {
      minHeight: '100vh', background: '#0A0E1A', display: 'flex',
      alignItems: 'center', justifyContent: 'center',
      fontFamily: "'JetBrains Mono', monospace",
      backgroundImage: 'linear-gradient(rgba(0,212,255,0.02) 1px,transparent 1px),linear-gradient(90deg,rgba(0,212,255,0.02) 1px,transparent 1px)',
      backgroundSize: '50px 50px'
    },
    card: {
      background: '#0F1628', border: '1px solid #1E2D4D',
      borderRadius: 12, padding: 36, width: '100%', maxWidth: 420
    },
    input: {
      width: '100%', background: '#0A0E1A', border: '1px solid #1E2D4D',
      borderRadius: 6, padding: '10px 14px', color: '#E2E8F0',
      fontFamily: 'monospace', fontSize: 13, marginBottom: 12,
      outline: 'none', boxSizing: 'border-box'
    },
    label: { fontSize: '0.65rem', color: '#4A5568', letterSpacing: 3,
             marginBottom: 6, display: 'block' },
    btn: {
      width: '100%', background: 'linear-gradient(135deg,#00D4FF,#0088AA)',
      color: '#0A0E1A', border: 'none', borderRadius: 6, padding: '11px',
      fontWeight: 700, cursor: 'pointer', fontFamily: 'monospace',
      letterSpacing: 2, fontSize: 13, marginTop: 4
    },
    tab: (active) => ({
      flex: 1, padding: '10px', background: active ? '#0F1628' : 'transparent',
      border: 'none', borderBottom: active ? '2px solid #00D4FF' : '2px solid transparent',
      color: active ? '#00D4FF' : '#4A5568', cursor: 'pointer',
      fontFamily: 'monospace', fontSize: '0.75rem', letterSpacing: 2
    }),
    error: { color: '#FF4D6D', fontSize: 12, marginBottom: 10 },
    success: { color: '#48BB78', fontSize: 12, marginBottom: 10 },
    select: {
      width: '100%', background: '#0A0E1A', border: '1px solid #1E2D4D',
      borderRadius: 6, padding: '10px 14px', color: '#E2E8F0',
      fontFamily: 'monospace', fontSize: 13, marginBottom: 12,
      outline: 'none', boxSizing: 'border-box'
    }
  }

  return (
    <div style={s.page}>
      <div>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ fontSize: '3rem' }}>⚡</div>
          <div style={{ color: '#E2E8F0', fontSize: '2rem', fontWeight: 700, letterSpacing: 6 }}>
            AUDIT<span style={{ color: '#00D4FF' }}>SYS</span>
          </div>
          <div style={{ color: '#4A5568', fontSize: '0.7rem', letterSpacing: 5, marginTop: 4 }}>
            AI-POWERED COMPLIANCE INTELLIGENCE
          </div>
          <div style={{ width: 60, height: 2, background: 'linear-gradient(90deg,transparent,#00D4FF,transparent)', margin: '16px auto 0' }} />
        </div>

        <div style={s.card}>
          {/* Tabs */}
          <div style={{ display: 'flex', marginBottom: 24, borderBottom: '1px solid #1E2D4D' }}>
            <button style={s.tab(tab === 'login')} onClick={() => setTab('login')}>◈ SIGN IN</button>
            <button style={s.tab(tab === 'register')} onClick={() => setTab('register')}>◈ REGISTER</button>
          </div>

          {tab === 'login' ? (
            <>
              <label style={s.label}>EMAIL</label>
              <input style={s.input} type="email" placeholder="admin@company.com"
                value={email} onChange={e => setEmail(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleLogin()} />
              <label style={s.label}>PASSWORD</label>
              <div style={{ position: 'relative' }}>
                <input style={s.input} type={showPassword ? 'text' : 'password'} placeholder="••••••••"
                  value={password} onChange={e => setPassword(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleLogin()} />
                <button style={{ position: 'absolute', right: 10, top: 10, background: 'none', border: 'none', color: '#4A5568', cursor: 'pointer' }}
                  onClick={() => setShowPassword(!showPassword)}>
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {error && <div style={s.error}>✗ {error}</div>}
              <button style={s.btn} onClick={handleLogin} disabled={loading}>
                {loading ? 'AUTHENTICATING...' : 'AUTHENTICATE →'}
              </button>
            </>
          ) : (
            <>
              <label style={s.label}>FULL NAME *</label>
              <input style={s.input} placeholder="John Smith"
                value={regData.full_name}
                onChange={e => setRegData({ ...regData, full_name: e.target.value })} />
              <label style={s.label}>EMAIL *</label>
              <input style={s.input} type="email" placeholder="john@company.com"
                value={regData.email}
                onChange={e => setRegData({ ...regData, email: e.target.value })} />
              <label style={s.label}>DESIGNATION</label>
              <input style={s.input} placeholder="Senior Auditor"
                value={regData.designation}
                onChange={e => setRegData({ ...regData, designation: e.target.value })} />
              <label style={s.label}>PASSWORD *</label>
              <input style={s.input} type="password" placeholder="Min 6 characters"
                value={regData.password}
                onChange={e => setRegData({ ...regData, password: e.target.value })} />
              <label style={s.label}>ROLE</label>
              <select style={s.select} value={regData.role}
                onChange={e => setRegData({ ...regData, role: e.target.value })}>
                <option value="viewer">Viewer</option>
                <option value="auditor">Auditor</option>
                <option value="admin">Admin</option>
              </select>
              {regError && <div style={s.error}>✗ {regError}</div>}
              {regSuccess && <div style={s.success}>✓ {regSuccess}</div>}
              <button style={s.btn} onClick={handleRegister}>
                CREATE ACCOUNT →
              </button>
            </>
          )}
        </div>

        <div style={{ textAlign: 'center', color: '#1E2D4D', fontSize: '0.65rem',
                      letterSpacing: 2, marginTop: 24 }}>
          SECURED · COMPLIANT · INTELLIGENT
        </div>
      </div>
    </div>
  )
}


