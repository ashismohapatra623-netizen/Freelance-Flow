"""
Project CRUD routes.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models.client import Client
from models.project import Project
from models.task import Task
from models.time_entry import TimeEntry
from schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse
from middleware.auth import get_current_user_id

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _compute_project_seconds(db: Session, project_id: str) -> int:
    """Sum all time entry durations for a project's tasks (in seconds)."""
    total = (
        db.query(func.coalesce(func.sum(TimeEntry.duration_seconds), 0))
        .join(Task, TimeEntry.task_id == Task.id)
        .filter(Task.project_id == project_id)
        .scalar()
    )
    return total or 0


def _compute_project_hours(db: Session, project_id: str) -> float:
    """Sum all time entry durations for a project's tasks (in hours)."""
    total = _compute_project_seconds(db, project_id)
    return round(total / 3600, 2) if total else 0.0


@router.get("", response_model=List[ProjectListResponse])
def list_projects(
    client_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None, pattern="^(active|on-hold|completed)$"),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List all projects, optionally filtered by client and/or status."""
    query = db.query(Project).filter(Project.user_id == user_id)
    if client_id:
        query = query.filter(Project.client_id == client_id)
    if status:
        query = query.filter(Project.status == status)

    projects = query.order_by(Project.created_at.desc()).all()

    result = []
    for project in projects:
        client = db.query(Client).filter(Client.id == project.client_id).first()
        task_count = db.query(func.count(Task.id)).filter(Task.project_id == project.id).scalar()
        total_hours = _compute_project_hours(db, project.id)

        result.append(ProjectListResponse(
            id=project.id,
            client_id=project.client_id,
            client_name=client.name if client else "",
            name=project.name,
            status=project.status,
            deadline=project.deadline,
            is_billable=project.is_billable,
            task_count=task_count,
            total_hours=total_hours,
            created_at=project.created_at,
        ))
    return result


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get a single project by ID."""
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    client = db.query(Client).filter(Client.id == project.client_id).first()
    task_count = db.query(func.count(Task.id)).filter(Task.project_id == project.id).scalar()
    total_hours = _compute_project_hours(db, project.id)

    return ProjectResponse(
        id=project.id,
        user_id=project.user_id,
        client_id=project.client_id,
        client_name=client.name if client else "",
        name=project.name,
        description=project.description,
        status=project.status,
        deadline=project.deadline,
        hourly_rate=project.hourly_rate,
        is_billable=project.is_billable,
        created_at=project.created_at,
        updated_at=project.updated_at,
        task_count=task_count,
        total_hours=total_hours,
    )


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a new project linked to a client."""
    # Verify client exists and belongs to user
    client = db.query(Client).filter(Client.id == data.client_id, Client.user_id == user_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    project = Project(
        user_id=user_id,
        client_id=data.client_id,
        name=data.name,
        description=data.description,
        status=data.status,
        deadline=data.deadline,
        hourly_rate=data.hourly_rate,
        is_billable=data.is_billable,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    return ProjectResponse(
        id=project.id,
        user_id=project.user_id,
        client_id=project.client_id,
        client_name=client.name,
        name=project.name,
        description=project.description,
        status=project.status,
        deadline=project.deadline,
        hourly_rate=project.hourly_rate,
        is_billable=project.is_billable,
        created_at=project.created_at,
        updated_at=project.updated_at,
        task_count=0,
        total_hours=0.0,
    )


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update an existing project."""
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = data.model_dump(exclude_unset=True)

    # If changing client, verify new client exists and belongs to user
    if "client_id" in update_data:
        client = db.query(Client).filter(Client.id == update_data["client_id"], Client.user_id == user_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)

    client = db.query(Client).filter(Client.id == project.client_id).first()
    task_count = db.query(func.count(Task.id)).filter(Task.project_id == project.id).scalar()
    total_hours = _compute_project_hours(db, project.id)

    return ProjectResponse(
        id=project.id,
        user_id=project.user_id,
        client_id=project.client_id,
        client_name=client.name if client else "",
        name=project.name,
        description=project.description,
        status=project.status,
        deadline=project.deadline,
        hourly_rate=project.hourly_rate,
        is_billable=project.is_billable,
        created_at=project.created_at,
        updated_at=project.updated_at,
        task_count=task_count,
        total_hours=total_hours,
    )


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Delete a project and cascade to all tasks/time entries."""
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()
    return None


# ═══════════════════════════════════════════════
# Phase 3: Business Logic Endpoints
# ═══════════════════════════════════════════════

@router.patch("/{project_id}/status")
def change_project_status(
    project_id: str,
    data: dict,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Change project status.
    If set to 'completed', warn about incomplete tasks (don't block).
    """
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    new_status = data.get("status")
    valid_statuses = ["active", "on-hold", "completed"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=422, detail=f"Invalid status. Must be one of: {valid_statuses}")

    warnings = []

    if new_status == "completed":
        incomplete_count = (
            db.query(func.count(Task.id))
            .filter(Task.project_id == project.id, Task.status != "done")
            .scalar()
        )
        if incomplete_count > 0:
            warnings.append(f"{incomplete_count} task(s) are not yet done")

    project.status = new_status
    db.commit()
    db.refresh(project)

    client = db.query(Client).filter(Client.id == project.client_id).first()
    task_count = db.query(func.count(Task.id)).filter(Task.project_id == project.id).scalar()
    total_hours = _compute_project_hours(db, project.id)

    response = ProjectResponse(
        id=project.id,
        user_id=project.user_id,
        client_id=project.client_id,
        client_name=client.name if client else "",
        name=project.name,
        description=project.description,
        status=project.status,
        deadline=project.deadline,
        hourly_rate=project.hourly_rate,
        is_billable=project.is_billable,
        created_at=project.created_at,
        updated_at=project.updated_at,
        task_count=task_count,
        total_hours=total_hours,
    ).model_dump()

    if warnings:
        response["warnings"] = warnings

    return response


@router.get("/{project_id}/summary")
def get_project_summary(
    project_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Detailed project summary including:
    - Project info + client name
    - Task counts by status
    - Total time spent
    - Billable amount (hours * hourly_rate)
    - Deadline status (approaching/overdue)
    """
    from datetime import date, timedelta

    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    client = db.query(Client).filter(Client.id == project.client_id).first()

    # Task counts by status
    total_tasks = db.query(func.count(Task.id)).filter(Task.project_id == project.id).scalar()
    todo_count = db.query(func.count(Task.id)).filter(Task.project_id == project.id, Task.status == "todo").scalar()
    in_progress_count = db.query(func.count(Task.id)).filter(Task.project_id == project.id, Task.status == "in-progress").scalar()
    done_count = db.query(func.count(Task.id)).filter(Task.project_id == project.id, Task.status == "done").scalar()

    # Total time
    total_seconds = _compute_project_seconds(db, project.id)
    total_hours = round(total_seconds / 3600, 2) if total_seconds else 0.0

    # Billable amount
    billable_amount = None
    if project.is_billable and project.hourly_rate:
        billable_amount = round(total_hours * project.hourly_rate, 2)

    # Deadline status
    today = date.today()
    is_overdue = False
    is_approaching = False
    if project.deadline and project.status != "completed":
        if project.deadline < today:
            is_overdue = True
        elif project.deadline <= today + timedelta(days=3):
            is_approaching = True

    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "status": project.status,
            "deadline": project.deadline.isoformat() if project.deadline else None,
            "hourly_rate": project.hourly_rate,
            "is_billable": project.is_billable,
        },
        "client_name": client.name if client else "",
        "tasks": {
            "total": total_tasks,
            "todo": todo_count,
            "in_progress": in_progress_count,
            "done": done_count,
        },
        "total_seconds": total_seconds,
        "total_hours": total_hours,
        "billable_amount": billable_amount,
        "deadline_status": {
            "is_overdue": is_overdue,
            "is_approaching": is_approaching,
        },
    }

