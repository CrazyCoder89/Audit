# Helper service for creating audit log entries.
# Call log_action() from any route to record what happened.
# Example: log_action(db, user_id=1, action="document.upload", resource_type="document", resource_id=5)

from sqlalchemy.orm import Session
from models.audit_log import AuditLog
import json

def log_action(
    db: Session,
    action: str,
    user_id: int = None,
    resource_type: str = None,
    resource_id: int = None,
    details: dict = None,
    ip_address: str = None
):
    """
    Creates a new audit log entry in the database.

    Args:
        db           : database session
        action       : what happened e.g. "document.upload", "user.login", "document.ask"
        user_id      : who did it (None for system actions)
        resource_type: what type of thing was affected e.g. "document", "user"
        resource_id  : the ID of the affected thing
        details      : any extra info as a dict — gets stored as JSON string
        ip_address   : the IP address of the request
    """
    details_str = json.dumps(details) if details else None

    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details_str,
        ip_address=ip_address
    )

    db.add(log_entry)
    db.commit()


def get_logs(
    db: Session,
    user_id: int = None,
    action: str = None,
    resource_type: str = None,
    limit: int = 100
):
    """
    Retrieves audit logs with optional filters.

    Args:
        db           : database session
        user_id      : filter by specific user
        action       : filter by action type
        resource_type: filter by resource type
        limit        : max number of logs to return
    """
    query = db.query(AuditLog)

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)

    # Most recent first
    return query.order_by(AuditLog.created_at.desc()).limit(limit).all()