# Task comment endpoints — Jira-style discussion on tasks.
# POST /tasks/{id}/comments        — add a comment
# GET  /tasks/{id}/comments        — list all comments on a task
# PATCH /tasks/{id}/comments/{cid} — edit your own comment
# DELETE /tasks/{id}/comments/{cid}— delete your own comment (or admin)

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.task import Task
from models.task_comment import TaskComment
from schemas.task_comment import CommentCreate, CommentUpdate, CommentResponse
from auth.dependencies import get_current_user
from services.audit_services import log_action
from typing import Optional

router = APIRouter(tags=["Comments"])


@router.post("/tasks/{task_id}/comments", response_model=CommentResponse)
def add_comment(
    task_id: int,
    body: CommentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify task exists and user has access
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if current_user.role not in ["admin", "auditor"] and task.assigned_to != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if not body.content.strip():
        raise HTTPException(status_code=400, detail="Comment cannot be empty")

    comment = TaskComment(
        task_id=task_id,
        user_id=current_user.id,
        content=body.content.strip()
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    log_action(
        db=db,
        action="task.comment_add",
        user_id=current_user.id,
        resource_type="task",
        resource_id=task_id,
        details={"comment_id": comment.id, "task_title": task.title},
        ip_address=request.client.host
    )

    return comment


@router.get("/tasks/{task_id}/comments", response_model=list[CommentResponse])
def get_comments(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if current_user.role not in ["admin", "auditor"] and task.assigned_to != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return db.query(TaskComment).filter(
        TaskComment.task_id == task_id
    ).order_by(TaskComment.created_at.asc()).all()


@router.patch("/tasks/{task_id}/comments/{comment_id}", response_model=CommentResponse)
def edit_comment(
    task_id: int,
    comment_id: int,
    body: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    comment = db.query(TaskComment).filter(
        TaskComment.id == comment_id,
        TaskComment.task_id == task_id
    ).first()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Only the comment author can edit
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own comments")

    comment.content = body.content.strip()
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/tasks/{task_id}/comments/{comment_id}")
def delete_comment(
    task_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    comment = db.query(TaskComment).filter(
        TaskComment.id == comment_id,
        TaskComment.task_id == task_id
    ).first()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Author or admin can delete
    if comment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted"}


