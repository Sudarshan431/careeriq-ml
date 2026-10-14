"""Service layer for skill-gap analysis: the original raw (candidate_skills vs
required/preferred lists) endpoint, plus a job-centric variant that resolves
the candidate's persisted profile and a persisted job, reusing the exact same
underlying analysis + adds priority classification and a match score."""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.logging_config import get_logger, Timer
from app.db.repositories.candidate_repository import CandidateRepository
from app.db.repositories.job_repository import JobRepository
from app.ml.matching.baseline import baseline_match
from app.ml.matching.skill_gap import analyze_skill_gap
from app.ml.matching.skill_priority import prioritize_skill_gaps

logger = get_logger(__name__)


def get_skill_gap(candidate_skills: list[str], required_skills: list[str], preferred_skills: list[str] | None = None) -> dict:
    with Timer(logger, "skill_gap_analyze"):
        return analyze_skill_gap(candidate_skills, required_skills, preferred_skills)


def _coverage_assessment(coverage_percent: float) -> str:
    if coverage_percent >= 90:
        return "Candidate already covers nearly all required skills for this job."
    if coverage_percent >= 70:
        return "Candidate covers most required skills, with a few notable gaps."
    if coverage_percent >= 40:
        return "Candidate has a partial skill foundation for this job, with significant gaps to close."
    return "Candidate currently covers few of this job's required skills."


def analyze_candidate_job_skill_gap(db: Session, candidate_id: uuid.UUID, job_id: uuid.UUID) -> dict:
    """
    Job-centric skill-gap analysis for a persisted candidate + persisted job.
    Reuses analyze_skill_gap (matching/alias/relationship logic, unchanged)
    and baseline_match (for an overall match_score), then layers priority
    classification on top -- no duplicate skill-matching logic anywhere here.
    """
    candidate_repo = CandidateRepository(db)
    job_repo = JobRepository(db)

    candidate = candidate_repo.get_by_id(candidate_id)
    if candidate is None:
        raise NotFoundError("Candidate not found.")
    job = job_repo.get_by_id(job_id)
    if job is None:
        raise NotFoundError("Job not found.")

    with Timer(logger, "skill_gap_analyze_job_centric"):
        candidate_input = candidate_repo.to_matching_input(candidate)
        job_input = job_repo.to_matching_input(job)

        gap = analyze_skill_gap(candidate_input["skills"], job_input["required_skills"], job_input["preferred_skills"])
        match = baseline_match(candidate_input, job_input)
        priorities = prioritize_skill_gaps(gap)

    partial_matches = [
        {"skill": e["skill"], "related_skills_present": e["related_skills_present"]}
        for e in gap["partially_matched_skills"]
    ]
    missing_skills = gap["critical_missing_skills"] + gap["optional_missing_skills"]

    return {
        "target_job": {
            "job_id": str(job.id),
            "title": job.title,
            "company": job.company,
            "required_skills": job_input["required_skills"],
            "preferred_skills": job_input["preferred_skills"],
        },
        "match_score": match["match_score"],
        "matched_skills": gap["matched_skills"] + gap["matched_preferred_skills"],
        "partial_matches": partial_matches,
        "missing_skills": missing_skills,
        "skill_priorities": priorities,
        "analysis": {
            "skill_coverage_percent": gap["match_coverage_percent"],
            "total_required_skills": len(job_input["required_skills"]),
            "total_matched_required_skills": len(gap["matched_skills"]),
            "critical_gap_count": len(gap["critical_missing_skills"]),
            "assessment": _coverage_assessment(gap["match_coverage_percent"]),
        },
    }
