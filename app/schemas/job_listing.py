from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class JobListingResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    company: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    experience_required: Optional[int] = None
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    jobs: List[JobListingResponse]
