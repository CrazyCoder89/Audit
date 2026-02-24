# Audit logs viewer — compliance trail of all system actions.

import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import require_login, render_sidebar, api_get, page_header, get_user_role, status_badge
import requests

st.set_page_config(page_title="Audit Logs — AuditSys", page_icon="⚡", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&display=swap');
* { font-family: 'JetBrains Mono', monospace; }
.stApp { background: #0A0E1A; }
.stApp::before {
    content: '';
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background-image: 
        linear-gradient(rgba(0, 212, 255, 0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 212, 255, 0.02) 1px, transparent 1px);
    background-size: 50px 50px;
    pointer-events: none;
}
section[data-testid="stSidebar"] { background: #0A0E1A !important; border-right: 1px solid #1E2D4D; }
.stSelectbox > div > div { background: #0F1628 !important; border: 1px solid #1E2D4D !important; }
.stButton > button {
    background: linear-gradient(135deg, #00D4FF, #0088AA) !important;
    color: #0A0E1A !important; border: none !important;
    border-radius: 6px !important; font-weight: 700 !important; letter-spacing: 2px !important;
}
</style>
""", unsafe_allow_html=True)

require_login()
render_sidebar()

role = get_user_role()
if role not in ["admin", "auditor"]:
    st.error("✗ Access denied — Admin or Auditor role required")
    st.stop()

page_header("◈ AUDIT LOGS", "Complete compliance trail of all system actions")

# ── Filters ───────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
with col1:
    filter_action = st.selectbox("ACTION", [
        "all", "user.login", "user.login_failed", "user.register",
        "document.upload", "document.view", "document.ask", "document.delete",
        "task.create", "task.update", "task.delete"
    ])
with col2:
    filter_resource = st.selectbox("RESOURCE TYPE", ["all", "user", "document", "task"])
with col3:
    limit = st.selectbox("SHOW", [25, 50, 100, 200])
with col4:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    if role == "admin":
        if st.button("⬇ EXPORT CSV", use_container_width=True):
            token = st.session_state.get("token")
            r = requests.get(
                "http://localhost:8000/audit/export",
                headers={"Authorization": f"Bearer {token}"}
            )
            if r.ok:
                st.download_button(
                    "Download CSV",
                    data=r.content,
                    file_name="audit_logs.csv",
                    mime="text/csv"
                )

# ── Fetch Logs ────────────────────────────────────────────────────────────
params = {"limit": limit}
if filter_action != "all":
    params["action"] = filter_action
if filter_resource != "all":
    params["resource_type"] = filter_resource

logs = api_get("/audit/", params=params) or []

st.markdown(f"""
<div style='font-size: 0.7rem; color: #4A5568; letter-spacing: 3px; margin: 16px 0 12px 0;'>
    SHOWING {len(logs)} RECORDS
</div>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────
st.markdown("""
<div style='display: grid; grid-template-columns: 0.5fr 1fr 1.5fr 1fr 1fr 1fr;
            padding: 8px 16px; border-bottom: 1px solid #1E2D4D;
            font-size: 0.65rem; color: #4A5568; letter-spacing: 2px;'>
    <span>ID</span><span>USER</span><span>ACTION</span>
    <span>RESOURCE</span><span>IP</span><span>TIMESTAMP</span>
</div>
""", unsafe_allow_html=True)

action_colors = {
    "user.login": "#48BB78", "user.login_failed": "#FF4D6D",
    "user.register": "#00D4FF", "document.upload": "#00D4FF",
    "document.view": "#718096", "document.ask": "#F6AD55",
    "document.delete": "#FF4D6D", "task.create": "#48BB78",
    "task.update": "#F6AD55", "task.delete": "#FF4D6D",
}

if not logs:
    st.markdown("""
    <div style='background: #0F1628; border: 1px solid #1E2D4D; border-radius: 10px;
                padding: 40px; text-align: center; margin-top: 12px;'>
        <div style='color: #4A5568; letter-spacing: 2px;'>NO LOGS FOUND</div>
    </div>
    """, unsafe_allow_html=True)
else:
    for log in logs:
        action = log.get("action", "unknown")
        color = action_colors.get(action, "#718096")
        timestamp = log.get("created_at", "")[:19].replace("T", " ")
        resource = f"{log.get('resource_type', '')} #{log.get('resource_id', '')}" if log.get('resource_type') else "—"

        st.markdown(f"""
        <div style='display: grid; grid-template-columns: 0.5fr 1fr 1.5fr 1fr 1fr 1fr;
                    padding: 12px 16px; background: #0F1628; border-radius: 6px;
                    margin-bottom: 4px; border: 1px solid #1E2D4D;
                    border-left: 3px solid {color}; font-size: 0.75rem;'>
            <span style='color: #4A5568;'>#{log.get('id')}</span>
            <span style='color: #E2E8F0;'>user:{log.get('user_id', 'sys')}</span>
            <span style='color: {color}; font-weight: 700;'>{action}</span>
            <span style='color: #4A5568;'>{resource}</span>
            <span style='color: #4A5568;'>{log.get('ip_address', '—')}</span>
            <span style='color: #4A5568; font-family: monospace;'>{timestamp}</span>
        </div>
        """, unsafe_allow_html=True)