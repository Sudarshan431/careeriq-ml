from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel


class JobAnalyzeRequest(BaseModel):
    description: str


class JobRequirements(BaseModel):
    title: Optional[str] = None
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    experience_required: Optional[int] = None
    education: List[str] = []
    location: Optional[str] = None
    employment_type: Optional[str] = None
    responsibilities: List[str] = []


class JobAnalyzeResponse(BaseModel):
    job: JobRequirements
