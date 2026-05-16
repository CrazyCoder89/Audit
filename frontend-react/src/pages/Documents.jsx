import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext.jsx'
import Layout from '../components/Layout.jsx'
import PageHeader from '../components/PageHeader.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import axios from 'axios'
const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const CAT_COLORS = {
  financial: '#48BB78', legal: '#F6AD55',
  compliance: '#00D4FF', hr: '#9F7AEA', unknown: '#718096'
}

export default function Documents() {
  const { apiGet, apiDelete, authHeaders, user } = useAuth()
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [msg, setMsg] = useState('')
  const fileRef = useRef()

  const fetch = async () => {
    const docs = await apiGet('/documents/')
    setDocuments(docs || [])
    setLoading(false)
  }

  useEffect(() => { fetch() }, [])

  const upload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    if (!file.name.endsWith('.pdf')) { setMsg('Only PDF files allowed'); return }
    if (file.size > 10 * 1024 * 1024) { setMsg('File must be under 10MB'); return }
    setUploading(true)
    setMsg('')
    const form = new FormData()
    form.append('file', file)
    try {
      await axios.post(`${BASE}/documents/upload`, form,
        { headers: { ...authHeaders(), 'Content-Type': 'multipart/form-data' } })
      setMsg('✓ Uploaded — processing in background')
      fetch()
    } catch (err) {
      setMsg('✗ ' + (err.response?.data?.detail || 'Upload failed'))
    }
    setUploading(false)
    fileRef.current.value = ''
  }

  const download = async (doc) => {
    try {
      const res = await axios.get(
        `${BASE}/documents/${doc.id}/download`,
        { headers: authHeaders(), responseType: 'blob' }
      )
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url
      a.download = doc.filename
      a.click()
    } catch { setMsg('✗ Download failed') }
  }

  const deleteDoc = async (id) => {
    if (!window.confirm('Delete this document?')) return
    await apiDelete(`/documents/${id}`)
    fetch()
  }

  const s = {
    card: { background: '#0F1628', border: '1px solid #1E2D4D', borderRadius: 10, padding: 20, marginBottom: 20 },
    uploadBox: {
      border: '2px dashed #1E2D4D', borderRadius: 10, padding: 32,
      textAlign: 'center', cursor: 'pointer', marginBottom: 16,
      transition: 'border-color 0.2s'
    },
    btn: (color = '#00D4FF') => ({
      background: `linear-gradient(135deg,${color},${color}88)`,
      color: color === '#00D4FF' ? '#0A0E1A' : 'white',
      border: 'none', borderRadius: 6, padding: '6px 14px',
      cursor: 'pointer', fontFamily: 'monospace', fontSize: 11,
      fontWeight: 700, letterSpacing: 1
    }),
    row: {
      display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr 120px',
      padding: '12px 16px', background: '#0A0E1A', borderRadius: 8,
      marginBottom: 6, border: '1px solid #1E2D4D', alignItems: 'center'
    },
    headerRow: {
      display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr 120px',
      padding: '8px 16px', fontSize: '0.65rem', color: '#4A5568',
      letterSpacing: 2, marginBottom: 8
    }
  }

  return (
    <Layout>
      <PageHeader title="◈ DOCUMENTS" subtitle="Upload, manage, and analyze compliance documents" />

      {/* Upload */}
      <div style={{ ...s.card, borderTop: '3px solid #00D4FF' }}>
        <div style={{ fontSize: '0.65rem', color: '#4A5568', letterSpacing: 3, marginBottom: 12 }}>
          UPLOAD DOCUMENT
        </div>
        <div style={s.uploadBox} onClick={() => fileRef.current.click()}>
          <div style={{ fontSize: '2rem', marginBottom: 8 }}>📄</div>
          <div style={{ color: '#E2E8F0', fontSize: 14 }}>Drop PDF here or click to browse</div>
          <div style={{ color: '#4A5568', fontSize: 12, marginTop: 4 }}>PDF only · Max 10MB</div>
        </div>
        <input ref={fileRef} type="file" accept=".pdf"
          style={{ display: 'none' }} onChange={upload} />
        {uploading && <div style={{ color: '#F6AD55', fontSize: 13 }}>⚡ Uploading...</div>}
        {msg && <div style={{ color: msg.startsWith('✓') ? '#48BB78' : '#FF4D6D', fontSize: 13 }}>{msg}</div>}
      </div>

      {/* List */}
      <div style={{ ...s.card }}>
        <div style={{ fontSize: '0.65rem', color: '#4A5568', letterSpacing: 3, marginBottom: 12 }}>
          ALL DOCUMENTS — {documents.length} TOTAL
        </div>

        {documents.length === 0 ? (
          <div style={{ textAlign: 'center', color: '#4A5568', padding: '40px 0' }}>
            <div style={{ fontSize: '2rem', marginBottom: 8 }}>◈</div>
            No documents yet
          </div>
        ) : (
          <>
            <div style={s.headerRow}>
              <span>FILENAME</span><span>CATEGORY</span>
              <span>STATUS</span><span>SIZE</span>
              <span>DATE</span><span>ACTIONS</span>
            </div>
            {documents.map(doc => {
              const catColor = CAT_COLORS[doc.category] || '#718096'
              const sizeKb = Math.round(doc.file_size / 1024)
              const isShared = doc.uploaded_by !== user?.id
              return (
                <div key={doc.id} style={{ ...s.row, borderLeft: `3px solid ${catColor}` }}>
                  <div style={{ overflow: 'hidden' }}>
                    <div style={{ color: '#E2E8F0', fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      📄 {doc.filename}
                    </div>
                    {isShared && (
                      <span style={{ background: '#9F7AEA22', color: '#9F7AEA', fontSize: '0.6rem', padding: '1px 6px', borderRadius: 3, border: '1px solid #9F7AEA44' }}>
                        SHARED
                      </span>
                    )}
                  </div>
                  <span style={{ color: catColor, fontSize: 11, fontWeight: 700 }}>{doc.category?.toUpperCase()}</span>
                  <StatusBadge status={doc.status} />
                  <span style={{ color: '#4A5568', fontSize: 12 }}>{sizeKb} KB</span>
                  <span style={{ color: '#4A5568', fontSize: 12 }}>{doc.created_at?.slice(0, 10)}</span>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button style={s.btn()} onClick={() => download(doc)}>⬇</button>
                    {user?.role === 'admin' && (
                      <button style={s.btn('#FF4D6D')} onClick={() => deleteDoc(doc.id)}>✕</button>
                    )}
                  </div>
                </div>
              )
            })}
          </>
        )}
      </div>
    </Layout>
  )
}

