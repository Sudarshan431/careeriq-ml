"""Learning recommendation endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_authenticated, require_own_candidate_profile
from app.auth.models import CurrentUser
from app.db.session import get_db
from app.schemas.learning import LearningRecommendationsResponse
from app.schemas.skill_gap import SkillGapRequest
from app.services.learning_service import get_learning_recommendations_for_job, get_learning_recommendations_for_skills

router = APIRouter(prefix="/api/v1/learning", tags=["learning"])


@router.get(
    "/candidates/{candidate_id}/jobs/{job_id}/recommendations",
    response_model=LearningRecommendationsResponse,
    summary="Get prioritized, dependency-ordered learning recommendations for a candidate targeting a specific job",
    description="Built on the same skill-gap analysis used elsewhere -- HIGH/MEDIUM/LOW priority, ordered so "
    "prerequisite skills come first. Candidate may only request their own; ADMIN may request any.",
)
def learning_recommendations_for_job_endpoint(
    candidate_id: uuid.UUID,
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_own_candidate_profile),
):
    return get_learning_recommendations_for_job(db, candidate_id, job_id)


@router.post(
    "/recommendations",
    response_model=LearningRecommendationsResponse,
    summary="Get learning recommendations for a candidate targeting an arbitrary skill set (broader career target)",
    description="Same engine as the job-specific endpoint, but takes a raw target skill list instead of a "
    "persisted job -- useful for a broader career/role target rather than one specific posting.",
)
def learning_recommendations_for_skills_endpoint(payload: SkillGapRequest, current_user: CurrentUser = Depends(require_authenticated)):
    return get_learning_recommendations_for_skills(payload.candidate_skills, payload.required_skills, payload.preferred_skills)
