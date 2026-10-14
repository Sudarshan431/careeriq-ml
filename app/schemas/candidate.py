from __future__ import annotations

import uuid
from typing import Any, Optional

from pydantic import BaseModel

from app.schemas.resume import ResumeProfile


class CandidateProfileResponse(BaseModel):
    id: uuid.UUID
    location: Optional[str] = None
    summary: Optional[str] = None
    total_years_experience: Optional[float] = None
    preferences: Optional[dict[str, Any]] = None
    skills: list[str] = []
    education: list[dict] = []
    experience: list[dict] = []
    projects: list[dict] = []
    certifications: list[dict] = []


class CandidateWorkflowRequest(BaseModel):
    """Runs the full candidate journey: uses the candidate's persisted profile
    (already built from a prior resume upload) against a target job description."""
    job_description: str
    other_job_descriptions: Optional[list[dict]] = None  # [{"title": str, "description": str}, ...]
    use_semantic: bool = True
