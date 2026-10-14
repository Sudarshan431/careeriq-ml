"""Personalized career/learning plan endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_authenticated, require_own_candidate_profile
from app.auth.models import CurrentUser, Role
from app.core.exceptions import ForbiddenError, NotFoundError
from app.db.session import get_db
from app.db.repositories.candidate_repository import CandidateRepository
from app.db.repositories.learning_plan_repository import LearningPlanRepository
from app.schemas.career_plan import CareerPlanListResponse, CareerPlanResponse
from app.services.career_plan_service import generate_plan_for_job, get_plan, list_plans_for_candidate

router = APIRouter(prefix="/api/v1/career-plans", tags=["career-plans"])


@router.post(
    "/candidates/{candidate_id}/jobs/{job_id}",
    response_model=CareerPlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate and persist a personalized career/learning plan toward a specific job",
    description="Combines the existing skill-gap and learning-recommendation engines into an ordered, "
    "milestone-grouped plan with a job-readiness assessment. Candidate may only generate their own; ADMIN may generate any.",
)
def generate_career_plan_endpoint(
    candidate_id: uuid.UUID,
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_own_candidate_profile),
):
    return generate_plan_for_job(db, candidate_id, job_id)


@router.get(
    "/candidates/{candidate_id}",
    response_model=CareerPlanListResponse,
    summary="List a candidate's saved career plans",
)
def list_career_plans_endpoint(
    candidate_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_own_candidate_profile),
):
    return {"plans": list_plans_for_candidate(db, candidate_id)}


@router.get(
    "/{plan_id}",
    response_model=CareerPlanResponse,
    summary="Get a single saved career plan",
    description="A plan is reachable only by its own opaque id, so ownership is checked against the plan's "
    "own candidate_id here rather than a path candidate_id -- the candidate who owns it, or ADMIN.",
)
def get_career_plan_endpoint(plan_id: uuid.UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_authenticated)):
    plan_repo = LearningPlanRepository(db)
    plan_row = plan_repo.get_by_id(plan_id)
    if plan_row is None:
        raise NotFoundError("Career plan not found.")

    if current_user.role != Role.ADMIN:
        candidate = CandidateRepository(db).get_by_user_id(current_user.id)
        if candidate is None or plan_row.candidate_id != candidate.id:
            raise ForbiddenError("You may only view your own career plans.")

    return get_plan(db, plan_id)
