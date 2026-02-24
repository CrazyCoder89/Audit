# Admin panel — user management, system overview. Admin only.

import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import require_login, render_sidebar, api_get, page_header, get_user_role, metric_card

st.set_page_config(page_title="Admin — AuditSys", page_icon="⚡", layout="wide")

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
</style>
""", unsafe_allow_html=True)

require_login()
render_sidebar()

role = get_user_role()
if role != "admin":
    st.error("✗ Access denied — Admin role required")
    st.stop()

page_header("◈ ADMIN PANEL", "System administration and user management")

# ── System Stats ──────────────────────────────────────────────────────────
documents = api_get("/documents/") or []
tasks = api_get("/tasks/") or []
logs = api_get("/audit/", params={"limit": 500}) or []

col1, col2, col3, col4 = st.columns(4)
with col1:
    metric_card("TOTAL DOCUMENTS", len(documents), color="#00D4FF")
with col2:
    metric_card("TOTAL TASKS", len(tasks), color="#F6AD55")
with col3:
    metric_card("AUDIT EVENTS", len(logs), color="#48BB78")
with col4:
    failed = len([d for d in documents if d.get("status") == "failed"])
    metric_card("FAILED DOCS", failed, color="#FF4D6D")

st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

# ── Action Breakdown ──────────────────────────────────────────────────────
st.markdown("""
<div style='background: #0F1628; border: 1px solid #1E2D4D; border-radius: 10px;
            padding: 24px; border-top: 3px solid #00D4FF; margin-bottom: 20px;'>
    <div style='font-size: 0.7rem; color: #4A5568; letter-spacing: 3px; margin-bottom: 16px;'>
        SYSTEM ACTIVITY BREAKDOWN
    </div>
""", unsafe_allow_html=True)

action_counts = {}
for log in logs:
    action = log.get("action", "unknown")
    action_counts[action] = action_counts.get(action, 0) + 1

action_colors = {
    "user.login": "#48BB78", "user.login_failed": "#FF4D6D",
    "user.register": "#00D4FF", "document.upload": "#00D4FF",
    "document.view": "#718096", "document.ask": "#F6AD55",
    "document.delete": "#FF4D6D", "task.create": "#48BB78",
    "task.update": "#F6AD55", "task.delete": "#FF4D6D",
}

total_logs = len(logs)
for action, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True):
    pct = int((count / total_logs) * 100) if total_logs > 0 else 0
    color = action_colors.get(action, "#718096")
    st.markdown(f"""
    <div style='margin-bottom: 10px;'>
        <div style='display: flex; justify-content: space-between; margin-bottom: 4px;'>
            <span style='color: {color}; font-size: 0.8rem; font-weight: 700;'>{action}</span>
            <span style='color: #E2E8F0; font-size: 0.8rem;'>{count} ({pct}%)</span>
        </div>
        <div style='background: #1E2D4D; border-radius: 2px; height: 4px;'>
            <div style='background: {color}; width: {pct}%; height: 4px; border-radius: 2px;'></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ── Recent Documents Table ────────────────────────────────────────────────
st.markdown("""
<div style='background: #0F1628; border: 1px solid #1E2D4D; border-radius: 10px;
            padding: 24px; border-top: 3px solid #F6AD55;'>
    <div style='font-size: 0.7rem; color: #4A5568; letter-spacing: 3px; margin-bottom: 16px;'>
        RECENT DOCUMENTS
    </div>
""", unsafe_allow_html=True)

for doc in documents[-5:]:
    status = doc.get("status", "unknown")
    status_colors = {"processed": "#48BB78", "pending": "#F6AD55", "failed": "#FF4D6D"}
    s_color = status_colors.get(status, "#718096")
    st.markdown(f"""
    <div style='display: flex; justify-content: space-between; padding: 10px 0;
                border-bottom: 1px solid #0A0E1A; font-size: 0.8rem;'>
        <span style='color: #E2E8F0;'>📄 {doc.get('filename', 'unknown')[:50]}</span>
        <span style='color: {s_color}; font-weight: 700;'>{status.upper()}</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)