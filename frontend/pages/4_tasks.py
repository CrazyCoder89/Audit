import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import (require_login, render_sidebar, api_get, api_post,
                   api_patch, api_delete, page_header, status_badge, get_user_role)
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
[data-testid="stDialog"] { background: #0F1628 !important; }
</style>
""", unsafe_allow_html=True)

require_login()
render_sidebar()
page_header("◈ TASKS", "Manage and track audit tasks")

role = get_user_role()

# ── Fetch users for name lookup ───────────────────────────────────────────
users_list = api_get("/auth/users") or []
users_map = {u["id"]: u for u in users_list}

def get_user_display(user_id):
    """Returns name + designation for a user ID."""
    if not user_id:
        return "Unassigned"
    user = users_map.get(user_id)
    if not user:
        return f"User #{user_id}"
    name = user.get("full_name", f"User #{user_id}")
    desig = user.get("designation", "")
    return f"{name}" + (f" · {desig}" if desig else "")

# ── Session state for selected task ──────────────────────────────────────
if "selected_task" not in st.session_state:
    st.session_state.selected_task = None

# ── Create Task ───────────────────────────────────────────────────────────
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
            documents = api_get("/documents/") or []
            doc_options = {"None": None}
            doc_options.update({f"[{d['id']}] {d['filename']}": d['id'] for d in documents})
            selected_doc = st.selectbox("LINK TO DOCUMENT (optional)", list(doc_options.keys()))

            # User assignment by name
            if users_list:
                user_options = {f"{u['full_name']} ({u['email']})": u['id'] for u in users_list}
                selected_user_label = st.selectbox("ASSIGN TO", list(user_options.keys()))
                assigned_to = user_options[selected_user_label]
            else:
                assigned_to = st.number_input("ASSIGN TO USER ID", min_value=1, value=1)

        if st.button("CREATE TASK →", use_container_width=True):
            deadline_dt = datetime.combine(deadline, deadline_time).isoformat()
            result, status_code = api_post("/tasks/", {
                "title": title,
                "description": description,
                "priority": priority,
                "deadline": deadline_dt,
                "assigned_to": assigned_to,
                "document_id": doc_options.get(selected_doc)
            })
            if status_code == 200:
                st.success("✓ Task created — notification sent to assignee")
                st.rerun()
            else:
                st.error(f"✗ {result.get('detail', 'Failed to create task')}")

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

# ── Filters ───────────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 1])
with col1:
    filter_status = st.selectbox("STATUS", ["all", "pending", "in_progress", "completed", "overdue"])
with col2:
    filter_priority = st.selectbox("PRIORITY", ["all", "low", "medium", "high", "critical"])

params = {}
if filter_status != "all":
    params["status"] = filter_status
if filter_priority != "all":
    params["priority"] = filter_priority

tasks = api_get("/tasks/", params=params) or []

st.markdown(f"""
<div style='font-size: 0.7rem; color: #4A5568; letter-spacing: 3px; margin-bottom: 12px;'>
    TASKS — {len(tasks)} FOUND · CLICK ANY TASK TO VIEW DETAILS
</div>
""", unsafe_allow_html=True)

# ── Task Detail Modal ─────────────────────────────────────────────────────
@st.dialog("Task Details", width="large")
def show_task_detail(task):
    task_id = task.get("id")
    status = task.get("status", "pending")
    priority = task.get("priority", "medium")
    deadline = task.get("deadline", "")[:16].replace("T", " ") if task.get("deadline") else "No deadline"
    created_at = task.get("created_at", "")[:16].replace("T", " ")

    priority_colors = {
        "critical": "#FF4D6D", "high": "#F6AD55",
        "medium": "#00D4FF", "low": "#48BB78"
    }
    p_color = priority_colors.get(priority, "#718096")

    # Header
    st.markdown(f"""
    <div style='border-left: 4px solid {p_color}; padding-left: 16px; margin-bottom: 20px;'>
        <div style='font-size: 1.2rem; font-weight: 700; color: #E2E8F0;'>
            {task.get('title', 'Untitled')}
        </div>
        <div style='margin-top: 6px; display: flex; gap: 8px; align-items: center;'>
            {status_badge(status)}
            <span style='color: {p_color}; font-size: 0.7rem; font-weight: 700;
                         letter-spacing: 2px;'>{priority.upper()} PRIORITY</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Details grid
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div style='background: #0A0E1A; border: 1px solid #1E2D4D; border-radius: 8px; padding: 16px;'>
            <div style='font-size: 0.65rem; color: #4A5568; letter-spacing: 2px; margin-bottom: 12px;'>
                TASK INFO
            </div>
            <div style='margin-bottom: 10px;'>
                <div style='font-size: 0.7rem; color: #4A5568;'>TASK ID</div>
                <div style='color: #E2E8F0; font-size: 0.85rem;'>#{task_id}</div>
            </div>
            <div style='margin-bottom: 10px;'>
                <div style='font-size: 0.7rem; color: #4A5568;'>DEADLINE</div>
                <div style='color: #E2E8F0; font-size: 0.85rem;'>⏰ {deadline}</div>
            </div>
            <div style='margin-bottom: 10px;'>
                <div style='font-size: 0.7rem; color: #4A5568;'>CREATED AT</div>
                <div style='color: #E2E8F0; font-size: 0.85rem;'>{created_at}</div>
            </div>
            <div>
                <div style='font-size: 0.7rem; color: #4A5568;'>LINKED DOCUMENT</div>
                <div style='color: #E2E8F0; font-size: 0.85rem;'>
                    {"Doc #" + str(task.get("document_id")) if task.get("document_id") else "None"}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style='background: #0A0E1A; border: 1px solid #1E2D4D; border-radius: 8px; padding: 16px;'>
            <div style='font-size: 0.65rem; color: #4A5568; letter-spacing: 2px; margin-bottom: 12px;'>
                PEOPLE
            </div>
            <div style='margin-bottom: 10px;'>
                <div style='font-size: 0.7rem; color: #4A5568;'>ASSIGNED TO</div>
                <div style='color: #00D4FF; font-size: 0.85rem; font-weight: 600;'>
                    👤 {get_user_display(task.get("assigned_to"))}
                </div>
            </div>
            <div>
                <div style='font-size: 0.7rem; color: #4A5568;'>CREATED BY</div>
                <div style='color: #E2E8F0; font-size: 0.85rem;'>
                    👤 {get_user_display(task.get("created_by"))}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Description
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='background: #0A0E1A; border: 1px solid #1E2D4D; border-radius: 8px; padding: 16px;'>
        <div style='font-size: 0.65rem; color: #4A5568; letter-spacing: 2px; margin-bottom: 8px;'>
            DESCRIPTION
        </div>
        <div style='color: #E2E8F0; font-size: 0.85rem; line-height: 1.7;'>
            {task.get('description') or 'No description provided.'}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Actions
    st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size: 0.65rem; color: #4A5568; letter-spacing: 2px; margin-bottom: 8px;'>
        UPDATE STATUS
    </div>
    """, unsafe_allow_html=True)

    col_s, col_btn, col_del = st.columns([2, 1, 1])
    with col_s:
        new_status = st.selectbox(
            "New Status",
            ["pending", "in_progress", "completed"],
            index=["pending", "in_progress", "completed"].index(status)
                  if status in ["pending", "in_progress", "completed"] else 0,
            label_visibility="collapsed",
            key=f"modal_status_{task_id}"
        )
    with col_btn:
        if st.button("UPDATE →", use_container_width=True, key=f"modal_update_{task_id}"):
            result, code = api_patch(f"/tasks/{task_id}", {"status": new_status})
            if code == 200:
                st.success("✓ Status updated")
                st.rerun()
            else:
                st.error(f"✗ {result.get('detail', 'Failed')}")
    with col_del:
        if role == "admin":
            if st.button("✕ DELETE", use_container_width=True, key=f"modal_del_{task_id}"):
                api_delete(f"/tasks/{task_id}")
                st.rerun()

# ── Comments Section ──────────────────────────────────────────────────
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size: 0.65rem; color: #4A5568; letter-spacing: 2px; margin-bottom: 8px;'>
        ◈ COMMENTS
    </div>
    """, unsafe_allow_html=True)

    # Load comments
    comments = api_get(f"/tasks/{task_id}/comments") or []

    # Display existing comments
    if comments:
        for comment in comments:
            user_info = users_map.get(comment.get("user_id"), {})
            commenter = user_info.get("full_name", f"User #{comment.get('user_id')}")
            desig = user_info.get("designation", "")
            timestamp = comment.get("created_at", "")[:16].replace("T", " ")
            is_mine = comment.get("user_id") == st.session_state.get("user", {}).get("id")

            border_color = "#00D4FF" if is_mine else "#1E2D4D"
            st.markdown(f"""
            <div style='background: #0A0E1A; border: 1px solid {border_color};
                        border-radius: 8px; padding: 12px 16px; margin-bottom: 8px;'>
                <div style='display: flex; justify-content: space-between;
                            margin-bottom: 6px;'>
                    <div>
                        <span style='color: #00D4FF; font-size: 0.8rem;
                                     font-weight: 700;'>{commenter}</span>
                        {f'<span style="color:#4A5568; font-size:0.7rem; margin-left:6px;">{desig}</span>' if desig else ''}
                        {'<span style="color:#48BB78; font-size:0.65rem; margin-left:6px; font-weight:700;">YOU</span>' if is_mine else ''}
                    </div>
                    <span style='color: #4A5568; font-size: 0.7rem;'>{timestamp}</span>
                </div>
                <div style='color: #E2E8F0; font-size: 0.85rem; line-height: 1.6;'>
                    {comment.get("content", "")}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Delete button for own comments or admin
            current_role = get_user_role()
            current_uid = st.session_state.get("user", {}).get("id")
            if is_mine or current_role == "admin":
                if st.button("✕ Delete", key=f"del_comment_{comment['id']}"):
                    api_delete(f"/tasks/{task_id}/comments/{comment['id']}")
                    st.rerun()
    else:
        st.markdown("""
        <div style='color: #4A5568; font-size: 0.8rem; text-align: center;
                    padding: 16px; background: #0A0E1A; border-radius: 8px;
                    border: 1px dashed #1E2D4D;'>
            No comments yet — be the first to add one
        </div>
        """, unsafe_allow_html=True)

    # Add new comment
    st.markdown("<div style='height: 0.3rem;'></div>", unsafe_allow_html=True)
    new_comment = st.text_area(
        "Add comment",
        placeholder="Write a comment...",
        height=80,
        label_visibility="collapsed",
        key=f"new_comment_{task_id}"
    )
    if st.button("ADD COMMENT →", use_container_width=True, key=f"submit_comment_{task_id}"):
        if new_comment.strip():
            result, code = api_post(
                f"/tasks/{task_id}/comments",
                {"content": new_comment.strip()}
            )
            if code == 200:
                st.success("✓ Comment added")
                st.rerun()
            else:
                st.error(f"✗ {result.get('detail', 'Failed')}")
        else:
            st.warning("Comment cannot be empty")

            
# ── Task Cards Grid ───────────────────────────────────────────────────────
if not tasks:
    st.markdown("""
    <div style='background: #0F1628; border: 1px solid #1E2D4D; border-radius: 10px;
                padding: 40px; text-align: center;'>
        <div style='font-size: 2rem; margin-bottom: 8px;'>◈</div>
        <div style='color: #4A5568; letter-spacing: 2px;'>NO TASKS FOUND</div>
    </div>
    """, unsafe_allow_html=True)
else:
    # Render tasks in 2-column grid
    cols = st.columns(2)
    for i, task in enumerate(tasks):
        task_id = task.get("id")
        title = task.get("title", "Untitled")
        description = task.get("description", "")
        status = task.get("status", "pending")
        priority = task.get("priority", "medium")
        deadline = task.get("deadline", "")[:10] if task.get("deadline") else "No deadline"
        assigned_name = get_user_display(task.get("assigned_to"))

        priority_colors = {
            "critical": "#FF4D6D", "high": "#F6AD55",
            "medium": "#00D4FF", "low": "#48BB78"
        }
        p_color = priority_colors.get(priority, "#718096")

        with cols[i % 2]:
            st.markdown(f"""
            <div style='background: #0F1628; border: 1px solid #1E2D4D; border-radius: 10px;
                        padding: 18px; margin-bottom: 10px; border-left: 4px solid {p_color};'>
                <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
                    <div style='color: #E2E8F0; font-size: 0.9rem; font-weight: 600; 
                                max-width: 65%;'>{title}</div>
                    <div>{status_badge(status)}</div>
                </div>
                <div style='color: #4A5568; font-size: 0.75rem; margin-top: 6px; line-height: 1.5;'>
                    {description[:80] + '...' if len(description) > 80 else description or 'No description'}
                </div>
                <div style='display: flex; gap: 12px; margin-top: 10px; flex-wrap: wrap;
                            font-size: 0.7rem; color: #4A5568;'>
                    <span style='color: {p_color}; font-weight: 700;'>▪ {priority.upper()}</span>
                    <span>⏰ {deadline}</span>
                    <span>👤 {assigned_name.split(' · ')[0]}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"VIEW DETAILS", key=f"view_{task_id}", use_container_width=True):
                show_task_detail(task)



