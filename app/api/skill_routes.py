"""Standalone skill-gap analysis endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.auth.dependencies import require_authenticated
from app.auth.models import CurrentUser
from app.schemas.skill_gap import SkillGapRequest, SkillGapResponse
from app.services.skill_gap_service import get_skill_gap

router = APIRouter(prefix="/api/v1/skills", tags=["skills"])


@router.post(
    "/gap",
    response_model=SkillGapResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze the skill gap between a candidate and a job",
    description="Classifies job-required skills into matched / partially matched (related "
    "skill present) / critical missing / optional missing. Any authenticated user.",
)
def skill_gap_endpoint(payload: SkillGapRequest, current_user: CurrentUser = Depends(require_authenticated)):
    return get_skill_gap(payload.candidate_skills, payload.required_skills, payload.preferred_skills)
