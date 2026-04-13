"""
Task CRUD routes.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models.project import Project
from models.task import Task
from models.time_entry import TimeEntry
from schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskSummaryResponse

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# Phase 1: hardcoded user_id
HARDCODED_USER_ID = "11111111-1111-1111-1111-111111111111"


def get_current_user_id() -> str:
    return HARDCODED_USER_ID


def _compute_task_time(db: Session, task_id: str) -> int:
    """Sum all completed time entry durations for a task (in seconds)."""
    total = (
        db.query(func.coalesce(func.sum(TimeEntry.duration_seconds), 0))
        .filter(TimeEntry.task_id == task_id, TimeEntry.ended_at.isnot(None))
        .scalar()
    )
    return total or 0


def _build_task_response(db: Session, task: Task) -> TaskResponse:
    """Build a TaskResponse with computed fields."""
    project = db.query(Project).filter(Project.id == task.project_id).first()
    total_time = _compute_task_time(db, task.id)

    return TaskResponse(
        id=task.id,
        user_id=task.user_id,
        project_id=task.project_id,
        project_name=project.name if project else "",
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        is_today=task.is_today,
        estimated_hours=task.estimated_hours,
        total_time_spent=total_time,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.get("", response_model=List[TaskResponse])
def list_tasks(
    project_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None, pattern="^(todo|in-progress|done)$"),
    is_today: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List tasks, optionally filtered by project, status, or is_today."""
    query = db.query(Task).filter(Task.user_id == user_id)
    if project_id:
        query = query.filter(Task.project_id == project_id)
    if status:
        query = query.filter(Task.status == status)
    if is_today is not None:
        query = query.filter(Task.is_today == is_today)

    tasks = query.order_by(Task.created_at.desc()).all()
    return [_build_task_response(db, task) for task in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get a single task by ID."""
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return _build_task_response(db, task)


@router.post("", response_model=TaskResponse, status_code=201)
def create_task(
    data: TaskCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a new task linked to a project."""
    # Verify project exists and belongs to user
    project = db.query(Project).filter(Project.id == data.project_id, Project.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    task = Task(
        user_id=user_id,
        project_id=data.project_id,
        title=data.title,
        description=data.description,
        status=data.status,
        priority=data.priority,
        is_today=data.is_today,
        estimated_hours=data.estimated_hours,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    return _build_task_response(db, task)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: str,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update an existing task."""
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    return _build_task_response(db, task)


@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Delete a task and cascade to all time entries."""
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return None


@router.get("/{task_id}/summary", response_model=TaskSummaryResponse)
def get_task_summary(
    task_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get task with total time spent computed from time entries."""
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    total_time = _compute_task_time(db, task.id)
    entry_count = db.query(func.count(TimeEntry.id)).filter(TimeEntry.task_id == task.id).scalar()

    return TaskSummaryResponse(
        id=task.id,
        title=task.title,
        status=task.status,
        priority=task.priority,
        is_today=task.is_today,
        estimated_hours=task.estimated_hours,
        total_time_spent=total_time,
        time_entry_count=entry_count,
    )
