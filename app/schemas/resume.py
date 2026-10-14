from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


class EducationEntry(BaseModel):
    degree: Optional[str] = None
    field: Optional[str] = None
    institution: Optional[str] = None
    graduation_year: Optional[str] = None


class ExperienceEntry(BaseModel):
    role: Optional[str] = None
    company: Optional[str] = None
    duration_text: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)


class ProjectEntry(BaseModel):
    title: str
    technologies: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class CertificationEntry(BaseModel):
    name: str
    year: Optional[str] = None


class ResumeProfile(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    education: List[EducationEntry] = Field(default_factory=list)
    experience: List[ExperienceEntry] = Field(default_factory=list)
    total_years_experience: Optional[float] = None
    projects: List[ProjectEntry] = Field(default_factory=list)
    certifications: List[CertificationEntry] = Field(default_factory=list)
    sections_detected: List[str] = Field(default_factory=list)


class ResumeAnalyzeResponse(BaseModel):
    profile: ResumeProfile
