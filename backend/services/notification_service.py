# All 4 email notification types:
# 1. notify_task_assigned    — when a task is assigned to a user
# 2. notify_task_overdue     — when a task passes its deadline
# 3. notify_task_status      — when a task status changes
# 4. send_weekly_summary     — weekly compliance report to all admins

from services.email_service import send_email
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# EMAIL TEMPLATES
# ─────────────────────────────────────────────────────────────

BASE_STYLE = """
<style>
  body { margin: 0; padding: 0; background: #F4F5F7; font-family: Arial, sans-serif; }
  .wrapper { max-width: 600px; margin: 30px auto; background: #ffffff; border-radius: 8px;
             overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
  .header { background: #0A0E1A; padding: 28px 32px; text-align: center; }
  .header-logo { font-size: 28px; color: #00D4FF; font-weight: 700; letter-spacing: 4px; }
  .header-sub { font-size: 11px; color: #4A5568; letter-spacing: 3px; margin-top: 4px; }
  .body { padding: 32px; }
  .title { font-size: 20px; font-weight: 700; color: #0A0E1A; margin-bottom: 8px; }
  .subtitle { font-size: 13px; color: #6B778C; margin-bottom: 24px; }
  .card { background: #F8FAFC; border-radius: 6px; padding: 20px; margin-bottom: 20px;
          border-left: 4px solid #00D4FF; }
  .card-row { display: flex; justify-content: space-between; margin-bottom: 10px; }
  .card-label { font-size: 11px; color: #6B778C; font-weight: 700; letter-spacing: 1px; 
                text-transform: uppercase; }
  .card-value { font-size: 13px; color: #0A0E1A; font-weight: 600; }
  .badge { display: inline-block; padding: 3px 10px; border-radius: 4px; font-size: 11px;
           font-weight: 700; letter-spacing: 1px; }
  .badge-cyan { background: #E6FAFE; color: #00829A; }
  .badge-green { background: #E6F4EA; color: #1B6B2F; }
  .badge-amber { background: #FEF3E2; color: #8B5000; }
  .badge-red { background: #FDE8E8; color: #9B1C1C; }
  .btn { display: inline-block; background: #00D4FF; color: #0A0E1A; padding: 12px 28px;
         border-radius: 6px; text-decoration: none; font-weight: 700; font-size: 13px;
         margin-top: 8px; letter-spacing: 1px; }
  .footer { background: #F4F5F7; padding: 20px 32px; text-align: center;
            font-size: 11px; color: #6B778C; border-top: 1px solid #DFE1E6; }
  .divider { height: 1px; background: #DFE1E6; margin: 20px 0; }
  .stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }
  .stat-box { background: #F8FAFC; border-radius: 6px; padding: 16px; text-align: center;
              border: 1px solid #DFE1E6; }
  .stat-num { font-size: 28px; font-weight: 700; color: #0A0E1A; }
  .stat-label { font-size: 11px; color: #6B778C; margin-top: 4px; letter-spacing: 1px; }
</style>
"""


def _priority_badge(priority: str) -> str:
    classes = {
        "critical": "badge-red",
        "high": "badge-amber",
        "medium": "badge-cyan",
        "low": "badge-green"
    }
    cls = classes.get(priority, "badge-cyan")
    return f'<span class="badge {cls}">{priority.upper()}</span>'


def _status_badge(status: str) -> str:
    classes = {
        "pending": "badge-amber",
        "in_progress": "badge-cyan",
        "completed": "badge-green",
        "overdue": "badge-red"
    }
    cls = classes.get(status, "badge-cyan")
    label = status.replace("_", " ").upper()
    return f'<span class="badge {cls}">{label}</span>'


# ─────────────────────────────────────────────────────────────
# 1. TASK ASSIGNED NOTIFICATION
# ─────────────────────────────────────────────────────────────

def notify_task_assigned(
    to_email: str,
    assignee_name: str,
    task_title: str,
    task_description: str,
    priority: str,
    deadline: str,
    assigned_by: str
) -> bool:
    """Sends email when a task is assigned to a user."""

    subject = f"[AuditSys] New Task Assigned: {task_title}"

    html = f"""
    <!DOCTYPE html><html><head>{BASE_STYLE}</head><body>
    <div class="wrapper">
      <div class="header">
        <div class="header-logo">⚡ AUDITSYS</div>
        <div class="header-sub">COMPLIANCE INTELLIGENCE PLATFORM</div>
      </div>
      <div class="body">
        <div class="title">New Task Assigned to You</div>
        <div class="subtitle">Hi {assignee_name}, you have a new audit task requiring your attention.</div>

        <div class="card">
          <div class="card-row">
            <span class="card-label">Task Title</span>
            <span class="card-value">{task_title}</span>
          </div>
          <div class="card-row">
            <span class="card-label">Priority</span>
            <span>{_priority_badge(priority)}</span>
          </div>
          <div class="card-row">
            <span class="card-label">Deadline</span>
            <span class="card-value">{deadline or 'No deadline set'}</span>
          </div>
          <div class="card-row">
            <span class="card-label">Assigned By</span>
            <span class="card-value">{assigned_by}</span>
          </div>
          <div class="divider"></div>
          <div class="card-label">Description</div>
          <div style="font-size:13px; color:#2D3748; margin-top:6px; line-height:1.6;">
            {task_description or 'No description provided.'}
          </div>
        </div>

        <div style="text-align:center;">
          <a href="http://localhost:8501" class="btn">VIEW TASK IN AUDITSYS →</a>
        </div>

        <div class="divider"></div>
        <div style="font-size:12px; color:#6B778C; line-height:1.6;">
          Please log in to AuditSys to acknowledge and begin work on this task.
          Update the status to <b>In Progress</b> when you start.
        </div>
      </div>
      <div class="footer">
        AuditSys Compliance Platform &nbsp;·&nbsp;
        This is an automated notification &nbsp;·&nbsp;
        {datetime.now().strftime('%d %B %Y')}
      </div>
    </div>
    </body></html>
    """
    return send_email(to_email, subject, html)


# ─────────────────────────────────────────────────────────────
# 2. TASK OVERDUE NOTIFICATION
# ─────────────────────────────────────────────────────────────

def notify_task_overdue(
    to_email: str,
    assignee_name: str,
    task_title: str,
    deadline: str,
    days_overdue: int,
    priority: str
) -> bool:
    """Sends email when a task has passed its deadline."""

    subject = f"[AuditSys] ⚠ OVERDUE: {task_title}"

    html = f"""
    <!DOCTYPE html><html><head>{BASE_STYLE}</head><body>
    <div class="wrapper">
      <div class="header" style="background:#7B0000;">
        <div class="header-logo" style="color:#FF6B6B;">⚠ OVERDUE ALERT</div>
        <div class="header-sub" style="color:#FCA5A5;">AUDITSYS COMPLIANCE PLATFORM</div>
      </div>
      <div class="body">
        <div class="title" style="color:#9B1C1C;">Task is Overdue</div>
        <div class="subtitle">
          Hi {assignee_name}, the following task has passed its deadline and requires immediate attention.
        </div>

        <div class="card" style="border-left-color:#FF4D6D; background:#FFF5F5;">
          <div class="card-row">
            <span class="card-label">Task</span>
            <span class="card-value" style="color:#9B1C1C;">{task_title}</span>
          </div>
          <div class="card-row">
            <span class="card-label">Priority</span>
            <span>{_priority_badge(priority)}</span>
          </div>
          <div class="card-row">
            <span class="card-label">Deadline Was</span>
            <span class="card-value" style="color:#9B1C1C;">{deadline}</span>
          </div>
          <div class="card-row">
            <span class="card-label">Days Overdue</span>
            <span class="badge badge-red">{days_overdue} DAY{'S' if days_overdue != 1 else ''}</span>
          </div>
        </div>

        <div style="background:#FFF5F5; border:1px solid #FCA5A5; border-radius:6px;
                    padding:16px; margin-bottom:20px; font-size:13px; color:#7B0000; line-height:1.6;">
          <b>Action Required:</b> Please complete this task immediately or contact your audit manager
          to request a deadline extension. Overdue tasks impact your team's compliance score.
        </div>

        <div style="text-align:center;">
          <a href="http://localhost:8501" class="btn" 
             style="background:#FF4D6D; color:white;">RESOLVE NOW →</a>
        </div>
      </div>
      <div class="footer">
        AuditSys Compliance Platform &nbsp;·&nbsp; Automated Overdue Alert &nbsp;·&nbsp;
        {datetime.now().strftime('%d %B %Y')}
      </div>
    </div>
    </body></html>
    """
    return send_email(to_email, subject, html)


# ─────────────────────────────────────────────────────────────
# 3. TASK STATUS CHANGED NOTIFICATION
# ─────────────────────────────────────────────────────────────

def notify_task_status_changed(
    to_email: str,
    recipient_name: str,
    task_title: str,
    old_status: str,
    new_status: str,
    changed_by: str
) -> bool:
    """Sends email when a task's status is updated."""

    subject = f"[AuditSys] Task Update: {task_title} → {new_status.replace('_', ' ').title()}"

    status_messages = {
        "in_progress": "Work has started on this task.",
        "completed": "This task has been marked as complete. Great work!",
        "pending": "This task has been reset to pending status.",
        "overdue": "This task has been flagged as overdue.",
    }
    message = status_messages.get(new_status, "The task status has been updated.")

    html = f"""
    <!DOCTYPE html><html><head>{BASE_STYLE}</head><body>
    <div class="wrapper">
      <div class="header">
        <div class="header-logo">⚡ AUDITSYS</div>
        <div class="header-sub">COMPLIANCE INTELLIGENCE PLATFORM</div>
      </div>
      <div class="body">
        <div class="title">Task Status Updated</div>
        <div class="subtitle">Hi {recipient_name}, a task you are involved in has been updated.</div>

        <div class="card">
          <div class="card-row">
            <span class="card-label">Task</span>
            <span class="card-value">{task_title}</span>
          </div>
          <div class="card-row">
            <span class="card-label">Previous Status</span>
            <span>{_status_badge(old_status)}</span>
          </div>
          <div class="card-row">
            <span class="card-label">New Status</span>
            <span>{_status_badge(new_status)}</span>
          </div>
          <div class="card-row">
            <span class="card-label">Updated By</span>
            <span class="card-value">{changed_by}</span>
          </div>
          <div class="card-row">
            <span class="card-label">Updated At</span>
            <span class="card-value">{datetime.now().strftime('%d %b %Y, %H:%M')}</span>
          </div>
        </div>

        <div style="font-size:13px; color:#2D3748; line-height:1.6; margin-bottom:20px;">
          {message}
        </div>

        <div style="text-align:center;">
          <a href="http://localhost:8501" class="btn">VIEW IN AUDITSYS →</a>
        </div>
      </div>
      <div class="footer">
        AuditSys Compliance Platform &nbsp;·&nbsp; Automated Status Notification &nbsp;·&nbsp;
        {datetime.now().strftime('%d %B %Y')}
      </div>
    </div>
    </body></html>
    """
    return send_email(to_email, subject, html)

# ─────────────────────────────────────────────────────────────
# 4. WEEKLY COMPLIANCE SUMMARY
# ─────────────────────────────────────────────────────────────

def send_weekly_summary(
    to_email: str,
    recipient_name: str,
    total_docs: int,
    processed_docs: int,
    total_tasks: int,
    completed_tasks: int,
    overdue_tasks: int,
    pending_tasks: int,
    compliance_score: int,
    recent_actions: list
) -> bool:
    """Sends weekly compliance summary to admins."""

    subject = f"[AuditSys] Weekly Compliance Summary — {datetime.now().strftime('%d %b %Y')}"

    # Score color
    if compliance_score >= 80:
        score_color = "#1B6B2F"
        score_bg = "#E6F4EA"
        score_label = "COMPLIANT"
    elif compliance_score >= 60:
        score_color = "#8B5000"
        score_bg = "#FEF3E2"
        score_label = "AT RISK"
    else:
        score_color = "#9B1C1C"
        score_bg = "#FDE8E8"
        score_label = "NON-COMPLIANT"

    # Build recent actions list
    actions_html = ""
    for action in recent_actions[:5]:
        actions_html += f"""
        <div style="padding:8px 0; border-bottom:1px solid #DFE1E6; font-size:12px;
                    color:#2D3748; display:flex; justify-content:space-between;">
          <span>· {action.get('action', '')} — user:{action.get('user_id', 'sys')}</span>
          <span style="color:#6B778C;">{str(action.get('created_at', ''))[:10]}</span>
        </div>
        """

    html = f"""
    <!DOCTYPE html><html><head>{BASE_STYLE}</head><body>
    <div class="wrapper">
      <div class="header">
        <div class="header-logo">⚡ AUDITSYS</div>
        <div class="header-sub">WEEKLY COMPLIANCE SUMMARY</div>
      </div>
      <div class="body">
        <div class="title">Weekly Compliance Report</div>
        <div class="subtitle">
          Hi {recipient_name}, here is your compliance summary for the week ending
          {datetime.now().strftime('%d %B %Y')}.
        </div>

        <!-- Compliance Score -->
        <div style="background:{score_bg}; border-radius:8px; padding:20px; text-align:center;
                    margin-bottom:20px; border:1px solid {score_color}33;">
          <div style="font-size:11px; color:{score_color}; font-weight:700; 
                      letter-spacing:2px; margin-bottom:4px;">COMPLIANCE SCORE</div>
          <div style="font-size:48px; font-weight:700; color:{score_color}; 
                      line-height:1;">{compliance_score}%</div>
          <div style="font-size:12px; color:{score_color}; font-weight:700; 
                      letter-spacing:3px; margin-top:4px;">{score_label}</div>
        </div>

        <!-- Stats Grid -->
        <div class="stat-grid">
          <div class="stat-box">
            <div class="stat-num" style="color:#00829A;">{total_docs}</div>
            <div class="stat-label">TOTAL DOCUMENTS</div>
          </div>
          <div class="stat-box">
            <div class="stat-num" style="color:#1B6B2F;">{processed_docs}</div>
            <div class="stat-label">PROCESSED</div>
          </div>
          <div class="stat-box">
            <div class="stat-num" style="color:#1B6B2F;">{completed_tasks}</div>
            <div class="stat-label">TASKS COMPLETED</div>
          </div>
          <div class="stat-box">
            <div class="stat-num" style="color:#9B1C1C;">{overdue_tasks}</div>
            <div class="stat-label">TASKS OVERDUE</div>
          </div>
        </div>

        <!-- Task Breakdown -->
        <div class="card">
          <div class="card-label" style="margin-bottom:12px;">TASK BREAKDOWN</div>
          <div class="card-row">
            <span style="font-size:13px; color:#2D3748;">Total Tasks</span>
            <span class="card-value">{total_tasks}</span>
          </div>
          <div class="card-row">
            <span style="font-size:13px; color:#2D3748;">Completed</span>
            <span class="badge badge-green">{completed_tasks}</span>
          </div>
          <div class="card-row">
            <span style="font-size:13px; color:#2D3748;">In Progress</span>
            <span class="badge badge-cyan">{total_tasks - completed_tasks - overdue_tasks - pending_tasks}</span>
          </div>
          <div class="card-row">
            <span style="font-size:13px; color:#2D3748;">Pending</span>
            <span class="badge badge-amber">{pending_tasks}</span>
          </div>
          <div class="card-row">
            <span style="font-size:13px; color:#2D3748;">Overdue</span>
            <span class="badge badge-red">{overdue_tasks}</span>
          </div>
        </div>

        <!-- Recent Activity -->
        <div style="font-size:11px; color:#6B778C; font-weight:700; 
                    letter-spacing:2px; margin-bottom:8px;">RECENT ACTIVITY</div>
        <div style="background:#F8FAFC; border-radius:6px; padding:12px 16px;
                    border:1px solid #DFE1E6; margin-bottom:20px;">
          {actions_html if actions_html else '<div style="color:#6B778C; font-size:12px;">No activity this week</div>'}
        </div>

        <div style="text-align:center;">
          <a href="http://localhost:8501" class="btn">OPEN DASHBOARD →</a>
        </div>
      </div>
      <div class="footer">
        AuditSys Compliance Platform &nbsp;·&nbsp; Automated Weekly Report &nbsp;·&nbsp;
        {datetime.now().strftime('%d %B %Y')}
        <br><br>
        You are receiving this because you are an admin on AuditSys.
      </div>
    </div>
    </body></html>
    """
    return send_email(to_email, subject, html)
