from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class LearningPlanStep(BaseModel):
    skill: str
    priority: str
    difficulty: str
    reason: str
    prerequisite_skills: List[str] = []
    suggested_resource_types: List[str] = []
    recommended_order: int
    is_completed: Optional[bool] = None
    practice_suggestion: Optional[str] = None


class CareerPlanMilestone(BaseModel):
    label: str
    skills: List[str]
    steps: List[LearningPlanStep]


class CareerPlanResponse(BaseModel):
    plan_id: Optional[str] = None
    target_role: str
    target_job_id: Optional[str] = None
    strengths: List[str]
    job_readiness_percent: float
    job_readiness_assessment: Optional[str] = None
    summary: Optional[str] = None
    milestones: List[CareerPlanMilestone]
    learning_items: List[Dict[str, Any]]
    created_at: Optional[datetime] = None


class CareerPlanListResponse(BaseModel):
    plans: List[CareerPlanResponse]
