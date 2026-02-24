# Task management board — create, assign, track, and update audit tasks.

import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import require_login, render_sidebar, api_get, api_post, api_patch, api_delete, page_header, status_badge, get_user_role
from datetime import datetime, timedelta

st.set_page_config(page_title="Tasks — AuditSys", page_icon="⚡", layout="wide")

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
.stTextInput > div > div > input, .stTextArea > div > div > textarea {
    background: #0F1628 !important; border: 1px solid #1E2D4D !important;
    border-radius: 6px !important; color: #E2E8F0 !important;
    font-family: 'JetBrains Mono', monospace !important;
}
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
page_header("◈ TASKS", "Manage and track audit tasks")

role = get_user_role()

# ── Create Task (admin/auditor only) ──────────────────────────────────────
if role in ["admin", "auditor"]:
    with st.expander("✚  CREATE NEW TASK", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("TITLE", placeholder="Review Q3 compliance report")
            description = st.text_area("DESCRIPTION", placeholder="Detailed task description...", height=100)
            priority = st.selectbox("PRIORITY", ["low", "medium", "high", "critical"])
        with col2:
            deadline = st.date_input("DEADLINE", value=datetime.now() + timedelta(days=7))
            deadline_time = st.time_input("DEADLINE TIME")

            # Get users for assignment
            documents = api_get("/documents/") or []
            doc_options = {"None": None}
            doc_options.update({f"[{d['id']}] {d['filename']}": d['id'] for d in documents})
            selected_doc = st.selectbox("LINK TO DOCUMENT (optional)", list(doc_options.keys()))

            assigned_to = st.number_input("ASSIGN TO USER ID", min_value=1, value=1)

        if st.button("CREATE TASK →", use_container_width=True):
            deadline_dt = datetime.combine(deadline, deadline_time).isoformat()
            result, status = api_post("/tasks/", {
                "title": title,
                "description": description,
                "priority": priority,
                "deadline": deadline_dt,
                "assigned_to": assigned_to,
                "document_id": doc_options.get(selected_doc)
            })
            if status == 200:
                st.success("✓ Task created successfully")
                st.rerun()
            else:
                st.error(f"✗ {result.get('detail', 'Failed to create task')}")

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

# ── Filter Bar ────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    filter_status = st.selectbox("FILTER STATUS", ["all", "pending", "in_progress", "completed", "overdue"])
with col2:
    filter_priority = st.selectbox("FILTER PRIORITY", ["all", "low", "medium", "high", "critical"])

# ── Fetch Tasks ───────────────────────────────────────────────────────────
params = {}
if filter_status != "all":
    params["status"] = filter_status
if filter_priority != "all":
    params["priority"] = filter_priority

tasks = api_get("/tasks/", params=params) or []

# ── Task Board ────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='font-size: 0.7rem; color: #4A5568; letter-spacing: 3px; margin-bottom: 12px;'>
    TASKS — {len(tasks)} FOUND
</div>
""", unsafe_allow_html=True)

if not tasks:
    st.markdown("""
    <div style='background: #0F1628; border: 1px solid #1E2D4D; border-radius: 10px;
                padding: 40px; text-align: center;'>
        <div style='font-size: 2rem; margin-bottom: 8px;'>◈</div>
        <div style='color: #4A5568; letter-spacing: 2px;'>NO TASKS FOUND</div>
    </div>
    """, unsafe_allow_html=True)
else:
    for task in tasks:
        task_id = task.get("id")
        title = task.get("title", "Untitled")
        description = task.get("description", "")
        status = task.get("status", "pending")
        priority = task.get("priority", "medium")
        deadline = task.get("deadline", "")[:10] if task.get("deadline") else "No deadline"
        assigned_to = task.get("assigned_to", "Unassigned")

        priority_colors = {
            "critical": "#FF4D6D", "high": "#F6AD55",
            "medium": "#00D4FF", "low": "#48BB78"
        }
        p_color = priority_colors.get(priority, "#718096")

        st.markdown(f"""
        <div style='background: #0F1628; border: 1px solid #1E2D4D; border-radius: 10px;
                    padding: 20px; margin-bottom: 10px; border-left: 4px solid {p_color};'>
            <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
                <div>
                    <div style='color: #E2E8F0; font-size: 0.95rem; font-weight: 600;'>
                        {title}
                    </div>
                    <div style='color: #4A5568; font-size: 0.75rem; margin-top: 4px;'>
                        {description[:100] + '...' if len(description) > 100 else description}
                    </div>
                </div>
                <div style='text-align: right;'>
                    {status_badge(status)}
                    <div style='color: {p_color}; font-size: 0.65rem; letter-spacing: 2px; 
                                margin-top: 4px; font-weight: 700;'>{priority.upper()}</div>
                </div>
            </div>
            <div style='display: flex; gap: 20px; margin-top: 12px; 
                        font-size: 0.7rem; color: #4A5568;'>
                <span>⏰ {deadline}</span>
                <span>👤 User #{assigned_to}</span>
                <span>🔑 ID #{task_id}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Update status
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            new_status = st.selectbox(
                "Update status",
                ["pending", "in_progress", "completed"],
                index=["pending", "in_progress", "completed"].index(status) if status in ["pending", "in_progress", "completed"] else 0,
                key=f"status_{task_id}",
                label_visibility="collapsed"
            )
        with col2:
            if st.button("UPDATE STATUS", key=f"update_{task_id}"):
                result, code = api_patch(f"/tasks/{task_id}", {"status": new_status})
                if code == 200:
                    st.success("✓ Updated")
                    st.rerun()
                else:
                    st.error(f"✗ {result.get('detail', 'Failed')}")
        with col3:
            if role == "admin":
                if st.button("✕", key=f"del_{task_id}"):
                    api_delete(f"/tasks/{task_id}")
                    st.rerun()