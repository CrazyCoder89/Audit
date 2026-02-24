# Enhanced Dashboard — real-time compliance intelligence center
# Features: compliance score, charts, calendar, progress bars, quick access, auto-refresh

import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import require_login, render_sidebar, api_get, metric_card, page_header, status_badge
from datetime import datetime, timezone
import time

st.set_page_config(page_title="Dashboard — AuditSys", page_icon="⚡", layout="wide")

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
section[data-testid="stSidebar"] { 
    background: #0A0E1A !important; 
    border-right: 1px solid #1E2D4D; 
}
.stButton > button {
    background: linear-gradient(135deg, #00D4FF, #0088AA) !important;
    color: #0A0E1A !important; border: none !important;
    border-radius: 6px !important; font-weight: 700 !important;
    font-family: 'JetBrains Mono', monospace !important;
    letter-spacing: 2px !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(0,212,255,0.25) !important;
}
.stPlotlyChart { background: transparent !important; }
</style>
""", unsafe_allow_html=True)

require_login()
render_sidebar()

# ── Auto Refresh ──────────────────────────────────────────────────────────
col_title, col_refresh = st.columns([4, 1])
with col_title:
    page_header("◈ DASHBOARD", "Real-time compliance intelligence overview")
with col_refresh:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    auto_refresh = st.toggle("AUTO REFRESH", value=False)
    if auto_refresh:
        st.caption(f"↻ Refreshing every 30s")
        time.sleep(30)
        st.rerun()

# ── Fetch All Data ────────────────────────────────────────────────────────
documents = api_get("/documents/") or []
tasks = api_get("/tasks/") or []
logs = api_get("/audit/", params={"limit": 50}) or []

# Computed stats
total_docs = len(documents)
processed_docs = len([d for d in documents if d.get("status") == "processed"])
failed_docs = len([d for d in documents if d.get("status") == "failed"])
pending_docs = len([d for d in documents if d.get("status") == "pending"])

total_tasks = len(tasks)
pending_tasks = len([t for t in tasks if t.get("status") == "pending"])
in_progress_tasks = len([t for t in tasks if t.get("status") == "in_progress"])
completed_tasks = len([t for t in tasks if t.get("status") == "completed"])
overdue_tasks = len([t for t in tasks if t.get("status") == "overdue"])

# Compliance Score calculation
# Based on: processed docs ratio + task completion ratio + no overdue penalty
doc_score = (processed_docs / total_docs * 40) if total_docs > 0 else 0
task_score = (completed_tasks / total_tasks * 40) if total_tasks > 0 else 0
overdue_penalty = min(overdue_tasks * 5, 20)
compliance_score = max(0, min(100, int(doc_score + task_score + 20 - overdue_penalty)))

# Score color
if compliance_score >= 80:
    score_color = "#48BB78"
    score_label = "COMPLIANT"
elif compliance_score >= 60:
    score_color = "#F6AD55"
    score_label = "AT RISK"
else:
    score_color = "#FF4D6D"
    score_label = "NON-COMPLIANT"

# ── TOP ROW: Compliance Score + Key Metrics ───────────────────────────────
col_score, col_m1, col_m2, col_m3, col_m4 = st.columns([1.5, 1, 1, 1, 1])

with col_score:
    st.markdown(f"""
    <div style='background: #0F1628; border: 1px solid #1E2D4D; border-radius: 10px;
                padding: 20px; border-top: 3px solid {score_color}; height: 120px;
                display: flex; align-items: center; gap: 20px;'>
        <div style='position: relative; width: 80px; height: 80px;'>
            <svg viewBox="0 0 36 36" width="80" height="80">
                <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none" stroke="#1E2D4D" stroke-width="3"/>
                <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none" stroke="{score_color}" stroke-width="3"
                    stroke-dasharray="{compliance_score}, 100"
                    stroke-linecap="round"/>
                <text x="18" y="20.5" text-anchor="middle" 
                      style="font-size: 8px; font-family: monospace; 
                             fill: {score_color}; font-weight: 700;">
                    {compliance_score}%
                </text>
            </svg>
        </div>
        <div>
            <div style='font-size: 0.65rem; color: #4A5568; letter-spacing: 3px;'>
                COMPLIANCE SCORE
            </div>
            <div style='font-size: 1.1rem; color: {score_color}; font-weight: 700; 
                        letter-spacing: 2px; margin-top: 4px;'>
                {score_label}
            </div>
            <div style='font-size: 0.65rem; color: #4A5568; margin-top: 2px;'>
                {overdue_tasks} overdue · {failed_docs} failed
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_m1:
    metric_card("DOCUMENTS", total_docs, f"{processed_docs} processed", "#00D4FF")
with col_m2:
    metric_card("TOTAL TASKS", total_tasks, f"{pending_tasks} pending", "#F6AD55")
with col_m3:
    metric_card("COMPLETED", completed_tasks, "tasks done", "#48BB78")
with col_m4:
    metric_card("OVERDUE", overdue_tasks, "need attention",
                "#FF4D6D" if overdue_tasks > 0 else "#48BB78")

st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

# ── SECOND ROW: Charts ────────────────────────────────────────────────────
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

col_chart1, col_chart2, col_chart3 = st.columns(3)

if PLOTLY_AVAILABLE:
    # Chart 1: Task Status Donut
    with col_chart1:
        st.markdown("""
        <div style='font-size: 0.7rem; color: #4A5568; letter-spacing: 3px; 
                    margin-bottom: 8px;'>TASK STATUS</div>
        """, unsafe_allow_html=True)

        if total_tasks > 0:
            fig1 = go.Figure(data=[go.Pie(
                labels=["Pending", "In Progress", "Completed", "Overdue"],
                values=[pending_tasks, in_progress_tasks, completed_tasks, overdue_tasks],
                hole=0.6,
                marker=dict(colors=["#F6AD55", "#00D4FF", "#48BB78", "#FF4D6D"],
                           line=dict(color="#0A0E1A", width=2))
            )])
            fig1.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="JetBrains Mono", color="#E2E8F0", size=11),
                showlegend=True,
                legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
                margin=dict(t=10, b=10, l=10, r=10),
                height=220
            )
            st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown("<p style='color:#4A5568; text-align:center; padding:60px 0;'>No tasks yet</p>",
                       unsafe_allow_html=True)

    # Chart 2: Document Categories Bar
    with col_chart2:
        st.markdown("""
        <div style='font-size: 0.7rem; color: #4A5568; letter-spacing: 3px; 
                    margin-bottom: 8px;'>DOCUMENT CATEGORIES</div>
        """, unsafe_allow_html=True)

        if documents:
            cat_counts = {}
            for doc in documents:
                c = doc.get("category", "unknown")
                cat_counts[c] = cat_counts.get(c, 0) + 1

            cat_colors_map = {
                "financial": "#48BB78", "legal": "#F6AD55",
                "compliance": "#00D4FF", "hr": "#9F7AEA", "unknown": "#718096"
            }

            fig2 = go.Figure(data=[go.Bar(
                x=list(cat_counts.keys()),
                y=list(cat_counts.values()),
                marker=dict(
                    color=[cat_colors_map.get(k, "#718096") for k in cat_counts.keys()],
                    line=dict(color="#0A0E1A", width=1)
                )
            )])
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="JetBrains Mono", color="#E2E8F0", size=10),
                xaxis=dict(gridcolor="#1E2D4D", tickfont=dict(size=9)),
                yaxis=dict(gridcolor="#1E2D4D", tickfont=dict(size=9)),
                margin=dict(t=10, b=10, l=10, r=10),
                height=220
            )
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown("<p style='color:#4A5568; text-align:center; padding:60px 0;'>No documents yet</p>",
                       unsafe_allow_html=True)

    # Chart 3: Activity over time line chart
    with col_chart3:
        st.markdown("""
        <div style='font-size: 0.7rem; color: #4A5568; letter-spacing: 3px; 
                    margin-bottom: 8px;'>ACTIVITY TIMELINE</div>
        """, unsafe_allow_html=True)

        if logs:
            # Group logs by date
            date_counts = {}
            for log in logs:
                date = log.get("created_at", "")[:10]
                if date:
                    date_counts[date] = date_counts.get(date, 0) + 1

            sorted_dates = sorted(date_counts.keys())
            fig3 = go.Figure(data=[go.Scatter(
                x=sorted_dates,
                y=[date_counts[d] for d in sorted_dates],
                mode="lines+markers",
                line=dict(color="#00D4FF", width=2),
                marker=dict(color="#00D4FF", size=6,
                           line=dict(color="#0A0E1A", width=2)),
                fill="tozeroy",
                fillcolor="rgba(0, 212, 255, 0.05)"
            )])
            fig3.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="JetBrains Mono", color="#E2E8F0", size=10),
                xaxis=dict(gridcolor="#1E2D4D", tickfont=dict(size=8)),
                yaxis=dict(gridcolor="#1E2D4D", tickfont=dict(size=9)),
                margin=dict(t=10, b=10, l=10, r=10),
                height=220
            )
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown("<p style='color:#4A5568; text-align:center; padding:60px 0;'>No activity yet</p>",
                       unsafe_allow_html=True)
else:
    # Fallback if plotly not installed
    with col_chart1:
        st.info("Install plotly for charts: pip install plotly")

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

# ── THIRD ROW: Task Progress + Calendar + Recent Docs ─────────────────────
col_left, col_mid, col_right = st.columns([1.2, 1, 1])

# Task Progress Bars
with col_left:
    st.markdown("""
    <div style='background: #0F1628; border: 1px solid #1E2D4D; border-radius: 10px;
                padding: 20px; border-top: 3px solid #F6AD55;'>
        <div style='font-size: 0.7rem; color: #4A5568; letter-spacing: 3px; 
                    margin-bottom: 16px;'>TASK PROGRESS</div>
    """, unsafe_allow_html=True)

    if total_tasks > 0:
        task_bars = [
            ("COMPLETED", completed_tasks, "#48BB78"),
            ("IN PROGRESS", in_progress_tasks, "#00D4FF"),
            ("PENDING", pending_tasks, "#F6AD55"),
            ("OVERDUE", overdue_tasks, "#FF4D6D"),
        ]
        for label, count, color in task_bars:
            pct = int((count / total_tasks) * 100)
            st.markdown(f"""
            <div style='margin-bottom: 14px;'>
                <div style='display: flex; justify-content: space-between; margin-bottom: 5px;'>
                    <span style='color: #E2E8F0; font-size: 0.75rem;'>{label}</span>
                    <span style='color: {color}; font-size: 0.75rem; font-weight: 700;'>
                        {count} ({pct}%)
                    </span>
                </div>
                <div style='background: #1E2D4D; border-radius: 3px; height: 6px;'>
                    <div style='background: linear-gradient(90deg, {color}, {color}88); 
                                width: {pct}%; height: 6px; border-radius: 3px;
                                transition: width 0.5s ease;'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Overall completion ring
        completion_pct = int((completed_tasks / total_tasks) * 100)
        st.markdown(f"""
        <div style='margin-top: 16px; padding-top: 16px; border-top: 1px solid #1E2D4D;
                    display: flex; align-items: center; gap: 12px;'>
            <svg viewBox="0 0 36 36" width="50" height="50">
                <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none" stroke="#1E2D4D" stroke-width="3"/>
                <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none" stroke="#48BB78" stroke-width="3"
                    stroke-dasharray="{completion_pct}, 100" stroke-linecap="round"/>
                <text x="18" y="21" text-anchor="middle"
                      style="font-size: 7px; font-family: monospace; fill: #48BB78; font-weight: 700;">
                    {completion_pct}%
                </text>
            </svg>
            <div>
                <div style='color: #4A5568; font-size: 0.65rem; letter-spacing: 2px;'>COMPLETION</div>
                <div style='color: #48BB78; font-size: 0.9rem; font-weight: 700;'>
                    {completed_tasks}/{total_tasks} tasks
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("<p style='color:#4A5568;'>No tasks yet</p>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# Calendar View
with col_mid:
    st.markdown("""
    <div style='background: #0F1628; border: 1px solid #1E2D4D; border-radius: 10px;
                padding: 20px; border-top: 3px solid #9F7AEA;'>
        <div style='font-size: 0.7rem; color: #4A5568; letter-spacing: 3px; 
                    margin-bottom: 16px;'>UPCOMING DEADLINES</div>
    """, unsafe_allow_html=True)

    # Get tasks with deadlines
    tasks_with_deadlines = [
        t for t in tasks
        if t.get("deadline") and t.get("status") not in ["completed"]
    ]
    tasks_with_deadlines.sort(key=lambda x: x.get("deadline", ""))

    if tasks_with_deadlines:
        now = datetime.now(timezone.utc)
        for task in tasks_with_deadlines[:6]:
            deadline_str = task.get("deadline", "")[:10]
            title = task.get("title", "Untitled")[:30]
            priority = task.get("priority", "medium")

            try:
                deadline_dt = datetime.fromisoformat(task.get("deadline", "").replace("Z", "+00:00"))
                days_left = (deadline_dt - now).days
                if days_left < 0:
                    time_label = f"OVERDUE {abs(days_left)}d"
                    t_color = "#FF4D6D"
                elif days_left == 0:
                    time_label = "DUE TODAY"
                    t_color = "#FF4D6D"
                elif days_left <= 3:
                    time_label = f"{days_left}d left"
                    t_color = "#F6AD55"
                else:
                    time_label = f"{days_left}d left"
                    t_color = "#48BB78"
            except:
                time_label = deadline_str
                t_color = "#718096"

            priority_colors = {
                "critical": "#FF4D6D", "high": "#F6AD55",
                "medium": "#00D4FF", "low": "#48BB78"
            }
            p_color = priority_colors.get(priority, "#718096")

            st.markdown(f"""
            <div style='display: flex; align-items: center; padding: 8px 0;
                        border-bottom: 1px solid #0A0E1A;'>
                <div style='width: 8px; height: 8px; border-radius: 50%; 
                            background: {p_color}; margin-right: 10px; flex-shrink: 0;'></div>
                <div style='flex: 1; overflow: hidden;'>
                    <div style='color: #E2E8F0; font-size: 0.75rem; 
                                white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>
                        {title}
                    </div>
                    <div style='color: #4A5568; font-size: 0.65rem;'>{deadline_str}</div>
                </div>
                <div style='color: {t_color}; font-size: 0.65rem; font-weight: 700; 
                            margin-left: 8px; white-space: nowrap;'>
                    {time_label}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <p style='color:#4A5568; font-size: 0.8rem; text-align: center; 
                  padding: 30px 0;'>No upcoming deadlines</p>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# Recent Documents Quick Access
with col_right:
    st.markdown("""
    <div style='background: #0F1628; border: 1px solid #1E2D4D; border-radius: 10px;
                padding: 20px; border-top: 3px solid #00D4FF;'>
        <div style='font-size: 0.7rem; color: #4A5568; letter-spacing: 3px; 
                    margin-bottom: 16px;'>RECENT DOCUMENTS</div>
    """, unsafe_allow_html=True)

    recent_docs = sorted(documents, key=lambda x: x.get("created_at", ""), reverse=True)[:6]

    if recent_docs:
        for doc in recent_docs:
            status = doc.get("status", "unknown")
            filename = doc.get("filename", "unknown")
            category = doc.get("category", "unknown").upper()
            date = doc.get("created_at", "")[:10]
            size_kb = round(doc.get("file_size", 0) / 1024, 1)

            status_colors = {
                "processed": "#48BB78", "pending": "#F6AD55",
                "failed": "#FF4D6D", "unknown": "#718096"
            }
            s_color = status_colors.get(status, "#718096")
            cat_colors = {
                "FINANCIAL": "#48BB78", "LEGAL": "#F6AD55",
                "COMPLIANCE": "#00D4FF", "HR": "#9F7AEA", "UNKNOWN": "#718096"
            }
            c_color = cat_colors.get(category, "#718096")

            st.markdown(f"""
            <div style='padding: 10px 0; border-bottom: 1px solid #0A0E1A;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div style='color: #E2E8F0; font-size: 0.75rem; overflow: hidden;
                                text-overflow: ellipsis; white-space: nowrap; max-width: 150px;'>
                        📄 {filename}
                    </div>
                    <div style='width: 8px; height: 8px; border-radius: 50%; 
                                background: {s_color}; flex-shrink: 0;'></div>
                </div>
                <div style='display: flex; gap: 8px; margin-top: 3px;'>
                    <span style='color: {c_color}; font-size: 0.65rem; font-weight: 700;'>
                        {category}
                    </span>
                    <span style='color: #4A5568; font-size: 0.65rem;'>{size_kb} KB</span>
                    <span style='color: #4A5568; font-size: 0.65rem;'>{date}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <p style='color:#4A5568; font-size: 0.8rem; text-align: center; 
                  padding: 30px 0;'>No documents yet</p>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

# ── BOTTOM ROW: Recent Activity Feed ─────────────────────────────────────
st.markdown("""
<div style='background: #0F1628; border: 1px solid #1E2D4D; border-radius: 10px;
            padding: 20px; border-top: 3px solid #48BB78;'>
    <div style='font-size: 0.7rem; color: #4A5568; letter-spacing: 3px; 
                margin-bottom: 16px;'>LIVE ACTIVITY FEED</div>
""", unsafe_allow_html=True)

action_icons = {
    "user.login": "→", "user.register": "✦", "user.login_failed": "✕",
    "document.upload": "↑", "document.ask": "◈", "document.view": "◉",
    "document.delete": "✕", "task.create": "✚", "task.update": "↻", "task.delete": "✕",
}
action_colors = {
    "user.login": "#48BB78", "user.register": "#00D4FF", "user.login_failed": "#FF4D6D",
    "document.upload": "#00D4FF", "document.ask": "#F6AD55", "document.view": "#718096",
    "document.delete": "#FF4D6D", "task.create": "#48BB78",
    "task.update": "#F6AD55", "task.delete": "#FF4D6D",
}

if logs:
    # Show in a grid of 2 columns
    feed_cols = st.columns(2)
    for i, log in enumerate(logs[:10]):
        action = log.get("action", "unknown")
        icon = action_icons.get(action, "·")
        color = action_colors.get(action, "#718096")
        timestamp = log.get("created_at", "")[:19].replace("T", " ")
        user_id = log.get("user_id", "sys")
        resource = f"{log.get('resource_type', '')}#{log.get('resource_id', '')}" if log.get('resource_type') else ""

        with feed_cols[i % 2]:
            st.markdown(f"""
            <div style='display: flex; align-items: center; padding: 8px 12px;
                        background: #0A0E1A; border-radius: 6px; margin-bottom: 6px;
                        border-left: 3px solid {color};'>
                <div style='color: {color}; font-size: 0.9rem; width: 20px;'>{icon}</div>
                <div style='flex: 1; margin-left: 10px;'>
                    <span style='color: #E2E8F0; font-size: 0.75rem; font-weight: 600;'>
                        {action}
                    </span>
                    <span style='color: #4A5568; font-size: 0.7rem; margin-left: 6px;'>
                        {resource}
                    </span>
                </div>
                <div style='color: #4A5568; font-size: 0.65rem; white-space: nowrap;'>
                    {timestamp[11:]}
                </div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.markdown("<p style='color:#4A5568;'>No activity yet</p>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ── Last updated timestamp ────────────────────────────────────────────────
st.markdown(f"""
<div style='text-align: right; color: #1E2D4D; font-size: 0.65rem; 
            letter-spacing: 2px; margin-top: 12px;'>
    LAST UPDATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
</div>
""", unsafe_allow_html=True)


