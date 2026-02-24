# Login and registration page.
# This is the entry point — no other page is accessible without logging in.

import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import login_user, is_logged_in, api_post

st.set_page_config(
    page_title="AuditSys — Login",
    page_icon="⚡",
    layout="centered"
)

# Redirect if already logged in
if is_logged_in():
    st.switch_page("pages/1_dashboard.py")

# ── Styles ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Syne:wght@400;600;700;800&display=swap');

* { font-family: 'JetBrains Mono', monospace; }

.stApp {
    background: #0A0E1A;
    background-image: 
        radial-gradient(ellipse at 20% 50%, #0D1F3C 0%, transparent 60%),
        radial-gradient(ellipse at 80% 20%, #001A20 0%, transparent 50%);
}

/* Grid background */
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image: 
        linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px);
    background-size: 50px 50px;
    pointer-events: none;
    z-index: 0;
}

.stTextInput > div > div > input {
    background: #0F1628 !important;
    border: 1px solid #1E2D4D !important;
    border-radius: 6px !important;
    color: #E2E8F0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    padding: 12px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #00D4FF !important;
    box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.1) !important;
}

.stButton > button {
    background: linear-gradient(135deg, #00D4FF, #0088AA) !important;
    color: #0A0E1A !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 700 !important;
    font-family: 'JetBrains Mono', monospace !important;
    letter-spacing: 2px !important;
    padding: 12px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(0, 212, 255, 0.3) !important;
}

div[data-testid="stTabs"] button {
    color: #4A5568 !important;
    font-family: 'JetBrains Mono', monospace !important;
    letter-spacing: 2px !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #00D4FF !important;
    border-bottom-color: #00D4FF !important;
}

.stAlert { border-radius: 6px !important; }
</style>
""", unsafe_allow_html=True)

# ── Hero Section ─────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align: center; padding: 3rem 0 2rem 0;'>
    <div style='font-size: 3.5rem; margin-bottom: 0.5rem;'>⚡</div>
    <div style='font-family: monospace; font-size: 2.5rem; font-weight: 700;
                color: #E2E8F0; letter-spacing: 6px;'>
        AUDIT<span style='color: #00D4FF;'>SYS</span>
    </div>
    <div style='color: #4A5568; font-size: 0.75rem; letter-spacing: 5px; 
                margin-top: 6px;'>
        AI-POWERED COMPLIANCE INTELLIGENCE
    </div>
    <div style='width: 60px; height: 2px; background: linear-gradient(90deg, transparent, #00D4FF, transparent);
                margin: 1.5rem auto;'></div>
</div>
""", unsafe_allow_html=True)

# ── Login / Register Tabs ─────────────────────────────────────────────────
tab1, tab2 = st.tabs(["◈  SIGN IN", "◈  REGISTER"])

with tab1:
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    email = st.text_input("EMAIL", placeholder="admin@audit.com", key="login_email")
    password = st.text_input("PASSWORD", type="password", placeholder="••••••••", key="login_pass")
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    if st.button("AUTHENTICATE →", use_container_width=True, key="login_btn"):
        if email and password:
            with st.spinner("Authenticating..."):
                success, message = login_user(email, password)
                if success:
                    st.success("✓ Access granted")
                    st.switch_page("pages/1_dashboard.py")
                else:
                    st.error(f"✗ {message}")
        else:
            st.warning("Enter your credentials")

with tab2:
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    reg_name = st.text_input("FULL NAME", placeholder="John Smith", key="reg_name")
    reg_email = st.text_input("EMAIL", placeholder="john@company.com", key="reg_email")
    reg_password = st.text_input("PASSWORD", type="password", placeholder="••••••••", key="reg_pass")
    reg_role = st.selectbox("ROLE", ["viewer", "auditor", "admin"], key="reg_role")
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    if st.button("CREATE ACCOUNT →", use_container_width=True, key="reg_btn"):
        if reg_name and reg_email and reg_password:
            with st.spinner("Creating account..."):
                result, status = api_post("/auth/register", {
                    "full_name": reg_name,
                    "email": reg_email,
                    "password": reg_password,
                    "role": reg_role
                })
                if status == 200:
                    st.success("✓ Account created — sign in above")
                else:
                    st.error(f"✗ {result.get('detail', 'Registration failed')}")
        else:
            st.warning("Fill in all fields")

# ── Footer ────────────────────────────────────────────────────────────────
st.markdown("""
<div style='text-align: center; margin-top: 3rem; color: #1E2D4D; 
            font-size: 0.7rem; letter-spacing: 2px;'>
    SECURED · COMPLIANT · INTELLIGENT
</div>
""", unsafe_allow_html=True)


