# Task management endpoints:
# POST /tasks/              — create a new task (admin/auditor only)
# GET  /tasks/              — list tasks (filtered by role)
# GET  /tasks/{id}          — get a single task
# PATCH /tasks/{id}         — update task status or details
# DELETE /tasks/{id}        — delete a task (admin only)
# GET  /tasks/overdue       — list all overdue tasks

import os
import sys
import threading
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.task import Task, TaskStatus
from schemas.task import TaskCreate, TaskUpdate, TaskResponse
from auth.dependencies import get_current_user, require_admin
from services.audit_services import log_action
from services.notification_service import (
    notify_task_assigned,
    notify_task_overdue,
    notify_task_status_changed
)
from datetime import datetime, timezone
from typing import Optional
from fastapi import Query

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def check_overdue(task: Task) -> Task:
    if (
        task.deadline
        and task.status not in [TaskStatus.completed, TaskStatus.overdue]
        and task.deadline < datetime.now(timezone.utc)
    ):
        task.status = TaskStatus.overdue
    return task


def send_async(fn, *args, **kwargs):
    """Runs email sending in a background thread so it doesn't block the API."""
    thread = threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True)
    thread.start()


@router.post("/", response_model=TaskResponse)
def create_task(
    task_data: TaskCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "auditor"]:
        raise HTTPException(status_code=403, detail="Only admins and auditors can create tasks")

    assignee = None
    if task_data.assigned_to:
        assignee = db.query(User).filter(User.id == task_data.assigned_to).first()
        if not assignee:
            raise HTTPException(status_code=404, detail="Assigned user not found")

    new_task = Task(
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
        deadline=task_data.deadline,
        assigned_to=task_data.assigned_to,
        document_id=task_data.document_id,
        created_by=current_user.id
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    # Auto-trigger RAG processing if linked document is still pending
    if new_task.document_id:
        from models.document import Document, DocumentStatus
        from services.rag_services import process_document
        linked_doc = db.query(Document).filter(Document.id == new_task.document_id).first()
        if linked_doc and linked_doc.status == DocumentStatus.pending:
            def process_and_update(file_path, doc_id):
                from database import SessionLocal
                bg_db = SessionLocal()
                try:
                    result = process_document(file_path, doc_id)
                    d = bg_db.query(Document).filter(Document.id == doc_id).first()
                    if d:
                        d.status = DocumentStatus.processed if result["status"] == "success" else DocumentStatus.failed
                        bg_db.commit()
                    print(f"[AUTO-PROCESS] Document {doc_id} — {result['status']}")
                except Exception as e:
                    print(f"[AUTO-PROCESS ERROR] {e}")
                finally:
                    bg_db.close()

            thread = threading.Thread(
                target=process_and_update,
                args=(linked_doc.file_path, linked_doc.id),
                daemon=True
            )
            thread.start()
            print(f"[AUTO-PROCESS] Triggered for document {linked_doc.id}")

    log_action(
        db=db,
        action="task.create",
        user_id=current_user.id,
        resource_type="task",
        resource_id=new_task.id,
        details={"title": new_task.title, "assigned_to": new_task.assigned_to},
        ip_address=request.client.host
    )

    # Send assignment notification in background
    if assignee and assignee.email:
        deadline_str = new_task.deadline.strftime('%d %b %Y, %H:%M') if new_task.deadline else None

        doc_name = None
        if new_task.document_id:
            from models.document import Document
            linked_doc = db.query(Document).filter(Document.id == new_task.document_id).first()
            doc_name = linked_doc.filename if linked_doc else None

        description_with_doc = new_task.description or ""
        if doc_name:
            description_with_doc += f"\n\n📄 Linked Document: {doc_name}\nThis document has been shared with you and is available in your Documents page."

        send_async(
            notify_task_assigned,
            to_email=assignee.email,
            assignee_name=assignee.full_name,
            task_title=new_task.title,
            task_description=description_with_doc,
            priority=new_task.priority,
            deadline=deadline_str,
            assigned_by=current_user.full_name
        )

    return new_task

@router.get("/overdue", response_model=list[TaskResponse])
def get_overdue_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["admin", "auditor"]:
        raise HTTPException(status_code=403, detail="Access denied")

    now = datetime.now(timezone.utc)
    tasks = db.query(Task).filter(
        Task.deadline < now,
        Task.status != TaskStatus.completed
    ).all()

    for task in tasks:
        if task.status != TaskStatus.overdue:
            task.status = TaskStatus.overdue

            # Notify assignee about overdue in background
            if task.assigned_to:
                assignee = db.query(User).filter(User.id == task.assigned_to).first()
                if assignee:
                    days_overdue = (datetime.now(timezone.utc) - task.deadline).days
                    send_async(
                        notify_task_overdue,
                        to_email=assignee.email,
                        assignee_name=assignee.full_name,
                        task_title=task.title,
                        deadline=task.deadline.strftime('%d %b %Y'),
                        days_overdue=max(1, days_overdue),
                        priority=task.priority
                    )
    db.commit()
    return tasks




@router.get("/", response_model=list[TaskResponse])
def list_tasks(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Task)
    if current_user.role not in ["admin", "auditor"]:
        query = query.filter(Task.assigned_to == current_user.id)
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)

    tasks = query.order_by(Task.created_at.desc()).all()
    for task in tasks:
        check_overdue(task)
    db.commit()
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if current_user.role not in ["admin", "auditor"] and task.assigned_to != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return check_overdue(task)


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if current_user.role not in ["admin", "auditor"]:
        if task.assigned_to != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        if any([task_update.title, task_update.description,
                task_update.priority, task_update.deadline, task_update.assigned_to]):
            raise HTTPException(status_code=403, detail="Viewers can only update task status")

    old_status = task.status
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    log_action(
        db=db,
        action="task.update",
        user_id=current_user.id,
        resource_type="task",
        resource_id=task_id,
        details=update_data,
        ip_address=request.client.host
    )

    # Send status change notification in background
    new_status = task_update.status
    if new_status and new_status != old_status:
        # Notify assignee
        if task.assigned_to:
            assignee = db.query(User).filter(User.id == task.assigned_to).first()
            if assignee:
                send_async(
                    notify_task_status_changed,
                    to_email=assignee.email,
                    recipient_name=assignee.full_name,
                    task_title=task.title,
                    old_status=old_status,
                    new_status=new_status,
                    changed_by=current_user.full_name
                )
        # Also notify task creator if different from assignee
        if task.created_by != task.assigned_to:
            creator = db.query(User).filter(User.id == task.created_by).first()
            if creator:
                send_async(
                    notify_task_status_changed,
                    to_email=creator.email,
                    recipient_name=creator.full_name,
                    task_title=task.title,
                    old_status=old_status,
                    new_status=new_status,
                    changed_by=current_user.full_name
                )

    return task


@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()

    log_action(
        db=db,
        action="task.delete",
        user_id=current_user.id,
        resource_type="task",
        resource_id=task_id,
        details={"title": task.title},
        ip_address=request.client.host
    )

    return {"message": f"Task {task_id} deleted successfully"}

@router.get("/search/query", response_model=list[TaskResponse])
def search_tasks(
    q: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search tasks by title or description."""
    from sqlalchemy import or_
    query = db.query(Task)

    if current_user.role not in ["admin", "auditor"]:
        query = query.filter(Task.assigned_to == current_user.id)

    results = query.filter(
        or_(
            Task.title.ilike(f"%{q}%"),
            Task.description.ilike(f"%{q}%"),
            Task.priority.ilike(f"%{q}%"),
            Task.status.ilike(f"%{q}%")
        )
    ).all()
    return results

