from __future__ import annotations

import re
import uuid

from pydantic import BaseModel, EmailStr, field_validator

from app.auth.models import Role

_PASSWORD_MIN_LENGTH = 8


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: Role = Role.CANDIDATE  # RECRUITER may self-register; ADMIN must be provisioned separately (see auth_service)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < _PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password must be at least {_PASSWORD_MIN_LENGTH} characters.")
        if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
            raise ValueError("Password must contain both letters and numbers.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: Role
    is_active: bool

    class Config:
        from_attributes = True
