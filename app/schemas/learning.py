from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel


class LearningRecommendationItem(BaseModel):
    skill: str
    priority: str  # HIGH | MEDIUM | LOW
    reason: str
    related_skills_present: List[str] = []
    prerequisite_skills: List[str] = []
    difficulty: str  # FOUNDATIONAL | STANDARD | FOCUSED
    recommended_order: int
    suggested_resource_types: List[str] = []


class LearningRecommendationsResponse(BaseModel):
    target_job_id: Optional[str] = None
    target_job_title: Optional[str] = None
    recommendations: List[LearningRecommendationItem]
