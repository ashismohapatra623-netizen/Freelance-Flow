"""
Pydantic schemas for Auth endpoints (used in Phase 2, defined now for structure).
"""
from pydantic import BaseModel, Field, EmailStr


class AuthRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8)


class AuthLogin(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    id: str
    username: str
    email: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthResponse
