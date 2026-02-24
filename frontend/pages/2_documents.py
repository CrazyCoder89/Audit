# Document management page.
# Upload PDFs, view all documents, check processing status.

import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import require_login, render_sidebar, api_get, api_delete, page_header, status_badge, get_user_role
import requests

st.set_page_config(page_title="Documents — AuditSys", page_icon="⚡", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&display=swap');
* { font-family: 'JetBrains Mono', monospace; }
.stApp { background: #0A0E1A; }
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image: 
        linear-gradient(rgba(0, 212, 255, 0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 212, 255, 0.02) 1px, transparent 1px);
    background-size: 50px 50px;
    pointer-events: none;
}
section[data-testid="stSidebar"] { background: #0A0E1A !important; border-right: 1px solid #1E2D4D; }
.stFileUploader { background: #0F1628 !important; border: 1px dashed #1E2D4D !important; border-radius: 10px !important; }
.stButton > button {
    background: linear-gradient(135deg, #00D4FF, #0088AA) !important;
    color: #0A0E1A !important; border: none !important;
    border-radius: 6px !important; font-weight: 700 !important;
    font-family: 'JetBrains Mono', monospace !important;
    letter-spacing: 2px !important;
}
.stButton > button:hover { transform: translateY(-1px) !important; box-shadow: 0 6px 20px rgba(0,212,255,0.25) !important; }
</style>
""", unsafe_allow_html=True)

require_login()
render_sidebar()
page_header("◈ DOCUMENTS", "Upload, manage, and analyze compliance documents")

role = get_user_role()

# ── Upload Section ────────────────────────────────────────────────────────
st.markdown("""
<div style='background: #0F1628; border: 1px solid #1E2D4D; border-radius: 10px; 
            padding: 24px; border-top: 3px solid #00D4FF; margin-bottom: 24px;'>
    <div style='font-size: 0.7rem; color: #4A5568; letter-spacing: 3px; margin-bottom: 16px;'>
        UPLOAD DOCUMENT
    </div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Drop PDF here or click to browse",
    type=["pdf"],
    label_visibility="collapsed"
)

if uploaded_file:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
        <div style='background: #0A0E1A; border: 1px solid #1E2D4D; border-radius: 6px; 
                    padding: 12px; display: flex; align-items: center;'>
            <span style='color: #00D4FF; margin-right: 12px;'>📄</span>
            <div>
                <div style='color: #E2E8F0; font-size: 0.85rem;'>{uploaded_file.name}</div>
                <div style='color: #4A5568; font-size: 0.7rem;'>
                    {round(uploaded_file.size / 1024, 1)} KB
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("UPLOAD →", use_container_width=True):
            with st.spinner("Uploading and processing..."):
                token = st.session_state.get("token")
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                r = requests.post(
                    "http://localhost:8000/documents/upload",
                    headers={"Authorization": f"Bearer {token}"},
                    files=files
                )
                if r.ok:
                    st.success("✓ Document uploaded — processing in background")
                    st.rerun()
                else:
                    st.error(f"✗ {r.json().get('detail', 'Upload failed')}")

st.markdown("</div>", unsafe_allow_html=True)

# ── Document List ─────────────────────────────────────────────────────────
documents = api_get("/documents/") or []

st.markdown(f"""
<div style='font-size: 0.7rem; color: #4A5568; letter-spacing: 3px; 
            margin-bottom: 12px;'>
    ALL DOCUMENTS — {len(documents)} TOTAL
</div>
""", unsafe_allow_html=True)

if not documents:
    st.markdown("""
    <div style='background: #0F1628; border: 1px solid #1E2D4D; border-radius: 10px; 
                padding: 40px; text-align: center;'>
        <div style='font-size: 2rem; margin-bottom: 8px;'>◈</div>
        <div style='color: #4A5568; letter-spacing: 2px;'>NO DOCUMENTS YET</div>
        <div style='color: #2D3748; font-size: 0.75rem; margin-top: 4px;'>
            Upload your first PDF above
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    # Header row
    st.markdown("""
    <div style='display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr; 
                padding: 8px 16px; border-bottom: 1px solid #1E2D4D;
                font-size: 0.65rem; color: #4A5568; letter-spacing: 2px;'>
        <span>FILENAME</span>
        <span>CATEGORY</span>
        <span>STATUS</span>
        <span>SIZE</span>
        <span>UPLOADED</span>
    </div>
    """, unsafe_allow_html=True)

    for doc in documents:
        size_kb = round(doc.get("file_size", 0) / 1024, 1)
        date = doc.get("created_at", "")[:10]
        category = doc.get("category", "unknown").upper()
        status = doc.get("status", "unknown")
        filename = doc.get("filename", "unknown")
        doc_id = doc.get("id")

        cat_colors = {
            "FINANCIAL": "#48BB78", "LEGAL": "#F6AD55",
            "COMPLIANCE": "#00D4FF", "HR": "#9F7AEA", "UNKNOWN": "#718096"
        }
        cat_color = cat_colors.get(category, "#718096")

        st.markdown(f"""
        <div style='display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr;
                    padding: 14px 16px; background: #0F1628; border-radius: 8px;
                    margin-bottom: 6px; border: 1px solid #1E2D4D;
                    border-left: 3px solid {cat_color};
                    transition: all 0.2s;'>
            <span style='color: #E2E8F0; font-size: 0.8rem; 
                         overflow: hidden; text-overflow: ellipsis;
                         white-space: nowrap;'>📄 {filename}</span>
            <span style='color: {cat_color}; font-size: 0.75rem; font-weight: 700;'>
                {category}
            </span>
            <span>{status_badge(status)}</span>
            <span style='color: #4A5568; font-size: 0.75rem;'>{size_kb} KB</span>
            <span style='color: #4A5568; font-size: 0.75rem;'>{date}</span>
        </div>
        """, unsafe_allow_html=True)

        # Admin delete button
        if role == "admin":
            if st.button(f"✕ Delete", key=f"del_{doc_id}"):
                result, status_code = api_delete(f"/documents/{doc_id}")
                if status_code == 200:
                    st.success("Deleted")
                    st.rerun()