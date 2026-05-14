export default function MinutesPanel({ minutes, onClose, onDownload, onGoHome }) {
  return (
    <div style={{
      height: '100%', display: 'flex', flexDirection: 'column',
      fontFamily: 'monospace'
    }}>
      <div style={{
        padding: '12px 16px', borderBottom: '1px solid #1E2D4D',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center'
      }}>
        <span style={{ color: '#48BB78', fontSize: 12, fontWeight: 700, letterSpacing: 2 }}>
          ◈ MEETING MINUTES
        </span>
        <button onClick={onClose} style={{
          background: 'none', border: 'none', color: '#4A5568',
          cursor: 'pointer', fontSize: 18
        }}>✕</button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>
        <div style={{
          background: '#0A0E1A', border: '1px solid #1E2D4D',
          borderRadius: 8, padding: 16, fontSize: 12,
          color: '#E2E8F0', lineHeight: 1.8, whiteSpace: 'pre-wrap'
        }}>
          {minutes?.minutes || 'No minutes generated yet'}
        </div>
      </div>

      <div style={{ padding: 12, borderTop: '1px solid #1E2D4D', display: 'flex', flexDirection: 'column', gap: 8 }}>
        <button onClick={onDownload} style={{
          width: '100%', background: 'linear-gradient(135deg, #48BB78, #2D8A50)',
          color: 'white', border: 'none', borderRadius: 6,
          padding: '10px', cursor: 'pointer', fontFamily: 'monospace',
          fontWeight: 700, fontSize: 12, letterSpacing: 2
        }}>
          ⬇ DOWNLOAD PDF MINUTES
        </button>
        <button onClick={onGoHome} style={{
          width: '100%', background: '#1E2D4D',
          color: '#E2E8F0', border: 'none', borderRadius: 6,
          padding: '10px', cursor: 'pointer', fontFamily: 'monospace',
          fontWeight: 700, fontSize: 12, letterSpacing: 2
        }}>
          ← GO TO LOBBY
        </button>
      </div>
    </div>
  )
}