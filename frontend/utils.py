# Shared utilities for the Streamlit frontend.
# Handles API calls, session management, and reusable UI components.

import streamlit as st
import requests

API_BASE = "http://localhost:8000"

# ─────────────────────────────────────────
# API HELPERS
# ─────────────────────────────────────────

def get_headers():
    """Returns auth headers with JWT token."""
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}

def api_get(endpoint: str, params: dict = None):
    """Makes an authenticated GET request."""
    try:
        r = requests.get(f"{API_BASE}{endpoint}", headers=get_headers(), params=params)
        return r.json() if r.ok else None
    except:
        return None

def api_post(endpoint: str, data: dict = None, files=None):
    """Makes an authenticated POST request."""
    try:
        headers = get_headers()
        if files:
            r = requests.post(f"{API_BASE}{endpoint}", headers=headers, files=files)
        else:
            r = requests.post(f"{API_BASE}{endpoint}", headers=headers, json=data)
        return r.json(), r.status_code
    except Exception as e:
        return {"detail": str(e)}, 500

def api_patch(endpoint: str, data: dict):
    """Makes an authenticated PATCH request."""
    try:
        r = requests.patch(f"{API_BASE}{endpoint}", headers=get_headers(), json=data)
        return r.json(), r.status_code
    except Exception as e:
        return {"detail": str(e)}, 500

def api_delete(endpoint: str):
    """Makes an authenticated DELETE request."""
    try:
        r = requests.delete(f"{API_BASE}{endpoint}", headers=get_headers())
        return r.json(), r.status_code
    except Exception as e:
        return {"detail": str(e)}, 500

def login_user(email: str, password: str):
    """Logs in and stores token in session state."""
    try:
        r = requests.post(
            f"{API_BASE}/auth/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if r.ok:
            data = r.json()
            st.session_state.token = data["access_token"]
            # Fetch user profile
            me = requests.get(f"{API_BASE}/auth/me", headers=get_headers())
            if me.ok:
                st.session_state.user = me.json()
            return True, "Login successful"
        return False, r.json().get("detail", "Login failed")
    except:
        return False, "Cannot connect to server"

def is_logged_in():
    return "token" in st.session_state and st.session_state.token is not None

def require_login():
    """Redirects to login if not authenticated."""
    if not is_logged_in():
        st.switch_page("pages/0_login.py")

def get_user_role():
    user = st.session_state.get("user", {})
    return user.get("role", "viewer")

def logout():
    for key in ["token", "user"]:
        if key in st.session_state:
            del st.session_state[key]
    st.switch_page("pages/0_login.py")

# ─────────────────────────────────────────
# SHARED UI COMPONENTS
# ─────────────────────────────────────────

def render_sidebar():
    """Renders the navigation sidebar with user info."""
    user = st.session_state.get("user", {})
    role = user.get("role", "viewer").upper()
    name = user.get("full_name", "User")

    with st.sidebar:
        # Logo and branding
        st.markdown("""
        <div style='text-align:center; padding: 1rem 0 2rem 0;'>
            <div style='font-size: 2rem;'>⚡</div>
            <div style='font-family: monospace; font-size: 1.3rem; 
                        color: #00D4FF; font-weight: 700; letter-spacing: 3px;'>
                AUDIT<span style='color:#E2E8F0'>SYS</span>
            </div>
            <div style='font-size: 0.65rem; color: #4A5568; 
                        letter-spacing: 4px; margin-top: 2px;'>
                COMPLIANCE INTELLIGENCE
            </div>
        </div>
        """, unsafe_allow_html=True)

        # User badge
        role_colors = {
            "ADMIN": "#FF4D6D",
            "AUDITOR": "#00D4FF",
            "VIEWER": "#48BB78",
            "GUEST": "#718096"
        }
        color = role_colors.get(role, "#718096")
        st.markdown(f"""
        <div style='background: #0F1628; border: 1px solid #1E2D4D; 
                    border-radius: 8px; padding: 12px; margin-bottom: 20px;
                    border-left: 3px solid {color};'>
            <div style='font-size: 0.7rem; color: #4A5568; 
                        letter-spacing: 2px;'>LOGGED IN AS</div>
            <div style='font-size: 0.95rem; color: #E2E8F0; 
                        font-weight: 600; margin-top: 2px;'>{name}</div>
            <div style='display: inline-block; background: {color}22; 
                        color: {color}; font-size: 0.65rem; padding: 2px 8px; 
                        border-radius: 4px; margin-top: 4px; 
                        letter-spacing: 2px; font-weight: 700;'>{role}</div>
        </div>
        """, unsafe_allow_html=True)

        # Navigation
        st.markdown("<div style='font-size: 0.65rem; color: #4A5568; letter-spacing: 3px; margin-bottom: 8px;'>NAVIGATION</div>", unsafe_allow_html=True)
        st.page_link("pages/1_dashboard.py", label="Dashboard", icon="▪")
        st.page_link("pages/2_documents.py", label="Documents", icon="▪")
        st.page_link("pages/3_ask_ai.py", label="Ask AI", icon="▪")
        st.page_link("pages/4_tasks.py", label="Tasks", icon="▪")

        if role in ["ADMIN", "AUDITOR"]:
            st.page_link("pages/5_audit_logs.py", label="Audit Logs", icon="▪")
        if role == "ADMIN":
            st.page_link("pages/6_admin.py", label="Admin Panel", icon="▪")

        st.markdown("---")
        if st.button("⏻  Logout", use_container_width=True):
            logout()


def metric_card(label: str, value, delta: str = None, color: str = "#00D4FF"):
    """Renders a styled metric card."""
    delta_html = f"<div style='font-size:0.75rem; color:#48BB78; margin-top:4px;'>{delta}</div>" if delta else ""
    st.markdown(f"""
    <div style='background: #0F1628; border: 1px solid #1E2D4D; 
                border-radius: 10px; padding: 20px; 
                border-top: 3px solid {color}; height: 120px;'>
        <div style='font-size: 0.7rem; color: #4A5568; 
                    letter-spacing: 3px; margin-bottom: 8px;'>{label}</div>
        <div style='font-size: 2rem; font-weight: 700; 
                    color: {color}; font-family: monospace;'>{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def status_badge(status: str):
    """Returns colored HTML badge for task/document status."""
    colors = {
        "pending": ("#F6AD55", "#2D1F00"),
        "in_progress": ("#00D4FF", "#001A20"),
        "completed": ("#48BB78", "#00200A"),
        "overdue": ("#FF4D6D", "#200010"),
        "processed": ("#48BB78", "#00200A"),
        "failed": ("#FF4D6D", "#200010"),
        "unknown": ("#718096", "#1A1A1A"),
    }
    fg, bg = colors.get(status, ("#718096", "#1A1A1A"))
    label = status.replace("_", " ").upper()
    return f"""<span style='background:{bg}; color:{fg}; padding: 3px 10px; 
                border-radius: 4px; font-size: 0.7rem; font-weight: 700; 
                letter-spacing: 2px; border: 1px solid {fg}44;'>{label}</span>"""


def page_header(title: str, subtitle: str = ""):
    """Renders a consistent page header."""
    st.markdown(f"""
    <div style='margin-bottom: 2rem; padding-bottom: 1rem; 
                border-bottom: 1px solid #1E2D4D;'>
        <h1 style='font-family: monospace; font-size: 1.8rem; 
                   color: #E2E8F0; margin: 0; letter-spacing: 2px;'>
            {title}
        </h1>
        <p style='color: #4A5568; font-size: 0.85rem; 
                  margin: 4px 0 0 0; letter-spacing: 1px;'>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)