"""
Persisted job listing/detail endpoints. Added for frontend integration:
JobRepository.list_all()/get_by_id() already existed but were never exposed
via an endpoint, so there was no way to browse or view persisted jobs.
Read-only, reuses the existing repository -- no new business logic.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_authenticated, require_candidate, require_recruiter
from app.auth.models import CurrentUser
from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.db.repositories.candidate_repository import CandidateRepository
from app.db.repositories.job_repository import JobRepository
from app.schemas.application import ApplicationListResponse, ApplicationResponse
from app.schemas.job_listing import JobListingResponse, JobListResponse
from app.services.application_service import apply_to_job, list_job_applications

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


def _to_listing(job) -> dict:
    return {
        "id": job.id,
        "title": job.title,
        "description": job.description,
        "company": job.company,
        "location": job.location,
        "employment_type": job.employment_type,
        "experience_required": job.experience_required,
        "required_skills": [s.skill_name for s in job.skills if s.requirement_type == "required"],
        "preferred_skills": [s.skill_name for s in job.skills if s.requirement_type == "preferred"],
        "created_at": job.created_at,
    }


@router.get("", response_model=JobListResponse, summary="List persisted jobs")
def list_jobs(limit: int = 100, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_authenticated)):
    jobs = JobRepository(db).list_all(limit=limit)
    return {"jobs": [_to_listing(j) for j in jobs]}


@router.get("/{job_id}", response_model=JobListingResponse, summary="Get a persisted job by id")
def get_job(job_id: uuid.UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_authenticated)):
    job = JobRepository(db).get_by_id(job_id)
    if job is None:
        raise NotFoundError("Job not found.")
    return _to_listing(job)


@router.post(
    "/{job_id}/apply",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply to a job as the current candidate",
    description="Computes and persists the match score at application time using the existing matching "
    "pipeline. A candidate may only apply as themselves and cannot apply to the same job twice. CANDIDATE/ADMIN only.",
    responses={409: {"description": "Already applied to this job"}, 404: {"description": "Job not found"}},
)
def apply_to_job_endpoint(job_id: uuid.UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_candidate)):
    candidate = CandidateRepository(db).get_by_user_id(current_user.id)
    if candidate is None:
        raise NotFoundError("Candidate profile not found.")
    return apply_to_job(db, candidate.id, job_id)


@router.get(
    "/{job_id}/applications",
    response_model=ApplicationListResponse,
    summary="List applicants for a job",
    description="Returns applications for this job, each including the match score captured at application "
    "time. Restricted to the recruiter who owns the job, or ADMIN.",
    responses={403: {"description": "Not the owner of this job"}, 404: {"description": "Job not found"}},
)
def list_job_applications_endpoint(job_id: uuid.UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_recruiter)):
    return {"applications": list_job_applications(db, job_id, current_user)}
