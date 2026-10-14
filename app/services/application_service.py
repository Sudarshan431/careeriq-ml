"""
Service layer for the job application workflow (Phase 8). Reuses the
existing matching pipeline unchanged (app.services.matching_service) to
compute the application-time match score -- no new ML/NLP logic here.
"""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.auth.models import CurrentUser, Role
from app.core.exceptions import DuplicateApplicationError, ForbiddenError, NotFoundError
from app.core.logging_config import Timer, get_logger
from app.db.models.application import Application
from app.db.repositories.application_repository import ApplicationRepository
from app.db.repositories.candidate_repository import CandidateRepository
from app.db.repositories.job_repository import JobRepository
from app.services.matching_service import calculate_match

logger = get_logger(__name__)


def _to_response_dict(application: Application, job_title: str | None = None, candidate_email: str | None = None) -> dict:
    return {
        "id": application.id,
        "candidate_id": application.candidate_id,
        "job_id": application.job_id,
        "status": application.status,
        "match_score": application.match_score,
        "applied_at": application.applied_at,
        "job_title": job_title,
        "candidate_email": candidate_email,
    }


def apply_to_job(db: Session, candidate_id: uuid.UUID, job_id: uuid.UUID) -> dict:
    """
    Computes (once) and persists the match score at application time using
    the existing, unmodified matching pipeline. Never recomputed on later
    reads -- see ApplicationRepository.create.
    """
    candidate_repo = CandidateRepository(db)
    job_repo = JobRepository(db)
    application_repo = ApplicationRepository(db)

    candidate = candidate_repo.get_by_id(candidate_id)
    if candidate is None:
        raise NotFoundError("Candidate not found.")
    job = job_repo.get_by_id(job_id)
    if job is None:
        raise NotFoundError("Job not found.")

    # Clear, fast-path error for the common case; ApplicationRepository.create's
    # own IntegrityError handling is the real (race-safe) guarantee underneath.
    if application_repo.get_by_candidate_and_job(candidate_id, job_id) is not None:
        raise DuplicateApplicationError()

    with Timer(logger, "application_apply"):
        candidate_input = candidate_repo.to_matching_input(candidate)
        job_input = job_repo.to_matching_input(job)
        match_result = calculate_match(candidate_input, job_input, use_semantic=True)

        application = application_repo.create(
            candidate_id=candidate_id,
            job_id=job_id,
            match_score=match_result["match_score"],
            model_version_id=None,  # populated once model_versions rows are written by training (see MODEL_CARD.md)
        )

    return _to_response_dict(application, job_title=job.title)


def list_my_applications(db: Session, candidate_id: uuid.UUID) -> list[dict]:
    application_repo = ApplicationRepository(db)
    job_repo = JobRepository(db)

    applications = application_repo.list_by_candidate(candidate_id)
    job_title_cache: dict[uuid.UUID, str] = {}
    results = []
    for app_row in applications:
        if app_row.job_id not in job_title_cache:
            job = job_repo.get_by_id(app_row.job_id)
            job_title_cache[app_row.job_id] = job.title if job else "Unknown role"
        results.append(_to_response_dict(app_row, job_title=job_title_cache[app_row.job_id]))
    return results


def _require_job_owner(db: Session, job_id: uuid.UUID, current_user: CurrentUser):
    job = JobRepository(db).get_by_id(job_id)
    if job is None:
        raise NotFoundError("Job not found.")
    if current_user.role != Role.ADMIN and job.recruiter_id != current_user.id:
        raise ForbiddenError("You may only view applications for jobs you own.")
    return job


def list_job_applications(db: Session, job_id: uuid.UUID, current_user: CurrentUser) -> list[dict]:
    _require_job_owner(db, job_id, current_user)

    application_repo = ApplicationRepository(db)
    candidate_repo = CandidateRepository(db)

    applications = application_repo.list_by_job(job_id)
    results = []
    for app_row in applications:
        candidate = candidate_repo.get_by_id(app_row.candidate_id)
        candidate_email = candidate.user.email if candidate and candidate.user else None
        results.append(_to_response_dict(app_row, candidate_email=candidate_email))
    return results


def update_application_status(db: Session, application_id: uuid.UUID, new_status: str, current_user: CurrentUser) -> dict:
    application_repo = ApplicationRepository(db)
    application = application_repo.get_by_id(application_id)
    if application is None:
        raise NotFoundError("Application not found.")

    # Ownership: only the recruiter who owns the job (or ADMIN) may change
    # status -- a candidate, including the applicant themself, never can.
    _require_job_owner(db, application.job_id, current_user)

    updated = application_repo.update_status(application, new_status)
    job = JobRepository(db).get_by_id(updated.job_id)
    return _to_response_dict(updated, job_title=job.title if job else None)
