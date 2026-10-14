"""Job description analysis endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.auth.dependencies import require_authenticated
from app.auth.models import CurrentUser
from app.schemas.job import JobAnalyzeRequest, JobAnalyzeResponse
from app.services.job_service import analyze_job

router = APIRouter(prefix="/api/v1/job", tags=["job"])


@router.post(
    "/analyze",
    response_model=JobAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse a raw job description into structured requirements",
    description="Converts free-text job description into required/preferred skills, "
    "experience, education, location, and responsibilities. Requires any authenticated user.",
    responses={422: {"description": "Empty job description"}},
)
def analyze_job_endpoint(payload: JobAnalyzeRequest, current_user: CurrentUser = Depends(require_authenticated)):
    job = analyze_job(payload.description)
    return {"job": job}
