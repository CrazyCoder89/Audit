# Weekly compliance summary scheduler.
# Runs every Monday at 8:00 AM and sends summary email to all admins.
# Start this alongside uvicorn in a separate thread.

import schedule
import time
import threading
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from models.user import User
from models.document import Document, DocumentStatus
from models.task import Task, TaskStatus
from models.audit_log import AuditLog
from services.notification_service import send_weekly_summary


def calculate_compliance_score(db):
    """Same algorithm as the dashboard."""
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


def send_weekly_reports():
    """Fetches data and sends weekly summary to all admins."""
    print("[WEEKLY REPORT] Sending weekly compliance summaries...")
    db = SessionLocal()

    try:
        # Get all admin users
        admins = db.query(User).filter(
            User.role == "admin",
            User.is_active == True
        ).all()

        if not admins:
            print("[WEEKLY REPORT] No admin users found.")
            return

        # Fetch stats
        documents = db.query(Document).filter(Document.is_active == True).all()
        tasks = db.query(Task).all()
        recent_logs = db.query(AuditLog).order_by(
            AuditLog.created_at.desc()
        ).limit(10).all()

        total_docs = len(documents)
        processed_docs = len([d for d in documents if d.status == DocumentStatus.processed])
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == TaskStatus.completed])
        overdue_tasks = len([t for t in tasks if t.status == TaskStatus.overdue])
        pending_tasks = len([t for t in tasks if t.status == TaskStatus.pending])
        compliance_score = calculate_compliance_score(db)

        logs_data = [
            {"action": log.action, "user_id": log.user_id,
             "created_at": log.created_at}
            for log in recent_logs
        ]

        # Send to each admin
        for admin in admins:
            success = send_weekly_summary(
                to_email=admin.email,
                recipient_name=admin.full_name,
                total_docs=total_docs,
                processed_docs=processed_docs,
                total_tasks=total_tasks,
                completed_tasks=completed_tasks,
                overdue_tasks=overdue_tasks,
                pending_tasks=pending_tasks,
                compliance_score=compliance_score,
                recent_actions=logs_data
            )
            if success:
                print(f"[WEEKLY REPORT] Sent to {admin.email}")
            else:
                print(f"[WEEKLY REPORT] Failed for {admin.email}")

    except Exception as e:
        print(f"[WEEKLY REPORT ERROR] {e}")
    finally:
        db.close()


def run_scheduler():
    """Runs the scheduler in a background thread."""
    # Send every Monday at 08:00
    schedule.every().monday.at("08:00").do(send_weekly_reports)

    # Uncomment below to test immediately on startup:
    # send_weekly_reports()

    while True:
        schedule.run_pending()
        time.sleep(60)


def start_scheduler():
    """Starts the scheduler in a daemon thread."""
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()
    print("[SCHEDULER] Weekly report scheduler started — runs every Monday at 08:00")


    