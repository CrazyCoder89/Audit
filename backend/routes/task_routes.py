# Task management endpoints:
# POST /tasks/              — create a new task (admin/auditor only)
# GET  /tasks/              — list tasks (filtered by role)
# GET  /tasks/{id}          — get a single task
# PATCH /tasks/{id}         — update task status or details
# DELETE /tasks/{id}        — delete a task (admin only)
# GET  /tasks/overdue       — list all overdue tasks

from fastapi import APIRouter, Depends, HTTPException, Request,Query
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.task import Task, TaskStatus
from schemas.task import TaskCreate, TaskUpdate, TaskResponse
from auth.dependencies import get_current_user, require_admin
from services.audit_services import log_action
from datetime import datetime, timezone
from typing import Optional

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def check_overdue(task: Task) -> Task:
    """Automatically marks a task as overdue if deadline has passed."""
    if (
        task.deadline
        and task.status not in [TaskStatus.completed, TaskStatus.overdue]
        and task.deadline < datetime.now(timezone.utc)
    ):
        task.status = TaskStatus.overdue
    return task

@router.post("/", response_model=TaskResponse)
def create_task(
    task_data: TaskCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only admins and auditors can create tasks
    if current_user.role not in ["admin", "auditor"]:
        raise HTTPException(status_code=403, detail="Only admins and auditors can create tasks")

    # If assigning to someone, verify that user exists
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

    log_action(
        db=db,
        action="task.create",
        user_id=current_user.id,
        resource_type="task",
        resource_id=new_task.id,
        details={"title": new_task.title, "assigned_to": new_task.assigned_to},
        ip_address=request.client.host
    )

    return new_task


@router.get("/overdue", response_model=list[TaskResponse])
def get_overdue_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only admins and auditors can see overdue tasks
    if current_user.role not in ["admin", "auditor"]:
        raise HTTPException(status_code=403, detail="Access denied")

    now = datetime.now(timezone.utc)
    tasks = db.query(Task).filter(
        Task.deadline < now,
        Task.status != TaskStatus.completed
    ).all()

    # Mark them as overdue in DB
    for task in tasks:
        if task.status != TaskStatus.overdue:
            task.status = TaskStatus.overdue
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

    # Admins and auditors see all tasks
    # Viewers only see tasks assigned to them
    if current_user.role not in ["admin", "auditor"]:
        query = query.filter(Task.assigned_to == current_user.id)

    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)

    tasks = query.order_by(Task.created_at.desc()).all()

    # Auto-check for overdue
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

    # Viewers can only see their own assigned tasks
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

    # Viewers can only update status of their own assigned tasks
    if current_user.role not in ["admin", "auditor"]:
        if task.assigned_to != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        # Viewers can only change status, nothing else
        if any([
            task_update.title,
            task_update.description,
            task_update.priority,
            task_update.deadline,
            task_update.assigned_to
        ]):
            raise HTTPException(status_code=403, detail="Viewers can only update task status")

    # Apply updates — only update fields that were actually provided
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


