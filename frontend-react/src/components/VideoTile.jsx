import { useEffect, useRef } from 'react'

export default function VideoTile({ stream, name, muted, cameraOff, isSelf }) {
  const videoRef = useRef(null)

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream
    }
  }, [stream])

  return (
    <div style={{
      background: '#0F1628', borderRadius: 12,
      border: '1px solid #1E2D4D', position: 'relative',
      overflow: 'hidden', display: 'flex',
      alignItems: 'center', justifyContent: 'center',
      minHeight: 200
    }}>
      {/* Video element */}
      {!cameraOff && stream ? (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted={muted}
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />
      ) : (
        <div style={{
          width: 80, height: 80, borderRadius: '50%',
          background: '#1E2D4D', display: 'flex',
          alignItems: 'center', justifyContent: 'center',
          fontSize: '2rem', color: '#00D4FF', fontWeight: 700
        }}>
          {name?.[0]?.toUpperCase() || '?'}
        </div>
      )}

      {/* Name badge */}
      <div style={{
        position: 'absolute', bottom: 10, left: 10,
        background: 'rgba(10,14,26,0.8)', borderRadius: 6,
        padding: '4px 10px', fontSize: 12, color: '#E2E8F0',
        fontFamily: 'monospace'
      }}>
        {name}
        {isSelf && <span style={{ color: '#00D4FF', marginLeft: 6 }}>●</span>}
      </div>
    </div>
  )
}


