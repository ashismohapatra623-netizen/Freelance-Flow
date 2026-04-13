"""
Pydantic schemas for TimeEntry endpoints.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TimeEntryCreate(BaseModel):
    task_id: str
    note: Optional[str] = Field(None, max_length=500)


class TimeEntryStop(BaseModel):
    note: Optional[str] = Field(None, max_length=500)


class TimeEntryResponse(BaseModel):
    id: str
    user_id: str
    task_id: str
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: Optional[int]
    note: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
