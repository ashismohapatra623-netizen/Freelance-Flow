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
from middleware.auth import get_current_user_id

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


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


# ═══════════════════════════════════════════════
# Phase 3: Business Logic Endpoints
# ═══════════════════════════════════════════════

@router.patch("/{task_id}/status")
def change_task_status(
    task_id: str,
    data: dict,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Change task status with validation.
    All transitions between todo/in-progress/done are allowed.
    If status → done and timer is running, auto-stop the timer.
    If status → in-progress and no active timer, suggest starting one.
    """
    from datetime import datetime

    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    new_status = data.get("status")
    valid_statuses = ["todo", "in-progress", "done"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=422, detail=f"Invalid status. Must be one of: {valid_statuses}")

    old_status = task.status
    metadata = {}

    # If changing to 'done', auto-stop any running timer
    if new_status == "done":
        running_entry = (
            db.query(TimeEntry)
            .filter(TimeEntry.task_id == task.id, TimeEntry.ended_at.is_(None))
            .first()
        )
        if running_entry:
            now = datetime.utcnow()
            running_entry.ended_at = now
            running_entry.duration_seconds = int((now - running_entry.started_at).total_seconds())
            metadata["timer_stopped"] = True
            metadata["duration_seconds"] = running_entry.duration_seconds

    # If changing to 'in-progress', suggest starting timer if none running
    if new_status == "in-progress":
        running_entry = (
            db.query(TimeEntry)
            .filter(TimeEntry.task_id == task.id, TimeEntry.ended_at.is_(None))
            .first()
        )
        if not running_entry:
            metadata["suggest_start_timer"] = True

    task.status = new_status
    db.commit()
    db.refresh(task)

    response = _build_task_response(db, task).model_dump()
    response["metadata"] = metadata
    response["old_status"] = old_status
    return response


@router.patch("/{task_id}/today")
def toggle_today(
    task_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Toggle the is_today flag for a task."""
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.is_today = not task.is_today
    db.commit()
    db.refresh(task)

    return _build_task_response(db, task)


@router.get("/today/list", response_model=List[TaskResponse])
def get_today_tasks(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get all tasks marked for today, grouped by status."""
    tasks = (
        db.query(Task)
        .filter(Task.user_id == user_id, Task.is_today == True)
        .order_by(Task.status, Task.created_at.desc())
        .all()
    )
    return [_build_task_response(db, task) for task in tasks]


@router.post("/today/bulk")
def bulk_set_today(
    data: dict,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Set is_today=true for an array of task IDs."""
    task_ids = data.get("task_ids", [])
    if not isinstance(task_ids, list):
        raise HTTPException(status_code=422, detail="task_ids must be an array")

    updated = 0
    for tid in task_ids:
        task = db.query(Task).filter(Task.id == tid, Task.user_id == user_id).first()
        if task:
            task.is_today = True
            updated += 1

    db.commit()
    return {"updated": updated, "total_requested": len(task_ids)}

