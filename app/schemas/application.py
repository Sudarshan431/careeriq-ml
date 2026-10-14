from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from app.db.models.application import APPLICATION_STATUSES


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    status: str
    match_score: Optional[float] = None
    applied_at: datetime

    # Denormalized display fields, populated by the service layer from the
    # related Job/Candidate rows -- kept optional since not every caller
    # needs them (e.g. a bare status-update response).
    job_title: Optional[str] = None
    candidate_email: Optional[str] = None

    class Config:
        from_attributes = True


class ApplicationListResponse(BaseModel):
    applications: list[ApplicationResponse]


class ApplicationStatusUpdateRequest(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        normalized = v.strip().upper()
        if normalized not in APPLICATION_STATUSES:
            raise ValueError(f"status must be one of: {', '.join(APPLICATION_STATUSES)}")
        return normalized
