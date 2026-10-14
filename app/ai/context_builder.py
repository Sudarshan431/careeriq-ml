"""
Structured context builder for the AI Career Assistant.

Architecture (per spec): CareerIQ DB / ML services -> structured context ->
LLM -> natural-language answer. This module is the "structured context"
step -- it ONLY reads from the existing, already-tested services
(skill_gap logic, matching logic, and the repositories directly for
profile facts). It never calls the LLM and the LLM never influences what
goes in here. This is what prevents the assistant from hallucinating
candidate facts: everything the model is told about the candidate/job
came from here, not from the model's own "knowledge" or from unvalidated
user input.

Only structured, already-extracted fields are included -- never the raw
resume text or raw job description body -- both to keep the prompt small
and because raw free text is the injection surface the security section
warns about (a resume/job description is untrusted content; skills
already extracted from it are not, since they went through the existing,
tested extraction pipeline).

RAG addition: `retrieved_knowledge` is populated via app.rag (semantic
search over indexed job descriptions, scoped to what this candidate is
authorized to see -- retrieval-time authorization, not just filtering
after the fact; see SimpleVectorRetriever.search). This is strictly
additive: if the retrieval backend is unavailable or errors for any
reason, `retrieved_knowledge` is simply an empty list and everything else
in this function proceeds exactly as before -- the assistant keeps working
without RAG, per the requirement to preserve the existing non-RAG
assistant as a fallback.
"""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.logging_config import get_logger
from app.db.repositories.candidate_repository import CandidateRepository
from app.db.repositories.job_repository import JobRepository
from app.ml.matching.baseline import baseline_match
from app.ml.matching.skill_gap import analyze_skill_gap
from app.rag.context_retrieval import retrieve_knowledge

logger = get_logger(__name__)


def build_context(db: Session, candidate_id: uuid.UUID, job_id: uuid.UUID | None, user_question: str | None = None) -> dict:
    """
    Returns a plain dict of structured facts -- this is exactly what's
    also returned to the client as the API response's `context` field, so
    the assistant's answer and the ground-truth data the frontend can
    display directly are always the same data, never two different
    sources of truth.
    """
    candidate_repo = CandidateRepository(db)
    candidate = candidate_repo.get_by_id(candidate_id)
    if candidate is None:
        raise NotFoundError("Candidate not found.")

    candidate_input = candidate_repo.to_matching_input(candidate)
    context: dict = {
        "candidate_skills": candidate_input["skills"],
        "candidate_experience_years": candidate_input["experience_years"],
        "candidate_education": [
            f"{e.get('degree') or ''} {e.get('field') or ''}".strip() for e in candidate_input["education"]
        ],
    }

    if job_id is not None:
        job_repo = JobRepository(db)
        job = job_repo.get_by_id(job_id)
        if job is None:
            raise NotFoundError("Job not found.")
        job_input = job_repo.to_matching_input(job)

        gap = analyze_skill_gap(candidate_input["skills"], job_input["required_skills"], job_input["preferred_skills"])
        match = baseline_match(candidate_input, job_input)

        context.update(
            {
                "target_job_id": str(job.id),
                "target_job_title": job.title,
                "target_job_required_skills": job_input["required_skills"],
                "target_job_preferred_skills": job_input["preferred_skills"],
                "match_score": match["match_score"],
                "matched_skills": gap["matched_skills"] + gap["matched_preferred_skills"],
                "missing_skills": gap["critical_missing_skills"] + gap["optional_missing_skills"],
                "critical_missing_skills": gap["critical_missing_skills"],
                "skill_coverage_percent": gap["match_coverage_percent"],
            }
        )

    # Additive, best-effort: never raises, never blocks the non-RAG context above.
    query = user_question or context.get("target_job_title") or " ".join(context.get("candidate_skills", []))
    context["retrieved_knowledge"] = retrieve_knowledge(db, query, candidate_id) if query else []

    return context
