import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import {
  LayoutDashboard, FileText, MessageSquare, CheckSquare,
  Shield, Settings, Search, BarChart2, User, Users,
  LogOut, Zap, Video
} from 'lucide-react'

const ROLE_COLORS = {
  admin: '#FF4D6D', auditor: '#00D4FF',
  viewer: '#48BB78', guest: '#718096'
}

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const role = user?.role || 'viewer'
  const color = ROLE_COLORS[role] || '#718096'

  const navItems = [
    { path: '/', icon: <LayoutDashboard size={16} />, label: 'Dashboard', roles: ['admin','auditor','viewer','guest'] },
    { path: '/documents', icon: <FileText size={16} />, label: 'Documents', roles: ['admin','auditor','viewer'] },
    { path: '/ask-ai', icon: <MessageSquare size={16} />, label: 'Ask AI', roles: ['admin','auditor','viewer'] },
    { path: '/tasks', icon: <CheckSquare size={16} />, label: 'Tasks', roles: ['admin','auditor','viewer'] },
    { path: '/search', icon: <Search size={16} />, label: 'Search', roles: ['admin','auditor','viewer'] },
    { path: '/meetings', icon: <Video size={16} />, label: 'Meetings', roles: ['admin','auditor','viewer','guest'] },
    { path: '/audit-logs', icon: <Shield size={16} />, label: 'Audit Logs', roles: ['admin','auditor'] },
    { path: '/analytics', icon: <BarChart2 size={16} />, label: 'Analytics', roles: ['admin','auditor'] },
    { path: '/profile', icon: <User size={16} />, label: 'My Profile', roles: ['admin','auditor','viewer','guest'] },
    { path: '/admin', icon: <Settings size={16} />, label: 'Admin Panel', roles: ['admin'] },
    { path: '/users', icon: <Users size={16} />, label: 'User Management', roles: ['admin'] },
  ]

  const s = {
    app: { display: 'flex', height: '100vh', background: '#0A0E1A',
           fontFamily: "'JetBrains Mono', monospace", overflow: 'hidden' },
    sidebar: { width: 220, background: '#0A0E1A', borderRight: '1px solid #1E2D4D',
               display: 'flex', flexDirection: 'column', flexShrink: 0 },
    logo: { padding: '24px 20px', borderBottom: '1px solid #1E2D4D', textAlign: 'center' },
    logoText: { color: '#00D4FF', fontSize: '1.2rem', fontWeight: 700, letterSpacing: 3 },
    logoSub: { color: '#4A5568', fontSize: '0.55rem', letterSpacing: 4, marginTop: 2 },
    userBadge: {
      margin: '12px', background: '#0F1628', border: '1px solid #1E2D4D',
      borderLeft: `3px solid ${color}`, borderRadius: 8, padding: '10px 12px'
    },
    nav: { flex: 1, padding: '8px 0', overflowY: 'auto' },
    navItem: (active) => ({
      display: 'flex', alignItems: 'center', gap: 10,
      padding: '9px 16px', cursor: 'pointer', fontSize: '0.78rem',
      color: active ? '#00D4FF' : '#4A5568',
      background: active ? '#0F1628' : 'transparent',
      borderLeft: active ? '2px solid #00D4FF' : '2px solid transparent',
      transition: 'all 0.15s'
    }),
    main: { flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' },
    content: { flex: 1, overflowY: 'auto', padding: 24 },
    logoutBtn: {
      margin: 12, padding: '9px 16px', background: 'none',
      border: '1px solid #1E2D4D', borderRadius: 6, color: '#4A5568',
      cursor: 'pointer', fontFamily: 'monospace', fontSize: '0.75rem',
      display: 'flex', alignItems: 'center', gap: 8, width: 'calc(100% - 24px)'
    }
  }

  return (
    <div style={s.app}>
      {/* Sidebar */}
      <div style={s.sidebar}>
        <div style={s.logo}>
          <div style={{ fontSize: '1.5rem' }}>⚡</div>
          <div style={s.logoText}>AUDIT<span style={{ color: '#E2E8F0' }}>SYS</span></div>
          <div style={s.logoSub}>COMPLIANCE INTELLIGENCE</div>
        </div>

        {/* User badge */}
        <div style={s.userBadge}>
          <div style={{ fontSize: '0.6rem', color: '#4A5568', letterSpacing: 2 }}>LOGGED IN AS</div>
          <div style={{ color: '#E2E8F0', fontWeight: 600, fontSize: '0.85rem', marginTop: 2 }}>
            {user?.full_name}
          </div>
          {user?.designation && (
            <div style={{ color: '#718096', fontSize: '0.7rem', marginTop: 1 }}>{user.designation}</div>
          )}
          <span style={{
            display: 'inline-block', background: `${color}22`, color,
            fontSize: '0.6rem', padding: '2px 8px', borderRadius: 4,
            marginTop: 4, fontWeight: 700, letterSpacing: 2,
            border: `1px solid ${color}44`
          }}>{role.toUpperCase()}</span>
        </div>

        {/* Navigation */}
        <div style={s.nav}>
          <div style={{ fontSize: '0.6rem', color: '#4A5568', letterSpacing: 3, padding: '4px 16px 8px' }}>
            NAVIGATION
          </div>
          {navItems
            .filter(item => item.roles.includes(role))
            .map(item => (
              <div key={item.path}
                style={s.navItem(location.pathname === item.path)}
                onClick={() => navigate(item.path)}>
                {item.icon}
                {item.label}
              </div>
            ))}

          {/* Meeting link */}
          <div style={{ fontSize: '0.6rem', color: '#4A5568', letterSpacing: 3, padding: '12px 16px 8px' }}>
            TOOLS
          </div>
          <div style={s.navItem(false)}
            onClick={() => window.open('http://localhost:5173', '_blank')}>
            <Video size={16} />
            Meetings
          </div>
        </div>

        <button style={s.logoutBtn} onClick={logout}>
          <LogOut size={14} /> LOGOUT
        </button>
      </div>

      {/* Main content */}
      <div style={s.main}>
        <div style={s.content}>
          {children}
        </div>
      </div>
    </div>
  )
}


