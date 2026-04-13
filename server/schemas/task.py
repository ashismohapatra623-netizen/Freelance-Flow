"""
Pydantic schemas for Task endpoints.
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    project_id: str
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: Literal["todo", "in-progress", "done"] = "todo"
    priority: Literal["low", "medium", "high"] = "medium"
    is_today: bool = False
    estimated_hours: Optional[float] = Field(None, ge=0)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[Literal["todo", "in-progress", "done"]] = None
    priority: Optional[Literal["low", "medium", "high"]] = None
    is_today: Optional[bool] = None
    estimated_hours: Optional[float] = Field(None, ge=0)


class TaskResponse(BaseModel):
    id: str
    user_id: str
    project_id: str
    project_name: str = ""
    title: str
    description: Optional[str]
    status: str
    priority: str
    is_today: bool
    estimated_hours: Optional[float]
    total_time_spent: int = 0  # seconds
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskSummaryResponse(BaseModel):
    """Task with total time spent computed from time entries."""
    id: str
    title: str
    status: str
    priority: str
    is_today: bool
    estimated_hours: Optional[float]
    total_time_spent: int = 0  # seconds
    time_entry_count: int = 0

    model_config = {"from_attributes": True}
