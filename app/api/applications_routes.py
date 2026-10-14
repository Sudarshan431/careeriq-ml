"""Application-centric endpoints not scoped under a specific job: a candidate's own
application list, and status updates by the owning recruiter."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_candidate, require_recruiter
from app.auth.models import CurrentUser
from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.db.repositories.candidate_repository import CandidateRepository
from app.schemas.application import ApplicationListResponse, ApplicationResponse, ApplicationStatusUpdateRequest
from app.services.application_service import list_my_applications, update_application_status

router = APIRouter(prefix="/api/v1/applications", tags=["applications"])


@router.get(
    "/me",
    response_model=ApplicationListResponse,
    summary="List the current candidate's own applications",
    description="Resolves the caller's candidate_id from their JWT -- a candidate can never list "
    "another candidate's applications. CANDIDATE/ADMIN only.",
)
def list_my_applications_endpoint(db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_candidate)):
    candidate = CandidateRepository(db).get_by_user_id(current_user.id)
    if candidate is None:
        raise NotFoundError("Candidate profile not found.")
    return {"applications": list_my_applications(db, candidate.id)}


@router.patch(
    "/{application_id}/status",
    response_model=ApplicationResponse,
    summary="Update an application's status",
    description="Restricted to the recruiter who owns the job this application is for, or ADMIN. "
    "A candidate (including the applicant) can never change application status.",
    responses={403: {"description": "Not the owner of this job"}, 404: {"description": "Application not found"}},
)
def update_application_status_endpoint(
    application_id: uuid.UUID,
    payload: ApplicationStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_recruiter),
):
    return update_application_status(db, application_id, payload.status, current_user)
