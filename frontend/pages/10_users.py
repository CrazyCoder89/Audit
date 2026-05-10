# Admin user management — create, edit, deactivate, view all users

import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import (require_login, render_sidebar, api_get, api_post,
                   api_patch, api_delete, page_header, get_user_role)
import requests

st.set_page_config(page_title="Users — AuditSys", page_icon="⚡", layout="wide")

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
    background-size: 50px 50px; pointer-events: none;
}
section[data-testid="stSidebar"] {
    background: #0A0E1A !important;
    border-right: 1px solid #1E2D4D;
}
.stTextInput > div > div > input, .stSelectbox > div > div {
    background: #0F1628 !important;
    border: 1px solid #1E2D4D !important;
    border-radius: 6px !important;
    color: #E2E8F0 !important;
}
.stButton > button {
    background: linear-gradient(135deg, #00D4FF, #0088AA) !important;
    color: #0A0E1A !important; border: none !important;
    border-radius: 6px !important; font-weight: 700 !important;
    letter-spacing: 2px !important;
}
</style>
""", unsafe_allow_html=True)

require_login()
render_sidebar()

role = get_user_role()
if role != "admin":
    st.error("✗ Access denied — Admin role required")
    st.stop()

page_header("◈ USER MANAGEMENT", "Create, manage, and organize your team")

# ── Department list ───────────────────────────────────────────────────────
DEPARTMENTS = [
    "", "Finance & Accounting", "Legal & Compliance", "Human Resources",
    "Information Technology", "Operations", "Risk Management",
    "Internal Audit", "Executive Management", "Other"
]

# ── Create User Panel ─────────────────────────────────────────────────────
with st.expander("✚  CREATE NEW USER", expanded=False):
    col1, col2, col3 = st.columns(3)
    with col1:
        c_name = st.text_input("FULL NAME", placeholder="John Smith", key="c_name")
        c_email = st.text_input("EMAIL", placeholder="john@company.com", key="c_email")
    with col2:
        c_password = st.text_input("PASSWORD", type="password",
                                    placeholder="Min 6 characters", key="c_pass")
        c_role = st.selectbox("ROLE", ["viewer", "auditor", "admin"], key="c_role")
    with col3:
        c_designation = st.text_input("DESIGNATION",
                                       placeholder="Senior Auditor", key="c_desig")
        c_department = st.selectbox("DEPARTMENT", DEPARTMENTS, key="c_dept")

    if st.button("CREATE USER →", use_container_width=True):
        if c_name and c_email and c_password:
            token = st.session_state.get("token", "")
            r = requests.post(
                "http://localhost:8000/auth/users",
                headers={"Authorization": f"Bearer {token}",
                         "Content-Type": "application/json"},
                json={
                    "full_name": c_name,
                    "email": c_email,
                    "password": c_password,
                    "role": c_role,
                    "designation": c_designation,
                    "department": c_department or None
                }
            )
            if r.ok:
                st.success(f"✓ User {c_name} created successfully")
                st.rerun()
            else:
                detail = r.json().get("detail", "Failed")
                if isinstance(detail, list):
                    st.error(f"✗ {detail[0]['msg']}")
                else:
                    st.error(f"✗ {detail}")
        else:
            st.warning("Fill in name, email and password")

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

# ── Filters ───────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    filter_role = st.selectbox("FILTER ROLE",
                                ["all", "admin", "auditor", "viewer", "guest"])
with col2:
    filter_status = st.selectbox("FILTER STATUS", ["all", "active", "inactive"])
with col3:
    filter_dept = st.selectbox("FILTER DEPARTMENT", ["all"] + DEPARTMENTS[1:])

# ── Fetch users ───────────────────────────────────────────────────────────
users = api_get("/auth/users") or []

# Apply filters
if filter_role != "all":
    users = [u for u in users if u.get("role") == filter_role]
if filter_status == "active":
    users = [u for u in users if u.get("is_active") == True]
elif filter_status == "inactive":
    users = [u for u in users if u.get("is_active") == False]
if filter_dept != "all":
    users = [u for u in users if u.get("department") == filter_dept]

st.markdown(f"""
<div style='font-size: 0.7rem; color: #4A5568; letter-spacing: 3px;
            margin-bottom: 12px;'>
    {len(users)} USERS FOUND
</div>
""", unsafe_allow_html=True)

# ── Department stats ──────────────────────────────────────────────────────
all_users = api_get("/auth/users") or []
dept_counts = {}
for u in all_users:
    dept = u.get("department") or "Unassigned"
    dept_counts[dept] = dept_counts.get(dept, 0) + 1

if dept_counts:
    st.markdown("""
    <div style='background: #0F1628; border: 1px solid #1E2D4D;
                border-radius: 10px; padding: 16px; margin-bottom: 20px;
                border-top: 3px solid #9F7AEA;'>
        <div style='font-size: 0.65rem; color: #4A5568; letter-spacing: 3px;
                    margin-bottom: 12px;'>DEPARTMENT OVERVIEW</div>
        <div style='display: flex; flex-wrap: wrap; gap: 8px;'>
    """, unsafe_allow_html=True)

    dept_html = ""
    for dept, count in sorted(dept_counts.items(),
                               key=lambda x: x[1], reverse=True):
        dept_html += f"""
        <span style='background: #1E2D4D; color: #E2E8F0; padding: 4px 12px;
                     border-radius: 20px; font-size: 0.75rem;'>
            {dept} <span style='color: #9F7AEA; font-weight: 700;'>({count})</span>
        </span>"""

    st.markdown(dept_html + "</div></div>", unsafe_allow_html=True)

# ── User cards ────────────────────────────────────────────────────────────
role_colors = {
    "admin": "#FF4D6D", "auditor": "#00D4FF",
    "viewer": "#48BB78", "guest": "#718096"
}

current_user_id = st.session_state.get("user", {}).get("id")

for user in users:
    uid = user.get("id")
    name = user.get("full_name", "Unknown")
    email = user.get("email", "")
    urole = user.get("role", "viewer")
    designation = user.get("designation", "") or ""
    department = user.get("department", "") or "Unassigned"
    is_active = user.get("is_active", True)
    r_color = role_colors.get(urole, "#718096")

    status_color = "#48BB78" if is_active else "#FF4D6D"
    status_label = "ACTIVE" if is_active else "INACTIVE"

    st.markdown(f"""
    <div style='background: #0F1628; border: 1px solid #1E2D4D;
                border-radius: 10px; padding: 18px; margin-bottom: 8px;
                border-left: 4px solid {r_color};
                opacity: {"1" if is_active else "0.6"};'>
        <div style='display: flex; justify-content: space-between;
                    align-items: flex-start;'>
            <div style='display: flex; align-items: center; gap: 14px;'>
                <div style='width: 44px; height: 44px; border-radius: 50%;
                            background: {r_color}22; border: 2px solid {r_color};
                            display: flex; align-items: center;
                            justify-content: center; font-size: 1.1rem;
                            font-weight: 700; color: {r_color};
                            flex-shrink: 0;'>
                    {name[0].upper()}
                </div>
                <div>
                    <div style='color: #E2E8F0; font-size: 0.9rem;
                                font-weight: 600;'>
                        {name} {"<span style='color:#F6AD55; font-size:0.65rem; margin-left:6px;'>YOU</span>" if uid == current_user_id else ""}
                    </div>
                    <div style='color: #4A5568; font-size: 0.75rem;'>{email}</div>
                    <div style='color: #4A5568; font-size: 0.7rem; margin-top: 2px;'>
                        {designation}{" · " + department if designation else department}
                    </div>
                </div>
            </div>
            <div style='text-align: right;'>
                <span style='background: {r_color}22; color: {r_color};
                             font-size: 0.65rem; padding: 3px 10px;
                             border-radius: 4px; font-weight: 700;
                             letter-spacing: 2px; border: 1px solid {r_color}44;'>
                    {urole.upper()}
                </span>
                <div style='color: {status_color}; font-size: 0.65rem;
                            font-weight: 700; margin-top: 4px;
                            letter-spacing: 2px;'>● {status_label}</div>
                <div style='color: #4A5568; font-size: 0.65rem;
                            margin-top: 2px;'>ID #{uid}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Action buttons
    if uid != current_user_id:
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

        with col1:
            new_role = st.selectbox(
                "Role",
                ["viewer", "auditor", "admin"],
                index=["viewer", "auditor", "admin"].index(urole)
                      if urole in ["viewer", "auditor", "admin"] else 0,
                key=f"role_{uid}",
                label_visibility="collapsed"
            )
        with col2:
            new_dept = st.selectbox(
                "Department",
                DEPARTMENTS,
                index=DEPARTMENTS.index(department)
                      if department in DEPARTMENTS else 0,
                key=f"dept_{uid}",
                label_visibility="collapsed"
            )
        with col3:
            if st.button(
                "✓ UPDATE" if is_active else "✓ UPDATE",
                key=f"update_{uid}",
                use_container_width=True
            ):
                token = st.session_state.get("token", "")
                r = requests.patch(
                    f"http://localhost:8000/auth/users/{uid}",
                    headers={"Authorization": f"Bearer {token}",
                             "Content-Type": "application/json"},
                    json={"role": new_role,
                          "department": new_dept or None}
                )
                if r.ok:
                    st.success(f"✓ Updated")
                    st.rerun()
                else:
                    st.error(f"✗ {r.json().get('detail', 'Failed')}")

        with col4:
            # Toggle active/inactive
            btn_label = "⏸ DEACTIVATE" if is_active else "▶ ACTIVATE"
            btn_color = "FF4D6D" if is_active else "48BB78"
            if st.button(btn_label, key=f"toggle_{uid}",
                         use_container_width=True):
                token = st.session_state.get("token", "")
                r = requests.patch(
                    f"http://localhost:8000/auth/users/{uid}",
                    headers={"Authorization": f"Bearer {token}",
                             "Content-Type": "application/json"},
                    json={"is_active": not is_active}
                )
                if r.ok:
                    action = "Deactivated" if is_active else "Activated"
                    st.success(f"✓ {action}")
                    st.rerun()
                else:
                    st.error(f"✗ {r.json().get('detail', 'Failed')}")

    st.markdown("<div style='height: 0.3rem;'></div>", unsafe_allow_html=True)



    