"""
TimeEntry routes — start/stop timer, list entries for a task.
"""
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models.task import Task
from models.time_entry import TimeEntry
from schemas.time_entry import TimeEntryCreate, TimeEntryStop, TimeEntryResponse

router = APIRouter(prefix="/api/time-entries", tags=["time-entries"])

# Phase 1: hardcoded user_id
HARDCODED_USER_ID = "11111111-1111-1111-1111-111111111111"


def get_current_user_id() -> str:
    return HARDCODED_USER_ID


@router.post("", response_model=TimeEntryResponse, status_code=201)
def start_timer(
    data: TimeEntryCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Start a timer for a task (create time entry with no ended_at)."""
    # Verify task exists and belongs to user
    task = db.query(Task).filter(Task.id == data.task_id, Task.user_id == user_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Check if this task already has a running timer
    existing = (
        db.query(TimeEntry)
        .filter(TimeEntry.task_id == data.task_id, TimeEntry.ended_at.is_(None))
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Timer is already running for this task")

    entry = TimeEntry(
        user_id=user_id,
        task_id=data.task_id,
        note=data.note,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return TimeEntryResponse.model_validate(entry)


@router.put("/{entry_id}/stop", response_model=TimeEntryResponse)
def stop_timer(
    entry_id: str,
    data: TimeEntryStop = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Stop a running timer — sets ended_at and computes duration_seconds."""
    entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id, TimeEntry.user_id == user_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")

    if entry.ended_at is not None:
        raise HTTPException(status_code=400, detail="Timer is already stopped")

    now = datetime.utcnow()
    entry.ended_at = now
    # started_at from SQLite is naive (no timezone), so now must be naive too
    entry.duration_seconds = int((now - entry.started_at).total_seconds())

    if data and data.note is not None:
        entry.note = data.note

    db.commit()
    db.refresh(entry)

    return TimeEntryResponse.model_validate(entry)


@router.get("", response_model=List[TimeEntryResponse])
def list_time_entries(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List all time entries for the current user."""
    entries = (
        db.query(TimeEntry)
        .filter(TimeEntry.user_id == user_id)
        .order_by(TimeEntry.started_at.desc())
        .all()
    )
    return [TimeEntryResponse.model_validate(e) for e in entries]


@router.get("/{entry_id}", response_model=TimeEntryResponse)
def get_time_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get a single time entry."""
    entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id, TimeEntry.user_id == user_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
    return TimeEntryResponse.model_validate(entry)


@router.delete("/{entry_id}", status_code=204)
def delete_time_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Delete a time entry."""
    entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id, TimeEntry.user_id == user_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
    db.delete(entry)
    db.commit()
    return None
