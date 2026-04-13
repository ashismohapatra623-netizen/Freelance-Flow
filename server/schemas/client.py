"""
Pydantic schemas for Client endpoints.
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field


class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    company: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    status: Literal["active", "inactive"] = "active"


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    company: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    status: Optional[Literal["active", "inactive"]] = None


class ClientResponse(BaseModel):
    id: str
    user_id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    company: Optional[str]
    notes: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    project_count: int = 0

    model_config = {"from_attributes": True}


class ClientListResponse(BaseModel):
    id: str
    name: str
    email: Optional[str]
    company: Optional[str]
    status: str
    project_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}
