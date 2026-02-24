# Main entry point for the Streamlit app.
# This redirects to login or dashboard based on auth state.

import streamlit as st

st.set_page_config(page_title="AuditSys", page_icon="⚡", layout="wide")

if "token" not in st.session_state:
    st.switch_page("pages/0_login.py")
else:
    st.switch_page("pages/1_dashboard.py")