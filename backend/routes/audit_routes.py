# Audit log endpoints — only admins and auditors can view logs
# GET /audit/           — list all logs (with filters)
# GET /audit/export     — export logs as CSV

import csv
import json
import io
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.audit_log import AuditLog
from schemas.audit_log import AuditLogResponse
from auth.dependencies import get_current_user
from services.audit_services import get_logs
from typing import Optional

router = APIRouter(prefix="/audit", tags=["Audit Logs"])

@router.get("/", response_model=list[AuditLogResponse])
def list_audit_logs(
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only admins and auditors can view audit logs
    if current_user.role not in ["admin", "auditor"]:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Access denied")

    return get_logs(db, user_id=user_id, action=action, resource_type=resource_type, limit=limit)

@router.get("/export")
def export_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only admins can export logs
    if current_user.role != "admin":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin access required")

    logs = get_logs(db, limit=500)

    # Build CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "User ID", "Action", "Resource Type", "Resource ID", "Details", "IP Address", "Timestamp"])

    for log in logs:
        writer.writerow([
            log.id,
            log.user_id,
            log.action,
            log.resource_type,
            log.resource_id,
            log.details,
            log.ip_address,
            log.created_at.isoformat()
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"}
    )



