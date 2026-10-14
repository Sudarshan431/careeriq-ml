"""Recruiter-scoped endpoints: create jobs, rank candidates against a job."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_recruiter
from app.auth.models import CurrentUser
from app.core.exceptions import NotFoundError
from app.core.logging_config import get_logger
from app.db.session import get_db
from app.db.repositories.candidate_repository import CandidateRepository
from app.db.repositories.job_repository import JobRepository
from app.rag.ingestion import index_job_description
from app.schemas.job import JobAnalyzeRequest
from app.schemas.matching import CandidateInput
from app.services.job_service import analyze_job
from app.services.matching_service import rank_candidates_for_job

router = APIRouter(prefix="/api/v1/recruiter", tags=["recruiter"])
logger = get_logger(__name__)


@router.get(
    "/candidates",
    summary="List candidate profiles available for ranking",
    description="Read-only listing of persisted candidate profiles, shaped for use as "
    "matching/ranking input. RECRUITER/ADMIN only.",
)
def list_candidates(limit: int = 100, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_recruiter)):
    repo = CandidateRepository(db)
    candidates = repo.list_all(limit=limit)
    return {"candidates": [repo.to_matching_input(c) for c in candidates]}


@router.post(
    "/jobs",
    status_code=status.HTTP_201_CREATED,
    summary="Create and persist a job posting from a raw description",
    description="Parses the description with the existing job_parser and persists the job + its skills. RECRUITER/ADMIN only.",
)
def create_job(payload: JobAnalyzeRequest, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_recruiter)):
    parsed = analyze_job(payload.description)
    job = JobRepository(db).create_from_parsed_job(current_user.id, payload.description, parsed)
    try:
        index_job_description(db, job)
    except Exception as e:
        # RAG indexing is additive -- a failure here (e.g. embedding backend
        # unavailable) must never prevent the job itself from being created.
        # The existing non-RAG assistant/matching/recommendation flows don't
        # depend on this at all.
        logger.warning("rag_ingest_failed job_id=%s error=%s: %s", job.id, type(e).__name__, e)
    return {"job_id": str(job.id), "parsed": parsed}


@router.post(
    "/jobs/{job_id}/rank-candidates",
    summary="Rank a list of candidates against a persisted job",
    description="Deterministic ranking using the existing hybrid matcher. RECRUITER/ADMIN only.",
)
def rank_candidates_for_persisted_job(
    job_id: uuid.UUID,
    candidates: list[CandidateInput],
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_recruiter),
):
    job = JobRepository(db).get_by_id(job_id)
    if job is None:
        raise NotFoundError("Job not found.")
    job_input = JobRepository(db).to_matching_input(job)
    ranked = rank_candidates_for_job(job_input, [c.model_dump() for c in candidates])
    return {"ranked_candidates": ranked}
