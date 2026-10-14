from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class CandidateInput(BaseModel):
    candidate_id: Optional[str] = None
    skills: List[str] = []
    experience_years: Optional[float] = None
    education: List[Dict[str, Any]] = []
    location: Optional[str] = None
    summary: Optional[str] = None
    profile_text: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class JobInput(BaseModel):
    job_id: Optional[str] = None
    title: Optional[str] = None
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    experience_required: Optional[int] = None
    education: List[str] = []
    location: Optional[str] = None
    employment_type: Optional[str] = None
    description: Optional[str] = None


class MatchRequest(BaseModel):
    candidate: CandidateInput
    job: JobInput
    use_semantic: bool = True


class MatchExplanation(BaseModel):
    match_score: float
    strengths: List[str]
    matched_skills: List[str]
    missing_skills: List[str]
    experience_analysis: str
    recommendation: str


class MatchResponse(BaseModel):
    match_score: float
    skill_score: float
    semantic_similarity_score: Optional[float] = None
    experience_score: float
    education_score: float
    location_score: Optional[float] = None
    preference_score: Optional[float] = None
    embedding_backend: Optional[str] = None
    explanation: MatchExplanation
    skill_gap: Dict[str, Any]


class RankCandidatesRequest(BaseModel):
    job: JobInput
    candidates: List[CandidateInput]


class RankedCandidate(BaseModel):
    rank: int
    candidate_id: Optional[str]
    match_score: float
    semantic_similarity_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    experience_score: float


class RankCandidatesResponse(BaseModel):
    ranked_candidates: List[RankedCandidate]
