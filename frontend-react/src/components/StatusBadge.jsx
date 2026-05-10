const COLORS = {
  pending: { bg: '#2D1F00', text: '#F6AD55', border: '#F6AD5544' },
  in_progress: { bg: '#001A20', text: '#00D4FF', border: '#00D4FF44' },
  completed: { bg: '#00200A', text: '#48BB78', border: '#48BB7844' },
  overdue: { bg: '#200010', text: '#FF4D6D', border: '#FF4D6D44' },
  processed: { bg: '#00200A', text: '#48BB78', border: '#48BB7844' },
  failed: { bg: '#200010', text: '#FF4D6D', border: '#FF4D6D44' },
  unknown: { bg: '#1A1A1A', text: '#718096', border: '#71809644' },
  waiting: { bg: '#2D1F00', text: '#F6AD55', border: '#F6AD5544' },
  active: { bg: '#00200A', text: '#48BB78', border: '#48BB7844' },
  ended: { bg: '#1A1A1A', text: '#718096', border: '#71809644' },
}

export default function StatusBadge({ status }) {
  const c = COLORS[status] || COLORS.unknown
  return (
    <span style={{
      background: c.bg, color: c.text, border: `1px solid ${c.border}`,
      padding: '2px 10px', borderRadius: 4, fontSize: '0.65rem',
      fontWeight: 700, letterSpacing: 2
    }}>
      {status?.replace('_', ' ').toUpperCase()}
    </span>
  )
}