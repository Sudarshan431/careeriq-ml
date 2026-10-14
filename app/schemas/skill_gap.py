from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class SkillGapRequest(BaseModel):
    candidate_skills: List[str]
    required_skills: List[str]
    preferred_skills: Optional[List[str]] = None


class SkillGapResponse(BaseModel):
    matched_skills: List[str]
    matched_preferred_skills: List[str]
    partially_matched_skills: List[Dict[str, Any]]
    critical_missing_skills: List[str]
    optional_missing_skills: List[str]
    match_coverage_percent: float


class TargetJobSummary(BaseModel):
    job_id: str
    title: str
    company: Optional[str] = None
    required_skills: List[str]
    preferred_skills: List[str]


class SkillPriorityItem(BaseModel):
    skill: str
    priority: str  # HIGH | MEDIUM | LOW
    reason: str
    related_skills_present: List[str] = []


class SkillGapAnalysisSummary(BaseModel):
    skill_coverage_percent: float
    total_required_skills: int
    total_matched_required_skills: int
    critical_gap_count: int
    assessment: str


class JobSkillGapResponse(BaseModel):
    target_job: TargetJobSummary
    match_score: float
    matched_skills: List[str]
    partial_matches: List[Dict[str, Any]]
    missing_skills: List[str]
    skill_priorities: List[SkillPriorityItem]
    analysis: SkillGapAnalysisSummary
