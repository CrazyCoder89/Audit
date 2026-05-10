# Global search page — search across documents and tasks simultaneously.

import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import require_login, render_sidebar, api_get, page_header, status_badge

st.set_page_config(page_title="Search — AuditSys", page_icon="⚡", layout="wide")

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
    border: 2px solid #1E2D4D !important;
    border-radius: 8px !important;
    color: #E2E8F0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1rem !important;
    padding: 14px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #00D4FF !important;
    box-shadow: 0 0 0 3px rgba(0,212,255,0.1) !important;
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
page_header("◈ SEARCH", "Search across all documents and tasks")

# ── Search Input ──────────────────────────────────────────────────────────
col_input, col_btn = st.columns([5, 1])
with col_input:
    query = st.text_input(
        "Search",
        placeholder="Search documents, tasks, categories, priorities...",
        label_visibility="collapsed",
        key="global_search"
    )
with col_btn:
    search_btn = st.button("SEARCH →", use_container_width=True)

if not query:
    st.markdown("""
    <div style='text-align: center; padding: 4rem 0;'>
        <div style='font-size: 3rem; margin-bottom: 1rem;'>◈</div>
        <div style='color: #4A5568; font-size: 0.9rem; letter-spacing: 2px;'>
            TYPE TO SEARCH ACROSS DOCUMENTS AND TASKS
        </div>
        <div style='color: #2D3748; font-size: 0.75rem; margin-top: 8px;'>
            Search by filename, category, task title, description, priority, or status
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Fetch Results ──────────────────────────────────────────────────────────
doc_results = api_get("/documents/search/query", params={"q": query}) or []
task_results = api_get("/tasks/search/query", params={"q": query}) or []

total = len(doc_results) + len(task_results)

st.markdown(f"""
<div style='font-size: 0.7rem; color: #4A5568; letter-spacing: 3px; margin: 16px 0 20px 0;'>
    {total} RESULTS FOR "{query.upper()}" —
    {len(doc_results)} DOCUMENTS · {len(task_results)} TASKS
</div>
""", unsafe_allow_html=True)

if total == 0:
    st.markdown(f"""
    <div style='background: #0F1628; border: 1px solid #1E2D4D; border-radius: 10px;
                padding: 40px; text-align: center;'>
        <div style='font-size: 2rem; margin-bottom: 8px;'>◈</div>
        <div style='color: #4A5568; letter-spacing: 2px;'>NO RESULTS FOUND</div>
        <div style='color: #2D3748; font-size: 0.75rem; margin-top: 8px;'>
            Try a different search term
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

col_docs, col_tasks = st.columns(2)

# ── Document Results ──────────────────────────────────────────────────────
with col_docs:
    st.markdown(f"""
    <div style='font-size: 0.7rem; color: #00D4FF; letter-spacing: 3px; margin-bottom: 10px;'>
        ▪ DOCUMENTS ({len(doc_results)})
    </div>
    """, unsafe_allow_html=True)

    if not doc_results:
        st.markdown("""
        <div style='background: #0F1628; border: 1px solid #1E2D4D; border-radius: 8px;
                    padding: 20px; text-align: center; color: #4A5568; font-size: 0.8rem;'>
            No documents found
        </div>
        """, unsafe_allow_html=True)
    else:
        cat_colors = {
            "financial": "#48BB78", "legal": "#F6AD55",
            "compliance": "#00D4FF", "hr": "#9F7AEA", "unknown": "#718096"
        }
        for doc in doc_results:
            category = doc.get("category", "unknown")
            status = doc.get("status", "unknown")
            c_color = cat_colors.get(category, "#718096")
            size_kb = round(doc.get("file_size", 0) / 1024, 1)
            date = doc.get("created_at", "")[:10]

            # Highlight matching text
            filename = doc.get("filename", "")
            highlighted = filename.replace(
                query, f"<mark style='background:#00D4FF22; color:#00D4FF;'>{query}</mark>"
            )

            st.markdown(f"""
            <div style='background: #0F1628; border: 1px solid #1E2D4D; border-radius: 8px;
                        padding: 14px 16px; margin-bottom: 8px;
                        border-left: 3px solid {c_color};'>
                <div style='color: #E2E8F0; font-size: 0.85rem; font-weight: 600;
                            margin-bottom: 6px;'>
                    📄 {highlighted}
                </div>
                <div style='display: flex; gap: 10px; align-items: center;
                            flex-wrap: wrap;'>
                    <span style='color: {c_color}; font-size: 0.7rem;
                                 font-weight: 700;'>{category.upper()}</span>
                    {status_badge(status)}
                    <span style='color: #4A5568; font-size: 0.7rem;'>{size_kb} KB</span>
                    <span style='color: #4A5568; font-size: 0.7rem;'>{date}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ── Task Results ──────────────────────────────────────────────────────────
with col_tasks:
    st.markdown(f"""
    <div style='font-size: 0.7rem; color: #F6AD55; letter-spacing: 3px; margin-bottom: 10px;'>
        ▪ TASKS ({len(task_results)})
    </div>
    """, unsafe_allow_html=True)

    if not task_results:
        st.markdown("""
        <div style='background: #0F1628; border: 1px solid #1E2D4D; border-radius: 8px;
                    padding: 20px; text-align: center; color: #4A5568; font-size: 0.8rem;'>
            No tasks found
        </div>
        """, unsafe_allow_html=True)
    else:
        priority_colors = {
            "critical": "#FF4D6D", "high": "#F6AD55",
            "medium": "#00D4FF", "low": "#48BB78"
        }
        for task in task_results:
            priority = task.get("priority", "medium")
            status = task.get("status", "pending")
            p_color = priority_colors.get(priority, "#718096")
            deadline = task.get("deadline", "")[:10] if task.get("deadline") else "No deadline"

            title = task.get("title", "")
            highlighted_title = title.replace(
                query, f"<mark style='background:#F6AD5522; color:#F6AD55;'>{query}</mark>"
            )
            desc = task.get("description", "") or ""
            short_desc = desc[:80] + "..." if len(desc) > 80 else desc

            st.markdown(f"""
            <div style='background: #0F1628; border: 1px solid #1E2D4D; border-radius: 8px;
                        padding: 14px 16px; margin-bottom: 8px;
                        border-left: 3px solid {p_color};'>
                <div style='color: #E2E8F0; font-size: 0.85rem; font-weight: 600;
                            margin-bottom: 4px;'>
                    {highlighted_title}
                </div>
                <div style='color: #4A5568; font-size: 0.75rem; margin-bottom: 6px;'>
                    {short_desc}
                </div>
                <div style='display: flex; gap: 10px; align-items: center; flex-wrap: wrap;'>
                    <span style='color: {p_color}; font-size: 0.7rem;
                                 font-weight: 700;'>{priority.upper()}</span>
                    {status_badge(status)}
                    <span style='color: #4A5568; font-size: 0.7rem;'>⏰ {deadline}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)




            