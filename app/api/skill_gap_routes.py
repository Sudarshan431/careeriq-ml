"""
Job-centric skill-gap analysis endpoint (candidate + persisted job ->
structured comparison with priorities). Distinct from the existing raw
`POST /api/v1/skills/gap` (app/api/skill_routes.py, unchanged, still takes
plain skill lists) -- this one resolves real candidate/job records and adds
an overall match score + prioritized gap list on top of the same
underlying analyze_skill_gap logic.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_own_candidate_profile
from app.auth.models import CurrentUser
from app.db.session import get_db
from app.db.repositories.candidate_repository import CandidateRepository
from app.core.exceptions import NotFoundError
from app.schemas.skill_gap import JobSkillGapResponse
from app.services.skill_gap_service import analyze_candidate_job_skill_gap

router = APIRouter(prefix="/api/v1/skill-gaps", tags=["skill-gaps"])


@router.get(
    "/candidates/{candidate_id}/jobs/{job_id}",
    response_model=JobSkillGapResponse,
    summary="Analyze a candidate's skill gap against a specific persisted job",
    description="Matched / partially-matched (via taxonomy relationships) / missing skills, each missing skill "
    "prioritized HIGH/MEDIUM/LOW, plus an overall match score. Candidate may only analyze their own profile; ADMIN may analyze any.",
)
def job_skill_gap_endpoint(
    candidate_id: uuid.UUID,
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_own_candidate_profile),
):
    return analyze_candidate_job_skill_gap(db, candidate_id, job_id)
