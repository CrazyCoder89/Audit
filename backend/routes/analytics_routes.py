# Analytics endpoints:
# GET /analytics/user-activity     — user activity heatmap data
# GET /analytics/document-risk     — AI risk scoring for documents
# GET /analytics/overview          — combined analytics data

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from database import get_db
from models.user import User
from models.audit_log import AuditLog
from models.document import Document, DocumentStatus
from models.task import Task, TaskStatus
from auth.dependencies import get_current_user
from datetime import datetime, timedelta, timezone
from groq import Groq
import os
from dotenv import load_dotenv


load_dotenv()
def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in .env")
    return Groq(api_key=api_key)



router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/test-env")
def test_env(current_user: User = Depends(get_current_user)):
    import os
    key = os.getenv("GROQ_API_KEY")
    return {
        "key_found": key is not None,
        "key_length": len(key) if key else 0,
        "key_preview": key[:10] + "..." if key else "NOT FOUND"
    }

# ─────────────────────────────────────────────────────────────
# USER ACTIVITY HEATMAP
# ─────────────────────────────────────────────────────────────

@router.get("/user-activity")
def get_user_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "auditor"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get all logs from last 30 days
    since = datetime.now(timezone.utc) - timedelta(days=30)
    logs = db.query(AuditLog).filter(AuditLog.created_at >= since).all()

    users = db.query(User).filter(User.is_active == True).all()
    user_map = {u.id: u.full_name for u in users}

    # ── Per-user action counts ────────────────────────────────
    user_counts = {}
    for log in logs:
        uid = log.user_id
        if uid not in user_counts:
            user_counts[uid] = {
                "name": user_map.get(uid, f"User#{uid}"),
                "total": 0,
                "actions": {}
            }
        user_counts[uid]["total"] += 1
        action = log.action or "unknown"
        user_counts[uid]["actions"][action] = \
            user_counts[uid]["actions"].get(action, 0) + 1

    # ── Hourly activity heatmap (hour 0-23 x day 0-6) ────────
    # day 0 = Monday, day 6 = Sunday
    heatmap = [[0] * 24 for _ in range(7)]
    for log in logs:
        if log.created_at:
            dt = log.created_at
            day = dt.weekday()   # 0=Mon, 6=Sun
            hour = dt.hour
            heatmap[day][hour] += 1

    # ── Daily activity for last 30 days ──────────────────────
    daily = {}
    for log in logs:
        if log.created_at:
            date_str = log.created_at.strftime('%Y-%m-%d')
            daily[date_str] = daily.get(date_str, 0) + 1

    # Sort by date
    daily_sorted = dict(sorted(daily.items()))

    # ── Most active user ─────────────────────────────────────
    most_active = None
    max_count = 0
    for uid, data in user_counts.items():
        if data["total"] > max_count:
            max_count = data["total"]
            most_active = {"id": uid, "name": data["name"], "count": data["total"]}

    # ── Peak hour ────────────────────────────────────────────
    hour_totals = [0] * 24
    for day_row in heatmap:
        for h, count in enumerate(day_row):
            hour_totals[h] += count
    peak_hour = hour_totals.index(max(hour_totals)) if any(hour_totals) else 9

    return {
        "user_activity": [
            {
                "user_id": uid,
                "name": data["name"],
                "total_actions": data["total"],
                "action_breakdown": data["actions"]
            }
            for uid, data in sorted(
                user_counts.items(),
                key=lambda x: x[1]["total"],
                reverse=True
            )
        ],
        "heatmap": heatmap,
        "daily_activity": daily_sorted,
        "most_active_user": most_active,
        "peak_hour": peak_hour,
        "peak_hour_label": f"{peak_hour:02d}:00 - {peak_hour+1:02d}:00",
        "total_actions_30d": len(logs),
        "days_analyzed": 30
    }


# ─────────────────────────────────────────────────────────────
# DOCUMENT RISK SCORING
# ─────────────────────────────────────────────────────────────

def score_document_risk(filename: str, category: str, file_size: int,
                         status: str, has_tasks: bool) -> dict:
    """
    AI-powered document risk scoring using Groq.
    Returns risk level, score (0-100), and reasoning.
    """
    prompt = f"""You are a compliance risk analyst. Analyze this document and provide a risk assessment.

Document Details:
- Filename: {filename}
- Category: {category}
- File Size: {round(file_size / 1024, 1)} KB
- Processing Status: {status}
- Has Audit Tasks: {has_tasks}

Respond ONLY with a valid JSON object in this exact format with no other text:
{{
  "risk_level": "LOW" or "MEDIUM" or "HIGH" or "CRITICAL",
  "risk_score": <integer 0-100>,
  "primary_risk": "<one sentence describing the main risk>",
  "factors": ["<factor 1>", "<factor 2>", "<factor 3>"],
  "recommendation": "<one actionable recommendation>"
}}

Risk scoring guide:
- CRITICAL (80-100): Legal documents, contracts, financial reports with high liability
- HIGH (60-79): Compliance documents, regulatory filings, sensitive HR data
- MEDIUM (40-59): Standard operational documents, general compliance materials
- LOW (0-39): Informational documents, processed and reviewed materials"""

    try:
        client = get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=300
        )
        content = response.choices[0].message.content
        # Clean response
        content = content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        return json.loads(content)
    except Exception as e:
        print(f"[RISK SCORING ERROR] {e}")
        # Fallback scoring based on category
        fallback = {
            "legal": {"risk_level": "HIGH", "risk_score": 70},
            "financial": {"risk_level": "HIGH", "risk_score": 65},
            "compliance": {"risk_level": "MEDIUM", "risk_score": 55},
            "hr": {"risk_level": "MEDIUM", "risk_score": 50},
            "unknown": {"risk_level": "LOW", "risk_score": 30},
        }
        base = fallback.get(category, {"risk_level": "MEDIUM", "risk_score": 50})
        return {
            "risk_level": base["risk_level"],
            "risk_score": base["risk_score"],
            "primary_risk": f"{category.upper()} document requires review",
            "factors": ["Category-based assessment", "Manual review recommended"],
            "recommendation": "Review document content manually"
        }


@router.get("/document-risk")
def get_document_risk_scores(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "auditor"]:
        raise HTTPException(status_code=403, detail="Access denied")

    documents = db.query(Document).filter(Document.is_active == True).all()

    results = []
    for doc in documents:
        # Check if document has associated tasks
        has_tasks = db.query(Task).filter(Task.document_id == doc.id).first() is not None

        category = doc.category.value if hasattr(doc.category, 'value') else str(doc.category)
        status = doc.status.value if hasattr(doc.status, 'value') else str(doc.status)

        risk = score_document_risk(
            filename=doc.filename,
            category=category,
            file_size=doc.file_size,
            status=status,
            has_tasks=has_tasks
        )

        results.append({
            "document_id": doc.id,
            "filename": doc.filename,
            "category": category,
            "status": status,
            "file_size": doc.file_size,
            "risk_level": risk.get("risk_level", "MEDIUM"),
            "risk_score": risk.get("risk_score", 50),
            "primary_risk": risk.get("primary_risk", ""),
            "factors": risk.get("factors", []),
            "recommendation": risk.get("recommendation", ""),
            "uploaded_at": doc.created_at.isoformat() if doc.created_at else ""
        })

    # Sort by risk score descending
    results.sort(key=lambda x: x["risk_score"], reverse=True)

    return {
        "documents": results,
        "summary": {
            "total": len(results),
            "critical": len([r for r in results if r["risk_level"] == "CRITICAL"]),
            "high": len([r for r in results if r["risk_level"] == "HIGH"]),
            "medium": len([r for r in results if r["risk_level"] == "MEDIUM"]),
            "low": len([r for r in results if r["risk_level"] == "LOW"]),
            "avg_risk_score": int(sum(r["risk_score"] for r in results) / len(results)) if results else 0
        }
    }

# ─────────────────────────────────────────────────────────────
# AI TASK SUGGESTIONS
# ─────────────────────────────────────────────────────────────

@router.post("/suggest-tasks/{document_id}")
def suggest_tasks_for_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Uses Groq AI to analyze a processed document and suggest
    audit tasks that should be created based on its content.
    """
    if current_user.role not in ["admin", "auditor"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get document
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.is_active == True
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.status != DocumentStatus.processed:
        raise HTTPException(
            status_code=400,
            detail="Document must be processed before suggesting tasks"
        )

    # Load document chunks from RAG index to get content sample
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".."))
        from services.rag_services import ask_document

        # Ask RAG for document summary to feed into task suggestion
        summary_result = ask_document(
            document_id,
            "Summarize the key compliance issues, risks, and action items in this document in detail."
        )
        doc_summary = summary_result.get("answer", "")
    except Exception as e:
        doc_summary = f"Document: {doc.filename}, Category: {doc.category}"
        print(f"[TASK SUGGEST] RAG summary failed: {e}")

    category = doc.category.value if hasattr(doc.category, 'value') else str(doc.category)

    prompt = f"""You are an expert compliance auditor. Based on this document analysis, suggest specific audit tasks that need to be created.

Document: {doc.filename}
Category: {category.upper()}
Content Summary: {doc_summary}

Generate exactly 5 specific, actionable audit tasks for this document.
Respond ONLY with a valid JSON array, no other text:
[
  {{
    "title": "Short task title (max 60 chars)",
    "description": "Detailed description of what needs to be done (2-3 sentences)",
    "priority": "low" or "medium" or "high" or "critical",
    "suggested_deadline_days": <integer 1-30>
  }}
]

Make tasks specific to the document content, not generic. Focus on compliance, risk, and action items found in the document."""

    try:
        client = get_groq_client()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000
        )
        content = response.choices[0].message.content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        suggestions = json.loads(content)
    except Exception as e:
        print(f"[TASK SUGGEST ERROR] {e}")
        raise HTTPException(status_code=500, detail=f"AI suggestion failed: {str(e)}")

    return {
        "document_id": document_id,
        "document_name": doc.filename,
        "category": category,
        "suggestions": suggestions
    }

# ─────────────────────────────────────────────────────────────
# ANOMALY DETECTION
# ─────────────────────────────────────────────────────────────

@router.get("/anomalies")
def detect_anomalies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Detects unusual patterns in audit logs and flags them.
    Checks for:
    - Login attempts outside business hours (before 7am or after 10pm)
    - Multiple failed login attempts from same IP
    - Unusual bulk document downloads
    - Users accessing documents outside their role
    - High volume of actions in short time period
    """
    if current_user.role not in ["admin", "auditor"]:
        raise HTTPException(status_code=403, detail="Access denied")

    since = datetime.now(timezone.utc) - timedelta(days=7)
    logs = db.query(AuditLog).filter(AuditLog.created_at >= since).all()
    users = db.query(User).all()
    user_map = {u.id: u.full_name for u in users}

    anomalies = []

    # ── 1. Off-hours login activity ───────────────────────────
    off_hours_logins = []
    for log in logs:
        if log.action == "user.login" and log.created_at:
            hour = log.created_at.hour
            if hour < 7 or hour >= 22:
                off_hours_logins.append({
                    "user": user_map.get(log.user_id, f"User#{log.user_id}"),
                    "time": log.created_at.strftime('%d %b %Y %H:%M'),
                    "ip": log.ip_address,
                    "hour": hour
                })

    if off_hours_logins:
        anomalies.append({
            "type": "OFF_HOURS_ACCESS",
            "severity": "MEDIUM",
            "title": f"Off-Hours Login Detected ({len(off_hours_logins)} occurrences)",
            "description": f"{len(off_hours_logins)} login(s) detected outside business hours (7AM-10PM) in the last 7 days.",
            "details": off_hours_logins[:5],
            "recommendation": "Verify these logins were authorized. Consider implementing time-based access controls."
        })

    # ── 2. Multiple failed login attempts ─────────────────────
    failed_by_ip = {}
    for log in logs:
        if log.action == "user.login_failed":
            ip = log.ip_address or "unknown"
            failed_by_ip[ip] = failed_by_ip.get(ip, 0) + 1

    for ip, count in failed_by_ip.items():
        if count >= 3:
            anomalies.append({
                "type": "BRUTE_FORCE_ATTEMPT",
                "severity": "HIGH" if count >= 5 else "MEDIUM",
                "title": f"Multiple Failed Logins from {ip}",
                "description": f"{count} failed login attempts detected from IP {ip} in the last 7 days.",
                "details": [{"ip": ip, "failed_attempts": count}],
                "recommendation": "Consider blocking this IP address or implementing rate limiting."
            })

    # ── 3. High volume actions by single user ─────────────────
    user_action_counts = {}
    for log in logs:
        if log.user_id:
            user_action_counts[log.user_id] = \
                user_action_counts.get(log.user_id, 0) + 1

    if user_action_counts:
        avg_actions = sum(user_action_counts.values()) / len(user_action_counts)
        for uid, count in user_action_counts.items():
            if count > avg_actions * 3 and count > 20:
                anomalies.append({
                    "type": "HIGH_VOLUME_ACTIVITY",
                    "severity": "MEDIUM",
                    "title": f"Unusually High Activity — {user_map.get(uid, f'User#{uid}')}",
                    "description": f"{user_map.get(uid, f'User#{uid}')} performed {count} actions in 7 days, {int(count/avg_actions)}x the average ({int(avg_actions)}).",
                    "details": [{"user": user_map.get(uid, f"User#{uid}"),
                                 "actions": count, "average": int(avg_actions)}],
                    "recommendation": "Review this user's activity log to ensure all actions were authorized."
                })

    # ── 4. Mass document access ───────────────────────────────
    doc_access_by_user = {}
    for log in logs:
        if log.action in ["document.view", "document.ask", "document.download"]:
            uid = log.user_id or 0
            doc_access_by_user[uid] = doc_access_by_user.get(uid, 0) + 1

    for uid, count in doc_access_by_user.items():
        if count >= 10:
            anomalies.append({
                "type": "MASS_DOCUMENT_ACCESS",
                "severity": "HIGH" if count >= 20 else "MEDIUM",
                "title": f"Mass Document Access — {user_map.get(uid, f'User#{uid}')}",
                "description": f"{user_map.get(uid, f'User#{uid}')} accessed {count} documents in the last 7 days.",
                "details": [{"user": user_map.get(uid, f"User#{uid}"),
                             "document_accesses": count}],
                "recommendation": "Verify this user had authorization for all document accesses."
            })

    # ── 5. Multiple deletions ─────────────────────────────────
    deletions = [log for log in logs if log.action in
                 ["document.delete", "task.delete", "user.delete"]]
    if len(deletions) >= 3:
        anomalies.append({
            "type": "MASS_DELETION",
            "severity": "CRITICAL",
            "title": f"Multiple Deletions Detected ({len(deletions)} in 7 days)",
            "description": f"{len(deletions)} deletion actions performed in the last 7 days across documents, tasks, or users.",
            "details": [{"action": d.action,
                         "user": user_map.get(d.user_id, f"User#{d.user_id}"),
                         "time": d.created_at.strftime('%d %b %Y %H:%M')
                         if d.created_at else "—"}
                        for d in deletions[:5]],
            "recommendation": "Review all deletions to ensure they were authorized by management."
        })

    # ── 6. Use AI to analyze patterns ────────────────────────
    if logs:
        action_summary = {}
        for log in logs:
            action_summary[log.action] = action_summary.get(log.action, 0) + 1

        ai_prompt = f"""You are a security analyst reviewing audit logs for a compliance system.

Activity summary for the last 7 days:
{json.dumps(action_summary, indent=2)}

Total users: {len(users)}
Total log entries: {len(logs)}
Anomalies already detected: {len(anomalies)}

Are there any other suspicious patterns worth flagging? 
Respond ONLY with a JSON object:
{{
  "has_additional_anomaly": true or false,
  "anomaly": {{
    "type": "PATTERN_TYPE",
    "severity": "LOW" or "MEDIUM" or "HIGH" or "CRITICAL",
    "title": "Short title",
    "description": "What was detected",
    "recommendation": "What to do about it"
  }}
}}
If no additional anomaly, set has_additional_anomaly to false and anomaly to null."""

        try:
            client = get_groq_client()
            ai_response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": ai_prompt}],
                temperature=0.1,
                max_tokens=400
            )
            ai_content = ai_response.choices[0].message.content.strip()
            if "```" in ai_content:
                ai_content = ai_content.split("```")[1]
                if ai_content.startswith("json"):
                    ai_content = ai_content[4:]
            ai_result = json.loads(ai_content)
            if ai_result.get("has_additional_anomaly") and ai_result.get("anomaly"):
                ai_anomaly = ai_result["anomaly"]
                ai_anomaly["details"] = []
                ai_anomaly["ai_detected"] = True
                anomalies.append(ai_anomaly)
        except Exception as e:
            print(f"[ANOMALY AI ERROR] {e}")

    # Sort by severity
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    anomalies.sort(key=lambda x: severity_order.get(x.get("severity", "LOW"), 3))

    return {
        "anomalies": anomalies,
        "total": len(anomalies),
        "critical": len([a for a in anomalies if a["severity"] == "CRITICAL"]),
        "high": len([a for a in anomalies if a["severity"] == "HIGH"]),
        "medium": len([a for a in anomalies if a["severity"] == "MEDIUM"]),
        "low": len([a for a in anomalies if a["severity"] == "LOW"]),
        "analyzed_logs": len(logs),
        "period_days": 7
    }
