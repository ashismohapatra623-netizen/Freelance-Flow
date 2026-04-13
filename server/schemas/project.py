"""
Pydantic schemas for Project endpoints.
"""
from datetime import datetime, date
from typing import Optional, Literal
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    client_id: str
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: Literal["active", "on-hold", "completed"] = "active"
    deadline: Optional[date] = None
    hourly_rate: Optional[float] = Field(None, ge=0)
    is_billable: bool = True


class ProjectUpdate(BaseModel):
    client_id: Optional[str] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[Literal["active", "on-hold", "completed"]] = None
    deadline: Optional[date] = None
    hourly_rate: Optional[float] = Field(None, ge=0)
    is_billable: Optional[bool] = None


class ProjectResponse(BaseModel):
    id: str
    user_id: str
    client_id: str
    client_name: str = ""
    name: str
    description: Optional[str]
    status: str
    deadline: Optional[date]
    hourly_rate: Optional[float]
    is_billable: bool
    created_at: datetime
    updated_at: datetime
    task_count: int = 0
    total_hours: float = 0.0

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    id: str
    client_id: str
    client_name: str = ""
    name: str
    status: str
    deadline: Optional[date]
    is_billable: bool
    task_count: int = 0
    total_hours: float = 0.0
    created_at: datetime

    model_config = {"from_attributes": True}
