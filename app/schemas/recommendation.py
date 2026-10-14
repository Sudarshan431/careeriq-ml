from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from app.schemas.matching import CandidateInput, JobInput


class RecommendationRequest(BaseModel):
    candidate: CandidateInput
    jobs: List[JobInput]
    top_k: int = 5
    strategy: str = "hybrid"  # content | semantic | hybrid
    explain: bool = False  # when true, each returned recommendation is enriched with a score
    # breakdown + explanation + skill gap, reusing the existing matching pipeline (see
    # recommendation_service.recommend_jobs) -- computed only for the top_k results actually
    # returned, not the whole job pool, to keep this cheap. Defaults to False so existing
    # callers/response shapes are completely unaffected.


class JobRecommendation(BaseModel):
    job_id: Optional[str]
    title: Optional[str] = None
    score: float
    reason: Optional[str] = None
    explanation: Optional[Dict[str, Any]] = None  # populated only when explain=True
    skill_gap: Optional[Dict[str, Any]] = None  # populated only when explain=True
    score_breakdown: Optional[Dict[str, Any]] = None  # populated only when explain=True


class RecommendationResponse(BaseModel):
    recommendations: List[JobRecommendation]
