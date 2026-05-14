export default function MetricCard({ label, value, delta, color = '#00D4FF' }) {
  return (
    <div style={{
      background: '#0F1628', border: '1px solid #1E2D4D',
      borderRadius: 10, padding: 20, borderTop: `3px solid ${color}`,
      minHeight: 110
    }}>
      <div style={{ fontSize: '0.65rem', color: '#4A5568',
                    letterSpacing: 3, marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: '2rem', fontWeight: 700,
                    color, fontFamily: 'monospace' }}>{value}</div>
      {delta && <div style={{ fontSize: '0.75rem', color: '#48BB78',
                              marginTop: 4 }}>{delta}</div>}
    </div>
  )
}



