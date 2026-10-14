"""Candidate-job matching and candidate ranking endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.auth.dependencies import require_authenticated, require_recruiter
from app.auth.models import CurrentUser
from app.schemas.matching import MatchRequest, MatchResponse, RankCandidatesRequest, RankCandidatesResponse
from app.services.matching_service import calculate_match, rank_candidates_for_job

router = APIRouter(prefix="/api/v1/matching", tags=["matching"])


@router.post(
    "/calculate",
    response_model=MatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate a candidate-job match score",
    description="Returns overall/skill/semantic/experience/education scores plus an "
    "evidence-based explanation and skill-gap breakdown. Any authenticated user.",
)
def calculate_match_endpoint(payload: MatchRequest, current_user: CurrentUser = Depends(require_authenticated)):
    return calculate_match(payload.candidate.model_dump(), payload.job.model_dump(), payload.use_semantic)


@router.post(
    "/rank-candidates",
    response_model=RankCandidatesResponse,
    status_code=status.HTTP_200_OK,
    summary="Rank multiple candidates against a single job",
    description="Deterministic ranking of candidates for a job using the hybrid matcher. "
    "Restricted to RECRUITER and ADMIN roles.",
)
def rank_candidates_endpoint(payload: RankCandidatesRequest, current_user: CurrentUser = Depends(require_recruiter)):
    candidates = [c.model_dump() for c in payload.candidates]
    ranked = rank_candidates_for_job(payload.job.model_dump(), candidates)
    return {"ranked_candidates": ranked}
