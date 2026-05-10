# User profile page — view and edit own profile, change password

import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import require_login, render_sidebar, api_get, api_patch, page_header
import requests

st.set_page_config(page_title="Profile — AuditSys", page_icon="⚡", layout="wide")

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
.stTextInput > div > div > input {
    background: #0F1628 !important;
    border: 1px solid #1E2D4D !important;
    border-radius: 6px !important;
    color: #E2E8F0 !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.stTextInput > div > div > input:focus {
    border-color: #00D4FF !important;
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
page_header("◈ MY PROFILE", "Manage your account and personal details")

user = st.session_state.get("user", {})
role = user.get("role", "viewer").upper()

role_colors = {
    "ADMIN": "#FF4D6D", "AUDITOR": "#00D4FF",
    "VIEWER": "#48BB78", "GUEST": "#718096"
}
color = role_colors.get(role, "#718096")

# ── Profile Header Card ───────────────────────────────────────────────────
st.markdown(f"""
<div style='background: #0F1628; border: 1px solid #1E2D4D; border-radius: 12px;
            padding: 28px; margin-bottom: 24px; border-top: 3px solid {color};
            display: flex; align-items: center; gap: 24px;'>
    <div style='width: 70px; height: 70px; border-radius: 50%;
                background: {color}22; border: 2px solid {color};
                display: flex; align-items: center; justify-content: center;
                font-size: 1.8rem; font-weight: 700; color: {color};'>
        {user.get("full_name", "U")[0].upper()}
    </div>
    <div>
        <div style='font-size: 1.3rem; font-weight: 700;
                    color: #E2E8F0;'>{user.get("full_name", "")}</div>
        <div style='color: #4A5568; font-size: 0.85rem;
                    margin-top: 2px;'>{user.get("email", "")}</div>
        <div style='display: flex; gap: 10px; margin-top: 8px;
                    align-items: center;'>
            <span style='background: {color}22; color: {color};
                         font-size: 0.65rem; padding: 3px 10px;
                         border-radius: 4px; font-weight: 700;
                         letter-spacing: 2px; border: 1px solid {color}44;'>
                {role}
            </span>
            {f'<span style="color:#4A5568; font-size:0.8rem;">{user.get("designation", "")}</span>'
              if user.get("designation") else ''}
            {f'<span style="color:#4A5568; font-size:0.8rem;">· {user.get("department", "")}</span>'
              if user.get("department") else ''}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["◈  EDIT PROFILE", "◈  CHANGE PASSWORD"])

# ── Tab 1: Edit Profile ───────────────────────────────────────────────────
with tab1:
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        new_name = st.text_input("FULL NAME",
                                  value=user.get("full_name", ""),
                                  key="prof_name")
        new_designation = st.text_input("DESIGNATION",
                                         value=user.get("designation", "") or "",
                                         placeholder="e.g. Senior Auditor",
                                         key="prof_desig")
    with col2:
        new_department = st.text_input("DEPARTMENT",
                                        value=user.get("department", "") or "",
                                        placeholder="e.g. Finance & Compliance",
                                        key="prof_dept")
        st.text_input("EMAIL", value=user.get("email", ""),
                      disabled=True, key="prof_email")

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    if st.button("SAVE CHANGES →", use_container_width=False):
        result, code = api_patch("/auth/me", {
            "full_name": new_name,
            "designation": new_designation,
            "department": new_department
        })
        if code == 200:
            # Update session state
            st.session_state.user["full_name"] = result.get("full_name")
            st.session_state.user["designation"] = result.get("designation")
            st.session_state.user["department"] = result.get("department")
            st.success("✓ Profile updated successfully")
            st.rerun()
        else:
            st.error(f"✗ {result.get('detail', 'Update failed')}")

# ── Tab 2: Change Password ────────────────────────────────────────────────
with tab2:
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        current_pass = st.text_input("CURRENT PASSWORD",
                                      type="password",
                                      key="curr_pass")
        new_pass = st.text_input("NEW PASSWORD",
                                  type="password",
                                  placeholder="Min 6 characters",
                                  key="new_pass")
        confirm_pass = st.text_input("CONFIRM NEW PASSWORD",
                                      type="password",
                                      key="confirm_pass")

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    if st.button("CHANGE PASSWORD →", use_container_width=False):
        if not current_pass or not new_pass or not confirm_pass:
            st.warning("Fill in all password fields")
        elif new_pass != confirm_pass:
            st.error("✗ New passwords do not match")
        elif len(new_pass) < 6:
            st.error("✗ New password must be at least 6 characters")
        else:
            token = st.session_state.get("token", "")
            r = requests.post(
                "http://localhost:8000/auth/me/change-password",
                headers={"Authorization": f"Bearer {token}",
                         "Content-Type": "application/json"},
                json={"current_password": current_pass,
                      "new_password": new_pass}
            )
            if r.ok:
                st.success("✓ Password changed successfully")
            else:
                st.error(f"✗ {r.json().get('detail', 'Failed')}")

                