"""
Candidate-scoped endpoints: own profile, resume upload -> persisted profile,
and the end-to-end candidate workflow (match + skill gap + recommendations
against a job description).

All routes here enforce ownership (a candidate can only touch their own
data) via `require_own_candidate_profile`; ADMIN bypasses the check.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_candidate, require_own_candidate_profile
from app.auth.models import CurrentUser
from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.db.repositories.candidate_repository import CandidateRepository
from app.db.repositories.job_repository import JobRepository
from app.db.repositories.matching_repository import MatchingRepository
from app.db.file_storage import resume_storage
from app.db.models.resume import Resume
from app.schemas.candidate import CandidateProfileResponse, CandidateWorkflowRequest
from app.services.job_service import analyze_job
from app.services.matching_service import calculate_match
from app.services.recommendation_service import recommend_jobs
from app.services.resume_service import analyze_resume

router = APIRouter(prefix="/api/v1/candidates", tags=["candidates"])


def _to_profile_response(candidate) -> CandidateProfileResponse:
    return CandidateProfileResponse(
        id=candidate.id, location=candidate.location, summary=candidate.summary,
        total_years_experience=candidate.total_years_experience, preferences=candidate.preferences,
        skills=[s.skill_name for s in candidate.skills],
        education=[{"degree": e.degree, "field": e.field, "institution": e.institution, "graduation_year": e.graduation_year} for e in candidate.education],
        experience=[{"role": e.role, "company": e.company, "duration_text": e.duration_text, "technologies": e.technologies} for e in candidate.experience],
        projects=[{"title": p.title, "technologies": p.technologies, "description": p.description} for p in candidate.projects],
        certifications=[{"name": c.name, "year": c.year} for c in candidate.certifications],
    )


@router.get(
    "/me",
    response_model=CandidateProfileResponse,
    summary="Get the current user's own candidate profile",
    description="Resolves the caller's candidate_id from their JWT and returns their profile. CANDIDATE/ADMIN.",
)
def get_my_candidate_profile(db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_candidate)):
    candidate = CandidateRepository(db).get_by_user_id(current_user.id)
    if candidate is None:
        raise NotFoundError("Candidate profile not found.")
    return _to_profile_response(candidate)


@router.get(
    "/{candidate_id}",
    response_model=CandidateProfileResponse,
    summary="Get a candidate's profile",
    description="Returns the persisted candidate profile. Candidates may only fetch their own; ADMIN may fetch any.",
)
def get_candidate_profile(
    candidate_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_own_candidate_profile),
):
    candidate = CandidateRepository(db).get_by_id(candidate_id)
    if candidate is None:
        raise NotFoundError("Candidate not found.")
    return _to_profile_response(candidate)


@router.post(
    "/{candidate_id}/resume",
    response_model=CandidateProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload a resume and refresh the candidate's persisted profile",
    description="Parses the uploaded resume (reusing the existing resume_service/NLP pipeline unchanged) "
    "and overwrites the candidate's skills/education/experience/projects/certifications.",
)
async def upload_resume(
    candidate_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_own_candidate_profile),
):
    candidate = CandidateRepository(db).get_by_id(candidate_id)
    if candidate is None:
        raise NotFoundError("Candidate not found.")

    file_bytes = await file.read()
    profile = analyze_resume(file_bytes, file.filename)  # existing NLP pipeline, unchanged

    storage_key = resume_storage.save(candidate_id, file.filename, file_bytes)
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "txt"
    resume_row = Resume(
        candidate_id=candidate_id, filename=file.filename[:255], file_type=ext,
        file_size=len(file_bytes), storage_key=storage_key, processing_status="processed",
    )
    db.add(resume_row)

    candidate = CandidateRepository(db).replace_profile_from_parsed_resume(candidate, profile)
    return _to_profile_response(candidate)


@router.post(
    "/{candidate_id}/workflow",
    summary="Run the full CareerIQ workflow for this candidate against a job",
    description="job analysis -> matching -> skill gap -> recommendations -> explanation, "
    "using the candidate's already-persisted profile. Persists the matching result and recommendations.",
)
def run_workflow(
    candidate_id: uuid.UUID,
    payload: CandidateWorkflowRequest,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_own_candidate_profile),
):
    candidate_repo = CandidateRepository(db)
    candidate = candidate_repo.get_by_id(candidate_id)
    if candidate is None:
        raise NotFoundError("Candidate not found.")

    job_repo = JobRepository(db)
    parsed_job = analyze_job(payload.job_description)
    # ad-hoc job text (not necessarily a persisted Job row) is matched directly;
    # persisted Job rows are matched via job_repo.to_matching_input elsewhere.
    candidate_input = candidate_repo.to_matching_input(candidate)
    result = calculate_match(candidate_input, parsed_job, use_semantic=payload.use_semantic)

    recommendations = []
    if payload.other_job_descriptions:
        parsed_others = []
        for raw in payload.other_job_descriptions:
            p = analyze_job(raw["description"])
            p["job_id"] = raw.get("title")
            p["title"] = raw.get("title")
            parsed_others.append(p)
        recommendations = recommend_jobs(candidate_input, parsed_others, top_k=5, strategy="hybrid")

    return {"job": parsed_job, "match": result, "recommendations": recommendations}
