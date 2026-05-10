# Analytics page — user activity heatmap + document risk scoring

import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import require_login, render_sidebar, api_get, api_post, page_header, get_user_role
from datetime import datetime

st.set_page_config(page_title="Analytics — AuditSys", page_icon="⚡", layout="wide")

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
</style>
""", unsafe_allow_html=True)

require_login()
render_sidebar()

role = get_user_role()
if role not in ["admin", "auditor"]:
    st.error("✗ Access denied — Admin or Auditor role required")
    st.stop()

page_header("◈ ANALYTICS", "User activity intelligence and document risk assessment")

tab1, tab2, tab3, tab4 = st.tabs([
    "◈  USER ACTIVITY HEATMAP",
    "◈  DOCUMENT RISK SCORING",
    "◈  AI TASK SUGGESTIONS",
    "◈  ANOMALY DETECTION"
])

# ══════════════════════════════════════════════════════════════
# TAB 1 — USER ACTIVITY HEATMAP
# ══════════════════════════════════════════════════════════════
with tab1:
    with st.spinner("Loading activity data..."):
        data = api_get("/analytics/user-activity")

    if not data:
        st.error("Failed to load activity data")
        st.stop()

    # ── Summary metrics ───────────────────────────────────────
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    most_active = data.get("most_active_user") or {}
    metrics = [
        (col1, "TOTAL ACTIONS (30D)", data.get("total_actions_30d", 0), "#00D4FF"),
        (col2, "MOST ACTIVE USER", most_active.get("name", "—"), "#F6AD55"),
        (col3, "PEAK HOUR", data.get("peak_hour_label", "—"), "#48BB78"),
        (col4, "USERS TRACKED", len(data.get("user_activity", [])), "#9F7AEA"),
    ]
    for col, label, value, color in metrics:
        with col:
            st.markdown(f"""
            <div style='background: #0F1628; border: 1px solid #1E2D4D;
                        border-radius: 10px; padding: 20px;
                        border-top: 3px solid {color}; height: 110px;'>
                <div style='font-size: 0.65rem; color: #4A5568;
                            letter-spacing: 3px; margin-bottom: 8px;'>{label}</div>
                <div style='font-size: 1.6rem; font-weight: 700;
                            color: {color}; font-family: monospace;'>{value}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # ── Heatmap ───────────────────────────────────────────────
    try:
        import plotly.graph_objects as go

        heatmap_data = data.get("heatmap", [[0]*24 for _ in range(7)])
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        hours = [f"{h:02d}:00" for h in range(24)]

        fig_heatmap = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=hours,
            y=days,
            colorscale=[
                [0, "#0A0E1A"],
                [0.2, "#0D2035"],
                [0.4, "#0D3F5F"],
                [0.6, "#0070A0"],
                [0.8, "#00A8CC"],
                [1.0, "#00D4FF"]
            ],
            showscale=True,
            colorbar=dict(
                title=dict(text="Actions", font=dict(color="#E2E8F0", size=10)),
                tickfont=dict(color="#E2E8F0", size=9),
                bgcolor="#0F1628",
                bordercolor="#1E2D4D"
            ),
            hovertemplate="<b>%{y}</b><br>%{x}<br>Actions: %{z}<extra></extra>"
        ))

        fig_heatmap.update_layout(
            title=dict(text="Activity Heatmap — Last 30 Days",
                      font=dict(color="#E2E8F0", size=13), x=0),
            paper_bgcolor="#0F1628",
            plot_bgcolor="#0F1628",
            font=dict(family="JetBrains Mono", color="#E2E8F0", size=10),
            xaxis=dict(
                tickfont=dict(size=8),
                gridcolor="#1E2D4D",
                title=dict(text="Hour of Day", font=dict(size=10, color="#E2E8F0"))
            ),
            yaxis=dict(tickfont=dict(size=9), gridcolor="#1E2D4D"),
            margin=dict(t=40, b=40, l=10, r=10),
            height=300
        )
        st.plotly_chart(fig_heatmap, use_container_width=True,
                        config={"displayModeBar": False})

        # ── Daily activity line chart ─────────────────────────
        daily = data.get("daily_activity", {})
        if daily:
            fig_daily = go.Figure(data=go.Scatter(
                x=list(daily.keys()),
                y=list(daily.values()),
                mode="lines+markers",
                line=dict(color="#00D4FF", width=2),
                marker=dict(color="#00D4FF", size=5,
                           line=dict(color="#0A0E1A", width=1)),
                fill="tozeroy",
                fillcolor="rgba(0, 212, 255, 0.06)",
                hovertemplate="<b>%{x}</b><br>Actions: %{y}<extra></extra>"
            ))
            fig_daily.update_layout(
                title=dict(text="Daily Activity — Last 30 Days",
                          font=dict(color="#E2E8F0", size=13), x=0),
                paper_bgcolor="#0F1628",
                plot_bgcolor="#0F1628",
                font=dict(family="JetBrains Mono", color="#E2E8F0", size=10),
                xaxis=dict(gridcolor="#1E2D4D", tickfont=dict(size=8)),
                yaxis=dict(
                    gridcolor="#1E2D4D",
                    tickfont=dict(size=9),
                    title=dict(text="Actions", font=dict(size=10, color="#E2E8F0"))
                ),
                margin=dict(t=40, b=10, l=10, r=10),
                height=250
            )
            st.plotly_chart(fig_daily, use_container_width=True,
                            config={"displayModeBar": False})

    except ImportError:
        st.warning("Install plotly: pip install plotly")

    # ── Per-user breakdown ────────────────────────────────────
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='font-size: 0.7rem; color: #4A5568; letter-spacing: 3px;
                margin-bottom: 12px;'>USER ACTIVITY BREAKDOWN</div>
    """, unsafe_allow_html=True)

    user_activity = data.get("user_activity", [])
    max_actions = max((u["total_actions"] for u in user_activity), default=1)

    for user in user_activity:
        name = user.get("name", "Unknown")
        total = user.get("total_actions", 0)
        actions = user.get("action_breakdown", {})
        pct = int((total / max_actions) * 100) if max_actions > 0 else 0

        top_actions = sorted(actions.items(), key=lambda x: x[1], reverse=True)[:3]
        top_str = " · ".join([f"{a}: {c}" for a, c in top_actions])

        st.markdown(f"""
        <div style='background: #0F1628; border: 1px solid #1E2D4D;
                    border-radius: 8px; padding: 14px 16px; margin-bottom: 8px;'>
            <div style='display: flex; justify-content: space-between;
                        margin-bottom: 6px;'>
                <span style='color: #E2E8F0; font-size: 0.85rem;
                             font-weight: 600;'>👤 {name}</span>
                <span style='color: #00D4FF; font-size: 0.85rem;
                             font-weight: 700; font-family: monospace;'>
                    {total} actions
                </span>
            </div>
            <div style='background: #1E2D4D; border-radius: 3px;
                        height: 5px; margin-bottom: 6px;'>
                <div style='background: linear-gradient(90deg, #00D4FF, #0088AA);
                            width: {pct}%; height: 5px; border-radius: 3px;'></div>
            </div>
            <div style='color: #4A5568; font-size: 0.7rem;'>{top_str}</div>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# TAB 2 — DOCUMENT RISK SCORING
# ══════════════════════════════════════════════════════════════
with tab2:
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background: #0F1628; border: 1px solid #1E2D4D; border-radius: 8px;
                padding: 14px 16px; margin-bottom: 20px; border-left: 3px solid #F6AD55;'>
        <div style='color: #F6AD55; font-size: 0.75rem; font-weight: 700;
                    letter-spacing: 2px;'>AI-POWERED RISK ASSESSMENT</div>
        <div style='color: #4A5568; font-size: 0.75rem; margin-top: 4px;'>
            Each document is analyzed by Groq AI (Llama 3.3 70B) and scored
            on a 0-100 risk scale based on category, content, and compliance factors.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("⚡ RUN RISK ANALYSIS", use_container_width=False):
        with st.spinner("AI is analyzing all documents... this may take a moment"):
            risk_data = api_get("/analytics/document-risk")

        if not risk_data:
            st.error("Failed to load risk data")
            st.stop()

        summary = risk_data.get("summary", {})
        documents = risk_data.get("documents", [])

        # ── Summary metrics ───────────────────────────────────
        col1, col2, col3, col4, col5 = st.columns(5)
        risk_metrics = [
            (col1, "AVG RISK SCORE", summary.get("avg_risk_score", 0), "#F6AD55"),
            (col2, "CRITICAL", summary.get("critical", 0), "#FF4D6D"),
            (col3, "HIGH", summary.get("high", 0), "#F6AD55"),
            (col4, "MEDIUM", summary.get("medium", 0), "#00D4FF"),
            (col5, "LOW", summary.get("low", 0), "#48BB78"),
        ]
        for col, label, value, color in risk_metrics:
            with col:
                st.markdown(f"""
                <div style='background: #0F1628; border: 1px solid #1E2D4D;
                            border-radius: 10px; padding: 16px;
                            border-top: 3px solid {color}; text-align: center;'>
                    <div style='font-size: 0.6rem; color: #4A5568;
                                letter-spacing: 2px; margin-bottom: 6px;'>{label}</div>
                    <div style='font-size: 1.8rem; font-weight: 700;
                                color: {color}; font-family: monospace;'>{value}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        # ── Risk chart ────────────────────────────────────────
        try:
            import plotly.graph_objects as go
            filenames = [d["filename"][:25] + "..." if len(d["filename"]) > 25
                        else d["filename"] for d in documents]
            scores = [d["risk_score"] for d in documents]
            risk_colors = []
            for d in documents:
                rl = d["risk_level"]
                if rl == "CRITICAL":
                    risk_colors.append("#FF4D6D")
                elif rl == "HIGH":
                    risk_colors.append("#F6AD55")
                elif rl == "MEDIUM":
                    risk_colors.append("#00D4FF")
                else:
                    risk_colors.append("#48BB78")

            fig_risk = go.Figure(data=go.Bar(
                x=scores,
                y=filenames,
                orientation='h',
                marker=dict(color=risk_colors,
                           line=dict(color="#0A0E1A", width=1)),
                hovertemplate="<b>%{y}</b><br>Risk Score: %{x}<extra></extra>"
            ))
            fig_risk.update_layout(
                title=dict(text="Document Risk Scores",
                          font=dict(color="#E2E8F0", size=13), x=0),
                paper_bgcolor="#0F1628",
                plot_bgcolor="#0F1628",
                font=dict(family="JetBrains Mono", color="#E2E8F0", size=9),
                xaxis=dict(
                    gridcolor="#1E2D4D",
                    range=[0, 100],
                    title=dict(text="Risk Score (0-100)",
                              font=dict(size=10, color="#E2E8F0")),
                    tickfont=dict(size=9)
                ),
                yaxis=dict(gridcolor="#1E2D4D", tickfont=dict(size=8)),
                margin=dict(t=40, b=20, l=10, r=10),
                height=max(250, len(documents) * 35)
            )
            st.plotly_chart(fig_risk, use_container_width=True,
                            config={"displayModeBar": False})
        except ImportError:
            pass

        # ── Document risk cards ───────────────────────────────
        st.markdown("""
        <div style='font-size: 0.7rem; color: #4A5568; letter-spacing: 3px;
                    margin: 16px 0 12px 0;'>DETAILED RISK ASSESSMENT</div>
        """, unsafe_allow_html=True)

        risk_level_colors = {
            "CRITICAL": "#FF4D6D",
            "HIGH": "#F6AD55",
            "MEDIUM": "#00D4FF",
            "LOW": "#48BB78"
        }

        for doc in documents:
            rl = doc.get("risk_level", "MEDIUM")
            rs = doc.get("risk_score", 50)
            color = risk_level_colors.get(rl, "#718096")
            factors = doc.get("factors", [])
            factors_html = " · ".join(factors) if factors else ""

            st.markdown(f"""
            <div style='background: #0F1628; border: 1px solid #1E2D4D;
                        border-radius: 10px; padding: 18px; margin-bottom: 10px;
                        border-left: 4px solid {color};'>
                <div style='display: flex; justify-content: space-between;
                            align-items: flex-start; margin-bottom: 10px;'>
                    <div>
                        <div style='color: #E2E8F0; font-size: 0.9rem;
                                    font-weight: 600;'>
                            📄 {doc.get("filename", "")}
                        </div>
                        <div style='color: #4A5568; font-size: 0.7rem; margin-top: 3px;'>
                            {doc.get("category", "").upper()} ·
                            {doc.get("status", "").upper()}
                        </div>
                    </div>
                    <div style='text-align: right;'>
                        <div style='font-size: 1.8rem; font-weight: 700;
                                    color: {color}; font-family: monospace;
                                    line-height: 1;'>{rs}</div>
                        <div style='background: {color}22; color: {color};
                                    font-size: 0.65rem; padding: 2px 8px;
                                    border-radius: 4px; font-weight: 700;
                                    letter-spacing: 2px; margin-top: 4px;
                                    border: 1px solid {color}44;'>{rl}</div>
                    </div>
                </div>
                <div style='background: #1E2D4D; border-radius: 3px;
                            height: 4px; margin-bottom: 10px;'>
                    <div style='background: linear-gradient(90deg, {color}, {color}88);
                                width: {rs}%; height: 4px; border-radius: 3px;'></div>
                </div>
                <div style='color: #E2E8F0; font-size: 0.8rem; margin-bottom: 6px;'>
                    ⚠ {doc.get("primary_risk", "")}
                </div>
                <div style='color: #4A5568; font-size: 0.7rem; margin-bottom: 6px;'>
                    {factors_html}
                </div>
                <div style='color: #48BB78; font-size: 0.75rem;'>
                    ✓ {doc.get("recommendation", "")}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background: #0F1628; border: 1px solid #1E2D4D;
                    border-radius: 10px; padding: 60px; text-align: center;'>
            <div style='font-size: 2.5rem; margin-bottom: 12px;'>⚡</div>
            <div style='color: #E2E8F0; font-size: 0.9rem; font-weight: 600;
                        letter-spacing: 2px; margin-bottom: 8px;'>
                AI RISK ANALYSIS
            </div>
            <div style='color: #4A5568; font-size: 0.8rem;'>
                Click "RUN RISK ANALYSIS" to analyze all documents using Groq AI
            </div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# TAB 3 — AI TASK SUGGESTIONS
# ══════════════════════════════════════════════════════════════
with tab3:
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background: #0F1628; border: 1px solid #1E2D4D; border-radius: 8px;
                padding: 14px 16px; margin-bottom: 20px;
                border-left: 3px solid #48BB78;'>
        <div style='color: #48BB78; font-size: 0.75rem; font-weight: 700;
                    letter-spacing: 2px;'>AI TASK SUGGESTIONS</div>
        <div style='color: #4A5568; font-size: 0.75rem; margin-top: 4px;'>
            Select a processed document and Groq AI will analyze it and suggest
            specific audit tasks you should create based on its content.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Get processed documents
    all_docs = api_get("/documents/") or []
    processed = [d for d in all_docs if d.get("status") == "processed"]

    if not processed:
        st.warning("No processed documents available. Upload and process a PDF first.")
    else:
        doc_options = {f"[{d['id']}] {d['filename']}": d['id']
                      for d in processed}
        selected_label = st.selectbox(
            "SELECT DOCUMENT TO ANALYZE",
            list(doc_options.keys()),
            label_visibility="collapsed"
        )
        selected_doc_id = doc_options[selected_label]

        col_btn, col_info = st.columns([1, 3])
        with col_btn:
            analyze_btn = st.button("⚡ SUGGEST TASKS",
                                    use_container_width=True)
        with col_info:
            st.markdown("""
            <div style='color: #4A5568; font-size: 0.75rem; padding: 8px 0;'>
                AI will read the document and suggest 5 specific audit tasks
            </div>
            """, unsafe_allow_html=True)

        if analyze_btn:
            with st.spinner("AI is analyzing document and generating task suggestions..."):
                import requests as req
                token = st.session_state.get("token", "")
                r = req.post(
                    f"http://localhost:8000/analytics/suggest-tasks/{selected_doc_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )

            if r.ok:
                result = r.json()
                suggestions = result.get("suggestions", [])

                st.markdown(f"""
                <div style='font-size: 0.7rem; color: #4A5568; letter-spacing: 3px;
                            margin: 16px 0 12px 0;'>
                    {len(suggestions)} TASKS SUGGESTED FOR:
                    {result.get("document_name", "")}
                </div>
                """, unsafe_allow_html=True)

                priority_colors = {
                    "critical": "#FF4D6D", "high": "#F6AD55",
                    "medium": "#00D4FF", "low": "#48BB78"
                }

                for i, task in enumerate(suggestions):
                    priority = task.get("priority", "medium")
                    p_color = priority_colors.get(priority, "#718096")
                    days = task.get("suggested_deadline_days", 7)

                    st.markdown(f"""
                    <div style='background: #0F1628; border: 1px solid #1E2D4D;
                                border-radius: 10px; padding: 18px;
                                margin-bottom: 10px;
                                border-left: 4px solid {p_color};'>
                        <div style='display: flex; justify-content: space-between;
                                    align-items: flex-start; margin-bottom: 8px;'>
                            <div style='color: #E2E8F0; font-size: 0.9rem;
                                        font-weight: 600; max-width: 75%;'>
                                {task.get("title", "")}
                            </div>
                            <div style='text-align: right;'>
                                <span style='background: {p_color}22; color: {p_color};
                                             font-size: 0.65rem; padding: 3px 10px;
                                             border-radius: 4px; font-weight: 700;
                                             letter-spacing: 2px;
                                             border: 1px solid {p_color}44;'>
                                    {priority.upper()}
                                </span>
                                <div style='color: #4A5568; font-size: 0.65rem;
                                            margin-top: 4px;'>
                                    ⏰ {days} days deadline
                                </div>
                            </div>
                        </div>
                        <div style='color: #4A5568; font-size: 0.8rem;
                                    line-height: 1.6;'>
                            {task.get("description", "")}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # One-click create button
                    if st.button(f"✚ CREATE THIS TASK",
                                 key=f"create_task_{i}",
                                 use_container_width=False):
                        from datetime import datetime, timedelta
                        deadline = (datetime.now() +
                                   timedelta(days=days)).isoformat()
                        create_result, code = api_post("/tasks/", {
                            "title": task.get("title"),
                            "description": task.get("description"),
                            "priority": priority,
                            "deadline": deadline,
                            "document_id": selected_doc_id
                        })
                        if code == 200:
                            st.success(f"✓ Task created successfully")
                        else:
                            st.error(f"✗ {create_result.get('detail', 'Failed')}")
            else:
                st.error(f"✗ Failed: {r.json().get('detail', 'Unknown error')}")


# ══════════════════════════════════════════════════════════════
# TAB 4 — ANOMALY DETECTION
# ══════════════════════════════════════════════════════════════
with tab4:
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background: #0F1628; border: 1px solid #1E2D4D; border-radius: 8px;
                padding: 14px 16px; margin-bottom: 20px;
                border-left: 3px solid #FF4D6D;'>
        <div style='color: #FF4D6D; font-size: 0.75rem; font-weight: 700;
                    letter-spacing: 2px;'>ANOMALY DETECTION ENGINE</div>
        <div style='color: #4A5568; font-size: 0.75rem; margin-top: 4px;'>
            AI analyzes the last 7 days of audit logs to detect suspicious patterns —
            off-hours access, brute force attempts, mass deletions, and unusual activity.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("⚡ RUN ANOMALY SCAN", use_container_width=False):
        with st.spinner("Scanning audit logs for anomalies..."):
            anomaly_data = api_get("/analytics/anomalies")

        if not anomaly_data:
            st.error("Failed to run anomaly scan")
            st.stop()

        total = anomaly_data.get("total", 0)
        critical = anomaly_data.get("critical", 0)
        high = anomaly_data.get("high", 0)
        medium = anomaly_data.get("medium", 0)
        analyzed = anomaly_data.get("analyzed_logs", 0)

        # Summary metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        scan_metrics = [
            (col1, "LOGS SCANNED", analyzed, "#00D4FF"),
            (col2, "ANOMALIES", total, "#FF4D6D" if total > 0 else "#48BB78"),
            (col3, "CRITICAL", critical, "#FF4D6D"),
            (col4, "HIGH", high, "#F6AD55"),
            (col5, "MEDIUM", medium, "#00D4FF"),
        ]
        for col, label, value, color in scan_metrics:
            with col:
                st.markdown(f"""
                <div style='background: #0F1628; border: 1px solid #1E2D4D;
                            border-radius: 10px; padding: 16px;
                            border-top: 3px solid {color}; text-align: center;'>
                    <div style='font-size: 0.6rem; color: #4A5568;
                                letter-spacing: 2px; margin-bottom: 6px;'>{label}</div>
                    <div style='font-size: 1.8rem; font-weight: 700;
                                color: {color}; font-family: monospace;'>{value}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        anomalies = anomaly_data.get("anomalies", [])

        if not anomalies:
            st.markdown("""
            <div style='background: #0F1628; border: 1px solid #1E2D4D;
                        border-radius: 10px; padding: 40px; text-align: center;
                        border-top: 3px solid #48BB78;'>
                <div style='font-size: 2rem; margin-bottom: 8px;'>✓</div>
                <div style='color: #48BB78; font-size: 0.9rem; font-weight: 700;
                            letter-spacing: 2px;'>NO ANOMALIES DETECTED</div>
                <div style='color: #4A5568; font-size: 0.75rem; margin-top: 6px;'>
                    System activity appears normal for the last 7 days
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style='font-size: 0.7rem; color: #4A5568; letter-spacing: 3px;
                        margin-bottom: 12px;'>
                {total} ANOMALIES DETECTED — LAST 7 DAYS
            </div>
            """, unsafe_allow_html=True)

            severity_colors = {
                "CRITICAL": "#FF4D6D",
                "HIGH": "#F6AD55",
                "MEDIUM": "#00D4FF",
                "LOW": "#48BB78"
            }
            severity_icons = {
                "CRITICAL": "🔴",
                "HIGH": "🟠",
                "MEDIUM": "🟡",
                "LOW": "🟢"
            }

            for anomaly in anomalies:
                severity = anomaly.get("severity", "MEDIUM")
                color = severity_colors.get(severity, "#718096")
                icon = severity_icons.get(severity, "⚪")
                title = anomaly.get("title", "")
                atype = anomaly.get("type", "").replace("_", " ")
                description = anomaly.get("description", "")
                recommendation = anomaly.get("recommendation", "")
                ai_badge = " &nbsp;<b style='color:#9F7AEA;'>[AI]</b>" if anomaly.get("ai_detected") else ""

                details = anomaly.get("details", [])
                det_rows = ""
                for detail in details:
                    row = " · ".join([f"{k}: {v}" for k, v in detail.items()])
                    det_rows += f"<div style='padding:6px 0; border-bottom:1px solid #1E2D4D; font-size:0.75rem; color:#A0AEC0;'>{row}</div>"

                det_block = ""
                if det_rows:
                    det_block = f"<div style='margin-top:10px; padding:10px; background:#0A0E1A; border-radius:6px;'><div style='font-size:0.65rem; color:#4A5568; letter-spacing:2px; margin-bottom:6px;'>DETAILS</div>{det_rows}</div>"

                html = (
                    f"<div style='background:#0F1628; border:1px solid #1E2D4D; border-radius:10px; padding:18px; margin-bottom:10px; border-left:4px solid {color};'>"
                    f"<div style='display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;'>"
                    f"<div><div style='color:#E2E8F0; font-size:0.9rem; font-weight:600;'>{icon} {title}{ai_badge}</div>"
                    f"<div style='color:#4A5568; font-size:0.7rem; margin-top:3px;'>{atype}</div></div>"
                    f"<span style='background:{color}22; color:{color}; font-size:0.65rem; padding:3px 10px; border-radius:4px; font-weight:700; border:1px solid {color}44;'>{severity}</span>"
                    f"</div>"
                    f"<div style='color:#E2E8F0; font-size:0.8rem; line-height:1.6; margin-bottom:8px;'>{description}</div>"
                    f"<div style='color:#48BB78; font-size:0.75rem;'>✓ {recommendation}</div>"
                    f"{det_block}"
                    f"</div>"
                )
                st.markdown(html, unsafe_allow_html=True)



                