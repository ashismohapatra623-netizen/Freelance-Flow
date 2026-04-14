"""
Dashboard summary route — aggregated view of the freelancer's data.
"""
from datetime import date, timedelta, datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models.client import Client
from models.project import Project
from models.task import Task
from models.time_entry import TimeEntry
from middleware.auth import get_current_user_id

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def get_dashboard(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Dashboard summary:
    - Active clients count
    - Active projects count
    - Today's task count by status
    - Projects with overdue deadlines
    - Projects with deadlines within 3 days
    - Total billable hours this week
    """
    today = date.today()

    # Active counts
    active_clients = (
        db.query(func.count(Client.id))
        .filter(Client.user_id == user_id, Client.status == "active")
        .scalar()
    )

    active_projects = (
        db.query(func.count(Project.id))
        .filter(Project.user_id == user_id, Project.status == "active")
        .scalar()
    )

    # Today's tasks by status
    today_todo = (
        db.query(func.count(Task.id))
        .filter(Task.user_id == user_id, Task.is_today == True, Task.status == "todo")
        .scalar()
    )
    today_in_progress = (
        db.query(func.count(Task.id))
        .filter(Task.user_id == user_id, Task.is_today == True, Task.status == "in-progress")
        .scalar()
    )
    today_done = (
        db.query(func.count(Task.id))
        .filter(Task.user_id == user_id, Task.is_today == True, Task.status == "done")
        .scalar()
    )

    # Overdue projects (deadline < today, not completed)
    overdue_projects = (
        db.query(Project)
        .filter(
            Project.user_id == user_id,
            Project.deadline < today,
            Project.status != "completed",
            Project.deadline.isnot(None),
        )
        .all()
    )

    # Approaching deadline projects (deadline within 3 days, not completed, not overdue)
    approaching_projects = (
        db.query(Project)
        .filter(
            Project.user_id == user_id,
            Project.deadline >= today,
            Project.deadline <= today + timedelta(days=3),
            Project.status != "completed",
            Project.deadline.isnot(None),
        )
        .all()
    )

    # Total billable hours this week (Monday to Sunday)
    # Get the Monday of the current week
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    monday_dt = datetime.combine(monday, datetime.min.time())
    sunday_dt = datetime.combine(sunday, datetime.max.time())

    weekly_seconds = (
        db.query(func.coalesce(func.sum(TimeEntry.duration_seconds), 0))
        .join(Task, TimeEntry.task_id == Task.id)
        .join(Project, Task.project_id == Project.id)
        .filter(
            TimeEntry.user_id == user_id,
            TimeEntry.ended_at.isnot(None),
            TimeEntry.started_at >= monday_dt,
            TimeEntry.started_at <= sunday_dt,
            Project.is_billable == True,
        )
        .scalar()
    )
    weekly_billable_hours = round((weekly_seconds or 0) / 3600, 2)

    return {
        "active_clients": active_clients,
        "active_projects": active_projects,
        "today_tasks": {
            "todo": today_todo,
            "in_progress": today_in_progress,
            "done": today_done,
            "total": today_todo + today_in_progress + today_done,
        },
        "overdue_projects": [
            {
                "id": p.id,
                "name": p.name,
                "deadline": p.deadline.isoformat() if p.deadline else None,
                "status": p.status,
            }
            for p in overdue_projects
        ],
        "approaching_deadline_projects": [
            {
                "id": p.id,
                "name": p.name,
                "deadline": p.deadline.isoformat() if p.deadline else None,
                "status": p.status,
            }
            for p in approaching_projects
        ],
        "weekly_billable_hours": weekly_billable_hours,
    }
