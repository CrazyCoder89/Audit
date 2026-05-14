import { Mic, MicOff, Video, VideoOff, MessageSquare,
         PhoneOff, FileText } from 'lucide-react'

export default function Controls({
  muted, cameraOff, chatOpen,
  onToggleMute, onToggleCamera, onToggleChat,
  onEndMeeting, generating, hasMinutes, onViewMinutes
}) {
  const btn = (onClick, children, color = '#1E2D4D', textColor = '#E2E8F0') => (
    <button onClick={onClick} style={{
      background: color, border: 'none', borderRadius: 50,
      width: 48, height: 48, cursor: 'pointer', color: textColor,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      transition: 'all 0.2s'
    }}>
      {children}
    </button>
  )

  return (
    <div style={{
      background: '#0F1628', borderTop: '1px solid #1E2D4D',
      padding: '16px 24px', display: 'flex',
      justifyContent: 'center', alignItems: 'center',
      gap: 16, flexShrink: 0
    }}>
      {btn(onToggleMute, muted ? <MicOff size={20} /> : <Mic size={20} />,
        muted ? '#FF4D6D22' : '#1E2D4D', muted ? '#FF4D6D' : '#E2E8F0')}

      {btn(onToggleCamera, cameraOff ? <VideoOff size={20} /> : <Video size={20} />,
        cameraOff ? '#FF4D6D22' : '#1E2D4D', cameraOff ? '#FF4D6D' : '#E2E8F0')}

      {btn(onToggleChat, <MessageSquare size={20} />,
        chatOpen ? '#00D4FF22' : '#1E2D4D', chatOpen ? '#00D4FF' : '#E2E8F0')}

      {hasMinutes && btn(onViewMinutes, <FileText size={20} />,
        '#48BB7822', '#48BB78')}

      <button onClick={onEndMeeting} disabled={generating} style={{
        background: generating ? '#4A5568' : '#FF4D6D',
        color: 'white', border: 'none', borderRadius: 24,
        padding: '12px 28px', cursor: 'pointer', fontFamily: 'monospace',
        fontWeight: 700, fontSize: 13, letterSpacing: 2
      }}>
        {generating ? '⚡ GENERATING MINUTES...' : '⏹ END MEETING'}
      </button>
    </div>
  )
}
