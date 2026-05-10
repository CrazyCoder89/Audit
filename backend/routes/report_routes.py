# One-click compliance report generator.
# GET /reports/compliance — generates and returns a full PDF compliance report
# with current stats, task breakdown, document status, risk overview, and audit trail.

import io
import json
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.document import Document, DocumentStatus, DocumentCategory
from models.task import Task, TaskStatus, TaskPriority
from models.audit_log import AuditLog
from auth.dependencies import get_current_user
from datetime import datetime, timezone

router = APIRouter(prefix="/reports", tags=["Reports"])


def calculate_compliance_score(db):
    documents = db.query(Document).filter(Document.is_active == True).all()
    tasks = db.query(Task).all()
    total_docs = len(documents)
    processed_docs = len([d for d in documents if d.status == DocumentStatus.processed])
    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.status == TaskStatus.completed])
    overdue_tasks = len([t for t in tasks if t.status == TaskStatus.overdue])
    doc_score = (processed_docs / total_docs * 40) if total_docs > 0 else 0
    task_score = (completed_tasks / total_tasks * 40) if total_tasks > 0 else 0
    overdue_penalty = min(overdue_tasks * 5, 20)
    return max(0, min(100, int(doc_score + task_score + 20 - overdue_penalty)))


@router.get("/compliance")
def generate_compliance_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                     Table, TableStyle, HRFlowable, PageBreak)
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

    # ── Fetch all data ────────────────────────────────────────────────────
    documents = db.query(Document).filter(Document.is_active == True).all()
    tasks = db.query(Task).all()
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(20).all()
    users = db.query(User).filter(User.is_active == True).all()

    total_docs = len(documents)
    processed_docs = len([d for d in documents if d.status == DocumentStatus.processed])
    pending_docs = len([d for d in documents if d.status == DocumentStatus.pending])
    failed_docs = len([d for d in documents if d.status == DocumentStatus.failed])

    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.status == TaskStatus.completed])
    in_progress_tasks = len([t for t in tasks if t.status == TaskStatus.in_progress])
    pending_tasks = len([t for t in tasks if t.status == TaskStatus.pending])
    overdue_tasks = len([t for t in tasks if t.status == TaskStatus.overdue])
    critical_tasks = len([t for t in tasks if t.priority == TaskPriority.critical])

    compliance_score = calculate_compliance_score(db)
    completion_rate = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0
    processing_rate = int((processed_docs / total_docs * 100)) if total_docs > 0 else 0

    if compliance_score >= 80:
        score_label = "COMPLIANT"
        score_color = colors.HexColor('#1B6B2F')
        score_bg = colors.HexColor('#E6F4EA')
    elif compliance_score >= 60:
        score_label = "AT RISK"
        score_color = colors.HexColor('#8B5000')
        score_bg = colors.HexColor('#FEF3E2')
    else:
        score_label = "NON-COMPLIANT"
        score_color = colors.HexColor('#9B1C1C')
        score_bg = colors.HexColor('#FDE8E8')

    # ── Colors & Styles ───────────────────────────────────────────────────
    NAVY = colors.HexColor('#0A0E1A')
    CYAN = colors.HexColor('#00B8D9')
    GREEN = colors.HexColor('#36B37E')
    AMBER = colors.HexColor('#FF8B00')
    RED = colors.HexColor('#DE350B')
    MUTED = colors.HexColor('#6B778C')
    BORDER = colors.HexColor('#DFE1E6')
    OFFWHITE = colors.HexColor('#F4F5F7')
    WHITE = colors.white

    def ps(name, size, bold=False, color=None, align=TA_LEFT,
           before=0, after=6, leading=None):
        return ParagraphStyle(
            name, fontSize=size,
            fontName='Helvetica-Bold' if bold else 'Helvetica',
            textColor=color or colors.HexColor('#2D3748'),
            alignment=align, spaceBefore=before, spaceAfter=after,
            leading=leading or size * 1.4
        )

    def rule(c=BORDER, t=0.5):
        return HRFlowable(width="100%", thickness=t, color=c,
                          spaceBefore=4, spaceAfter=8)

    def section(num, title):
        return [
            Paragraph(num, ps('sn', 8, bold=True, color=CYAN, before=16, after=1)),
            Paragraph(title, ps('st', 15, bold=True, color=NAVY, before=2, after=6)),
            rule(BORDER, 0.5)
        ]

    def tbl(data, widths, hbg=NAVY):
        t = Table(data, colWidths=widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), hbg),
            ('TEXTCOLOR', (0,0), (-1,0), WHITE),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [OFFWHITE, WHITE]),
            ('GRID', (0,0), (-1,-1), 0.3, BORDER),
            ('PADDING', (0,0), (-1,-1), 7),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        return t

    # ── Build PDF ─────────────────────────────────────────────────────────
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    story = []

    # Cover header
    cover = Table([[
        Paragraph("⚡ AUDITSYS", ps('cl', 22, bold=True, color=WHITE, align=TA_CENTER)),
        Paragraph("COMPLIANCE REPORT", ps('ct', 13, color=colors.HexColor('#A0AEC0'), align=TA_CENTER)),
        Paragraph(datetime.now().strftime('%d %B %Y'), ps('cd', 10, color=MUTED, align=TA_CENTER)),
    ]], colWidths=[17*cm])
    cover.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), NAVY),
        ('PADDING', (0,0), (-1,-1), 20),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(cover)
    story.append(Spacer(1, 0.5*cm))

    # Meta info
    meta = [
        ["Generated By", current_user.full_name, "Role", current_user.role.upper()],
        ["Generated At", datetime.now().strftime('%d %b %Y, %H:%M'), "Total Users", str(len(users))],
    ]
    mt = Table(meta, colWidths=[3.5*cm, 6*cm, 3.5*cm, 4*cm])
    mt.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
        ('FONTNAME', (3,0), (3,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (0,-1), MUTED),
        ('TEXTCOLOR', (2,0), (2,-1), MUTED),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [OFFWHITE, WHITE]),
        ('GRID', (0,0), (-1,-1), 0.3, BORDER),
        ('PADDING', (0,0), (-1,-1), 7),
    ]))
    story.append(mt)
    story.append(Spacer(1, 0.4*cm))

    # ── Section 1: Compliance Score ───────────────────────────────────────
    story += section("01", "Compliance Score")

    score_tbl = Table([[
        Paragraph(f"{compliance_score}%",
                  ps('sc', 40, bold=True, color=score_color, align=TA_CENTER)),
        Paragraph(score_label,
                  ps('sl', 14, bold=True, color=score_color, align=TA_CENTER)),
    ]], colWidths=[8.5*cm, 8.5*cm])
    score_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), score_bg),
        ('PADDING', (0,0), (-1,-1), 20),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 1, score_color),
        ('ROUNDEDCORNERS', [6]),
    ]))
    story.append(score_tbl)
    story.append(Spacer(1, 0.3*cm))

    # Score breakdown
    breakdown = [
        ["Component", "Score", "Max", "Notes"],
        ["Document Processing", f"{int(processing_rate * 0.4)}pts",
         "40pts", f"{processed_docs}/{total_docs} docs processed ({processing_rate}%)"],
        ["Task Completion", f"{int(completion_rate * 0.4)}pts",
         "40pts", f"{completed_tasks}/{total_tasks} tasks completed ({completion_rate}%)"],
        ["Base Score", "20pts", "20pts", "System baseline"],
        ["Overdue Penalty", f"-{min(overdue_tasks * 5, 20)}pts",
         "max -20", f"{overdue_tasks} overdue tasks × 5pts each"],
        ["TOTAL", f"{compliance_score}pts", "100pts", score_label],
    ]
    story.append(tbl(breakdown, [5*cm, 2.5*cm, 2.5*cm, 7*cm]))
    story.append(Spacer(1, 0.4*cm))

    # ── Section 2: Document Summary ───────────────────────────────────────
    story += section("02", "Document Summary")

    doc_stats = [
        ["Metric", "Count", "Percentage"],
        ["Total Documents", str(total_docs), "100%"],
        ["Processed", str(processed_docs), f"{processing_rate}%"],
        ["Pending", str(pending_docs), f"{int(pending_docs/total_docs*100) if total_docs else 0}%"],
        ["Failed", str(failed_docs), f"{int(failed_docs/total_docs*100) if total_docs else 0}%"],
    ]
    story.append(tbl(doc_stats, [8*cm, 4*cm, 5*cm]))
    story.append(Spacer(1, 0.3*cm))

    # Category breakdown
    cat_counts = {}
    for d in documents:
        c = d.category.value if hasattr(d.category, 'value') else str(d.category)
        cat_counts[c] = cat_counts.get(c, 0) + 1

    cat_data = [["Category", "Count", "Percentage"]]
    for cat, count in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True):
        pct = int(count / total_docs * 100) if total_docs > 0 else 0
        cat_data.append([cat.upper(), str(count), f"{pct}%"])
    story.append(tbl(cat_data, [8*cm, 4*cm, 5*cm]))
    story.append(Spacer(1, 0.4*cm))

    # ── Section 3: Task Summary ───────────────────────────────────────────
    story += section("03", "Task Summary")

    task_stats = [
        ["Status", "Count", "Percentage"],
        ["Completed", str(completed_tasks), f"{completion_rate}%"],
        ["In Progress", str(in_progress_tasks),
         f"{int(in_progress_tasks/total_tasks*100) if total_tasks else 0}%"],
        ["Pending", str(pending_tasks),
         f"{int(pending_tasks/total_tasks*100) if total_tasks else 0}%"],
        ["Overdue", str(overdue_tasks),
         f"{int(overdue_tasks/total_tasks*100) if total_tasks else 0}%"],
        ["TOTAL", str(total_tasks), "100%"],
    ]
    story.append(tbl(task_stats, [8*cm, 4*cm, 5*cm]))
    story.append(Spacer(1, 0.3*cm))

    # Overdue tasks detail
    overdue_list = [t for t in tasks if t.status == TaskStatus.overdue]
    if overdue_list:
        story.append(Paragraph("Overdue Tasks Requiring Immediate Attention",
                               ps('ot', 10, bold=True, color=RED, before=8)))
        od_data = [["Task Title", "Priority", "Deadline", "Assigned To"]]
        for t in overdue_list:
            deadline_str = t.deadline.strftime('%d %b %Y') if t.deadline else "—"
            assignee = db.query(User).filter(User.id == t.assigned_to).first()
            assignee_name = assignee.full_name if assignee else "Unassigned"
            priority_str = t.priority.value if hasattr(t.priority, 'value') else str(t.priority)
            od_data.append([t.title[:40], priority_str.upper(), deadline_str, assignee_name])
        ot = Table(od_data, colWidths=[6*cm, 3*cm, 3.5*cm, 4.5*cm])
        ot.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), RED),
            ('TEXTCOLOR', (0,0), (-1,0), WHITE),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#FFF5F5'), WHITE]),
            ('GRID', (0,0), (-1,-1), 0.3, BORDER),
            ('PADDING', (0,0), (-1,-1), 7),
        ]))
        story.append(ot)

    story.append(PageBreak())

    # ── Section 4: Critical & High Priority Tasks ─────────────────────────
    story += section("04", "Critical & High Priority Tasks")

    critical_list = [t for t in tasks
                     if t.priority in [TaskPriority.critical, TaskPriority.high]
                     and t.status != TaskStatus.completed]
    if critical_list:
        ch_data = [["Title", "Priority", "Status", "Deadline"]]
        for t in critical_list:
            deadline_str = t.deadline.strftime('%d %b %Y') if t.deadline else "No deadline"
            priority_str = t.priority.value if hasattr(t.priority, 'value') else str(t.priority)
            status_str = t.status.value if hasattr(t.status, 'value') else str(t.status)
            ch_data.append([
                t.title[:45],
                priority_str.upper(),
                status_str.upper(),
                deadline_str
            ])
        story.append(tbl(ch_data, [7*cm, 3*cm, 3*cm, 4*cm]))
    else:
        story.append(Paragraph("No critical or high priority tasks pending.",
                               ps('np', 10, color=GREEN)))
    story.append(Spacer(1, 0.4*cm))

    # ── Section 5: Recent Audit Activity ─────────────────────────────────
    story += section("05", "Recent Audit Activity")

    action_colors_map = {
        "user.login": "✓", "document.upload": "↑",
        "document.ask": "◈", "task.create": "✚",
        "task.update": "↻", "document.delete": "✕",
        "user.login_failed": "✗"
    }

    log_data = [["#", "Action", "User ID", "Resource", "Timestamp"]]
    for i, log in enumerate(logs[:15], 1):
        resource = f"{log.resource_type or ''}#{log.resource_id or ''}" \
                   if log.resource_type else "—"
        timestamp = log.created_at.strftime('%d %b %Y %H:%M') if log.created_at else "—"
        log_data.append([
            str(i),
            log.action or "—",
            str(log.user_id or "sys"),
            resource,
            timestamp
        ])
    story.append(tbl(log_data, [1*cm, 5*cm, 2.5*cm, 3.5*cm, 5*cm]))
    story.append(Spacer(1, 0.4*cm))

    # ── Section 6: Recommendations ────────────────────────────────────────
    story += section("06", "Recommendations")

    recommendations = []
    if overdue_tasks > 0:
        recommendations.append(
            f"URGENT: {overdue_tasks} task(s) are overdue. Assign resources immediately to resolve."
        )
    if failed_docs > 0:
        recommendations.append(
            f"ACTION: {failed_docs} document(s) failed processing. Re-upload to enable AI analysis."
        )
    if pending_docs > 0:
        recommendations.append(
            f"INFO: {pending_docs} document(s) are still pending processing."
        )
    if compliance_score < 60:
        recommendations.append(
            "CRITICAL: Compliance score is below 60%. Immediate management review required."
        )
    elif compliance_score < 80:
        recommendations.append(
            "WARNING: Compliance score is below 80%. Focus on completing overdue tasks."
        )
    if critical_tasks > 0:
        recommendations.append(
            f"HIGH PRIORITY: {critical_tasks} critical task(s) require immediate attention."
        )
    if not recommendations:
        recommendations.append(
            "System is operating within compliance parameters. Continue monitoring."
        )

    rec_data = [["#", "Recommendation"]]
    for i, rec in enumerate(recommendations, 1):
        rec_data.append([str(i), rec])
    rt = Table(rec_data, colWidths=[1*cm, 16*cm])
    rt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#FFF8E6'), WHITE]),
        ('GRID', (0,0), (-1,-1), 0.3, BORDER),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEADING', (0,0), (-1,-1), 14),
    ]))
    story.append(rt)
    story.append(Spacer(1, 0.5*cm))

    # Footer
    story.append(rule(NAVY, 1))
    story.append(Paragraph(
        f"AuditSys Compliance Report  ·  Generated by {current_user.full_name}  ·  "
        f"{datetime.now().strftime('%d %B %Y %H:%M')}  ·  CONFIDENTIAL",
        ps('ft', 7.5, color=MUTED, align=TA_CENTER)
    ))

    doc.build(story)
    buffer.seek(0)

    filename = f"compliance_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )