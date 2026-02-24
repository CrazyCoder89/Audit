# Ask AI page — query any processed document using RAG.

import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import require_login, render_sidebar, api_get, api_post, page_header

st.set_page_config(page_title="Ask AI — AuditSys", page_icon="⚡", layout="wide")

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
.stTextInput > div > div > input {
    background: #0F1628 !important; border: 1px solid #1E2D4D !important;
    border-radius: 6px !important; color: #E2E8F0 !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.stTextInput > div > div > input:focus { border-color: #00D4FF !important; }
.stButton > button {
    background: linear-gradient(135deg, #00D4FF, #0088AA) !important;
    color: #0A0E1A !important; border: none !important;
    border-radius: 6px !important; font-weight: 700 !important;
    letter-spacing: 2px !important;
}
.stSelectbox > div > div {
    background: #0F1628 !important; border: 1px solid #1E2D4D !important;
    border-radius: 6px !important; color: #E2E8F0 !important;
}
</style>
""", unsafe_allow_html=True)

require_login()
render_sidebar()
page_header("◈ ASK AI", "Query your documents with AI-powered intelligence")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "selected_doc_id" not in st.session_state:
    st.session_state.selected_doc_id = None

# ── Document Selector ─────────────────────────────────────────────────────
documents = api_get("/documents/") or []
processed_docs = [d for d in documents if d.get("status") == "processed"]

if not processed_docs:
    st.markdown("""
    <div style='background: #0F1628; border: 1px solid #1E2D4D; border-radius: 10px;
                padding: 40px; text-align: center; border-top: 3px solid #F6AD55;'>
        <div style='font-size: 2rem; margin-bottom: 8px;'>◈</div>
        <div style='color: #F6AD55; letter-spacing: 2px; font-size: 0.9rem;'>
            NO PROCESSED DOCUMENTS
        </div>
        <div style='color: #4A5568; font-size: 0.75rem; margin-top: 8px;'>
            Upload and process a PDF in the Documents page first
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Document selection
doc_options = {f"[{d['id']}] {d['filename']}": d['id'] for d in processed_docs}

col1, col2 = st.columns([3, 1])
with col1:
    selected_label = st.selectbox(
        "SELECT DOCUMENT",
        options=list(doc_options.keys()),
        label_visibility="collapsed"
    )
with col2:
    if st.button("CLEAR CHAT", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

selected_doc_id = doc_options[selected_label]

# Reset chat if document changed
if st.session_state.selected_doc_id != selected_doc_id:
    st.session_state.chat_history = []
    st.session_state.selected_doc_id = selected_doc_id

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

# ── Chat History ──────────────────────────────────────────────────────────
chat_container = st.container()

with chat_container:
    if not st.session_state.chat_history:
        st.markdown(f"""
        <div style='background: #0F1628; border: 1px solid #1E2D4D; border-radius: 10px;
                    padding: 30px; text-align: center; border-left: 3px solid #00D4FF;'>
            <div style='color: #00D4FF; font-size: 0.8rem; letter-spacing: 2px;'>
                DOCUMENT LOADED
            </div>
            <div style='color: #E2E8F0; font-size: 0.85rem; margin-top: 8px;'>
                {selected_label}
            </div>
            <div style='color: #4A5568; font-size: 0.75rem; margin-top: 8px;'>
                Ask me anything about this document
            </div>
        </div>
        """, unsafe_allow_html=True)

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"""
            <div style='display: flex; justify-content: flex-end; margin: 12px 0;'>
                <div style='background: #0D2035; border: 1px solid #00D4FF44; 
                            border-radius: 10px 10px 0 10px; padding: 12px 16px;
                            max-width: 70%; color: #E2E8F0; font-size: 0.85rem;'>
                    {msg["content"]}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style='display: flex; justify-content: flex-start; margin: 12px 0;'>
                <div style='margin-right: 10px; color: #00D4FF; font-size: 1.2rem;'>⚡</div>
                <div style='background: #0F1628; border: 1px solid #1E2D4D;
                            border-radius: 10px 10px 10px 0; padding: 12px 16px;
                            max-width: 75%; color: #E2E8F0; font-size: 0.85rem; 
                            line-height: 1.6;'>
                    {msg["content"]}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Show sources if available
            if msg.get("sources"):
                with st.expander("◈ View Sources"):
                    for src in msg["sources"]:
                        st.markdown(f"""
                        <div style='background: #0A0E1A; border: 1px solid #1E2D4D; 
                                    border-radius: 6px; padding: 8px 12px; margin-bottom: 6px;
                                    font-size: 0.75rem;'>
                            <span style='color: #00D4FF;'>📄 {src.get('source', 'Unknown')}</span>
                            <span style='color: #4A5568; margin-left: 8px;'>
                                Page {src.get('page', '?')}
                            </span>
                            <span style='color: #48BB78; margin-left: 8px;'>
                                {int(src.get('relevance', 0) * 100)}% relevant
                            </span>
                        </div>
                        """, unsafe_allow_html=True)

# ── Question Input ────────────────────────────────────────────────────────
st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
col_q, col_btn = st.columns([5, 1])

with col_q:
    question = st.text_input(
        "Ask a question",
        placeholder="What are the main compliance requirements in this document?",
        label_visibility="collapsed",
        key="question_input"
    )
with col_btn:
    ask_btn = st.button("ASK →", use_container_width=True)

if ask_btn and question:
    st.session_state.chat_history.append({"role": "user", "content": question})

    with st.spinner("⚡ Analyzing document..."):
        result, status = api_post(f"/documents/{selected_doc_id}/ask", {"question": question})

    if status == 200:
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": result.get("answer", "No answer found"),
            "sources": result.get("sources", [])
        })
    else:
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": f"Error: {result.get('detail', 'Something went wrong')}",
            "sources": []
        })
    st.rerun()