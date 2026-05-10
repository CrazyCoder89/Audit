import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useLocation, useNavigate } from 'react-router-dom'
import SimplePeer from 'simple-peer'
import axios from 'axios'
import VideoTile from '../components/VideoTile.jsx'
import Controls from '../components/Controls.jsx'
import ChatPanel from '../components/ChatPanel.jsx'
import MinutesPanel from '../components/MinutesPanel.jsx'

const API = 'http://localhost:8000'
const WS_BASE = 'ws://localhost:8000'

export default function Room() {
  const { roomCode } = useParams()
  const { state } = useLocation()
  const navigate = useNavigate()

  const token = state?.token || localStorage.getItem('auditsys_token')
  const user = state?.user || JSON.parse(localStorage.getItem('auditsys_user') || '{}')
  const meetingId = state?.meetingId

  const [peers, setPeers] = useState({})           // userId -> peer instance
  const [streams, setStreams] = useState({})        // userId -> MediaStream
  const [peerNames, setPeerNames] = useState({})   // userId -> name
  const [localStream, setLocalStream] = useState(null)
  const [muted, setMuted] = useState(false)
  const [cameraOff, setCameraOff] = useState(false)
  const [chatOpen, setChatOpen] = useState(false)
  const [minutesOpen, setMinutesOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [minutes, setMinutes] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [participants, setParticipants] = useState([])
  const [connected, setConnected] = useState(false)

  const wsRef = useRef(null)
  const peersRef = useRef({})
  const localStreamRef = useRef(null)
  const transcriptRef = useRef('')

  // ── Get local media ──────────────────────────────────────────────────────
  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ video: true, audio: true })
      .then(stream => {
        setLocalStream(stream)
        localStreamRef.current = stream
        connectWS()
      })
      .catch(err => {
        console.error('Media error:', err)
        // Continue without media
        connectWS()
      })

    return () => {
      localStreamRef.current?.getTracks().forEach(t => t.stop())
      wsRef.current?.close()
      Object.values(peersRef.current).forEach(p => p.destroy())
    }
  }, [])

  // ── WebSocket connection ─────────────────────────────────────────────────
  const connectWS = useCallback(() => {
    const ws = new WebSocket(
      `${WS_BASE}/meetings/ws/${roomCode}/${user.id}`
    )
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      console.log('[WS] Connected to room', roomCode)
    }

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      handleSignal(msg)
    }

    ws.onclose = () => {
      setConnected(false)
      console.log('[WS] Disconnected')
    }
  }, [roomCode, user.id])

  // ── Handle signaling messages ────────────────────────────────────────────
  const handleSignal = (msg) => {
    switch (msg.type) {

      case 'room_info':
        setParticipants(msg.participants || [])
        // Create offers to all existing participants
        if (localStreamRef.current) {
          msg.participants.forEach(pid => {
            if (pid !== user.id) createPeer(pid, true)
          })
        }
        break

      case 'user_joined':
        setParticipants(msg.participants || [])
        setPeerNames(prev => ({ ...prev, [msg.user_id]: msg.user_name }))
        // They will send us an offer, we wait
        break

      case 'user_left':
        setParticipants(msg.participants || [])
        removePeer(msg.user_id)
        break

      case 'offer':
        setPeerNames(prev => ({ ...prev, [msg.from_user_id]: msg.from_user_name }))
        createPeer(msg.from_user_id, false, msg.sdp)
        break

      case 'answer':
        if (peersRef.current[msg.from_user_id]) {
          peersRef.current[msg.from_user_id].signal(msg.sdp)
        }
        break

      case 'ice_candidate':
        if (peersRef.current[msg.from_user_id]) {
          peersRef.current[msg.from_user_id].signal(msg.candidate)
        }
        break

      case 'chat':
        setMessages(prev => [...prev, msg])
        break

      case 'mute_toggle':
        // Update UI for remote user mute status
        break

      case 'meeting_ended':
        // Only participants (not the host who ended it) get redirected
        if (meetingId) {
            alert('The host has ended the meeting.')
            localStreamRef.current?.getTracks().forEach(t => t.stop())
            wsRef.current?.close()
            navigate('/')
        }
        break

      default:
        break
    }
  }

  // ── Create WebRTC peer ────────────────────────────────────────────────────
  const createPeer = (targetUserId, initiator, remoteSdp = null) => {
    if (peersRef.current[targetUserId]) return

    const peer = new SimplePeer({
      initiator,
      stream: localStreamRef.current || undefined,
      trickle: true
    })

    peer.on('signal', (data) => {
      if (!wsRef.current) return
      if (data.type === 'offer') {
        wsRef.current.send(JSON.stringify({
          type: 'offer', target_user_id: targetUserId, sdp: data
        }))
      } else if (data.type === 'answer') {
        wsRef.current.send(JSON.stringify({
          type: 'answer', target_user_id: targetUserId, sdp: data
        }))
      } else {
        wsRef.current.send(JSON.stringify({
          type: 'ice_candidate', target_user_id: targetUserId, candidate: data
        }))
      }
    })

    peer.on('stream', (remoteStream) => {
      setStreams(prev => ({ ...prev, [targetUserId]: remoteStream }))
    })

    peer.on('error', (err) => console.error('[PEER ERROR]', err))

    peer.on('close', () => removePeer(targetUserId))

    if (remoteSdp) peer.signal(remoteSdp)

    peersRef.current[targetUserId] = peer
    setPeers(prev => ({ ...prev, [targetUserId]: peer }))
  }

  const removePeer = (userId) => {
    if (peersRef.current[userId]) {
      peersRef.current[userId].destroy()
      delete peersRef.current[userId]
    }
    setPeers(prev => { const n = { ...prev }; delete n[userId]; return n })
    setStreams(prev => { const n = { ...prev }; delete n[userId]; return n })
  }

  // ── Controls ─────────────────────────────────────────────────────────────
  const toggleMute = () => {
    if (localStreamRef.current) {
      localStreamRef.current.getAudioTracks().forEach(t => t.enabled = muted)
      setMuted(!muted)
      wsRef.current?.send(JSON.stringify({ type: 'mute_toggle', muted: !muted }))
    }
  }

  const toggleCamera = () => {
    if (localStreamRef.current) {
      localStreamRef.current.getVideoTracks().forEach(t => t.enabled = cameraOff)
      setCameraOff(!cameraOff)
      wsRef.current?.send(JSON.stringify({ type: 'camera_toggle', camera_off: !cameraOff }))
    }
  }

const sendChat = (message) => {
    wsRef.current?.send(JSON.stringify({ type: 'chat', message }))
  }

const endMeeting = async () => {
    setGenerating(true)
    try {
      await axios.post(`${API}/meetings/${meetingId}/end`, {},
        { headers: { Authorization: `Bearer ${token}` } })

      // Broadcast meeting ended to all participants except host
      wsRef.current?.send(JSON.stringify({ type: 'meeting_ended' }))

      // Generate minutes
      await axios.post(`${API}/meetings/${meetingId}/generate-minutes`, {},
        { headers: { Authorization: `Bearer ${token}` } })

      const res = await axios.get(`${API}/meetings/${meetingId}/minutes`,
        { headers: { Authorization: `Bearer ${token}` } })
      setMinutes(res.data)
      setMinutesOpen(true)
      setChatOpen(false)

    } catch (e) {
      console.error(e)
    }
    setGenerating(false)
    localStreamRef.current?.getTracks().forEach(t => t.stop())
    wsRef.current?.close()
    // Host stays on screen to download minutes — no auto redirect
  }

  const downloadMinutes = async () => {
    const res = await axios.get(
      `${API}/meetings/${meetingId}/download-minutes`,
      { headers: { Authorization: `Bearer ${token}` }, responseType: 'blob' }
    )
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url
    a.download = `minutes_${roomCode}.pdf`
    a.click()
  }

  // ── Styles ────────────────────────────────────────────────────────────────
  const s = {
    room: {
      height: '100vh', background: '#0A0E1A', display: 'flex',
      flexDirection: 'column', fontFamily: 'monospace', overflow: 'hidden'
    },
    header: {
      background: '#0F1628', borderBottom: '1px solid #1E2D4D',
      padding: '10px 20px', display: 'flex',
      justifyContent: 'space-between', alignItems: 'center', flexShrink: 0
    },
    logo: { color: '#00D4FF', fontWeight: 700, letterSpacing: 3 },
    roomInfo: { color: '#4A5568', fontSize: 12 },
    grid: {
      flex: 1, display: 'grid', padding: 16, gap: 12, overflow: 'hidden',
      gridTemplateColumns: Object.keys(streams).length === 0
        ? '1fr'
        : Object.keys(streams).length === 1
        ? '1fr 1fr'
        : 'repeat(auto-fit, minmax(280px, 1fr))'
    },
    sidebar: {
      width: chatOpen || minutesOpen ? 320 : 0,
      background: '#0F1628', borderLeft: '1px solid #1E2D4D',
      transition: 'width 0.3s', overflow: 'hidden', flexShrink: 0
    }
  }

  return (
    <div style={s.room}>
      {/* Header */}
      <div style={s.header}>
        <div style={s.logo}>⚡ AUDITSYS MEET</div>
        <div style={s.roomInfo}>
          Room: <span style={{ color: '#00D4FF', fontWeight: 700 }}>{roomCode}</span>
          &nbsp;·&nbsp;
          {participants.length} participant{participants.length !== 1 ? 's' : ''}
          &nbsp;·&nbsp;
          <span style={{ color: connected ? '#48BB78' : '#FF4D6D' }}>
            {connected ? '● LIVE' : '● DISCONNECTED'}
          </span>
        </div>
        <button onClick={() => navigate('/')} style={{
          background: 'none', border: '1px solid #1E2D4D',
          color: '#4A5568', borderRadius: 6, padding: '6px 14px',
          cursor: 'pointer', fontFamily: 'monospace', fontSize: 12
        }}>← LOBBY</button>
      </div>

      {/* Main area */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Video Grid */}
        <div style={s.grid}>
          {/* Local video */}
          <VideoTile
            stream={localStream}
            name={`${user.full_name} (You)`}
            muted={true}
            cameraOff={cameraOff}
            isSelf={true}
          />
          {/* Remote videos */}
          {Object.entries(streams).map(([uid, stream]) => (
            <VideoTile
              key={uid}
              stream={stream}
              name={peerNames[uid] || `User ${uid}`}
              muted={false}
              cameraOff={false}
              isSelf={false}
            />
          ))}
        </div>

        {/* Sidebar */}
        <div style={s.sidebar}>
          {chatOpen && (
            <ChatPanel
              messages={messages}
              onSend={sendChat}
              onClose={() => setChatOpen(false)}
              userName={user.full_name}
            />
          )}
          {minutesOpen && minutes && (
            <MinutesPanel
              minutes={minutes}
              onClose={() => setMinutesOpen(false)}
              onDownload={downloadMinutes}
              onGoHome={() => navigate('/')}
            />
          )}
        </div>
      </div>

      {/* Controls */}
      <Controls
        muted={muted}
        cameraOff={cameraOff}
        chatOpen={chatOpen}
        onToggleMute={toggleMute}
        onToggleCamera={toggleCamera}
        onToggleChat={() => { setChatOpen(!chatOpen); setMinutesOpen(false) }}
        onEndMeeting={endMeeting}
        generating={generating}
        hasMinutes={!!minutes}
        onViewMinutes={() => { setMinutesOpen(!minutesOpen); setChatOpen(false) }}
      />
    </div>
  )
}




