"""Shared auth types: roles and the lightweight CurrentUser used by route dependencies."""
from __future__ import annotations

import enum
import uuid

from pydantic import BaseModel


class Role(str, enum.Enum):
    CANDIDATE = "CANDIDATE"
    RECRUITER = "RECRUITER"
    ADMIN = "ADMIN"


class CurrentUser(BaseModel):
    """
    The authenticated principal for the current request, built from the JWT
    claims (and, in the DB-backed path, cross-checked against the `users`
    table for `is_active`). Never includes the password hash.
    """

    id: uuid.UUID
    email: str
    role: Role
    is_active: bool = True

    class Config:
        use_enum_values = False
