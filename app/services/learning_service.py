"""Service layer for learning recommendations. Built entirely on top of the
existing skill-gap analysis (app.ml.matching.skill_gap) -- no duplicate
skill-matching logic."""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.logging_config import get_logger, Timer
from app.db.repositories.candidate_repository import CandidateRepository
from app.db.repositories.job_repository import JobRepository
from app.ml.matching.skill_gap import analyze_skill_gap
from app.ml.learning.learning_recommender import build_learning_recommendations

logger = get_logger(__name__)


def get_learning_recommendations_for_job(db: Session, candidate_id: uuid.UUID, job_id: uuid.UUID) -> dict:
    candidate_repo = CandidateRepository(db)
    job_repo = JobRepository(db)

    candidate = candidate_repo.get_by_id(candidate_id)
    if candidate is None:
        raise NotFoundError("Candidate not found.")
    job = job_repo.get_by_id(job_id)
    if job is None:
        raise NotFoundError("Job not found.")

    with Timer(logger, "learning_recommendations_for_job"):
        candidate_input = candidate_repo.to_matching_input(candidate)
        job_input = job_repo.to_matching_input(job)
        gap = analyze_skill_gap(candidate_input["skills"], job_input["required_skills"], job_input["preferred_skills"])
        recommendations = build_learning_recommendations(candidate_input["skills"], gap)

    return {"target_job_id": str(job.id), "target_job_title": job.title, "recommendations": recommendations}


def get_learning_recommendations_for_skills(candidate_skills: list[str], required_skills: list[str], preferred_skills: list[str] | None = None) -> dict:
    """
    Career-level variant: no persisted job needed, just a target skill set
    (e.g. a broader role/career target described by its typical required
    skills) -- reuses the exact same underlying logic.
    """
    with Timer(logger, "learning_recommendations_for_skills"):
        gap = analyze_skill_gap(candidate_skills, required_skills, preferred_skills)
        recommendations = build_learning_recommendations(candidate_skills, gap)
    return {"target_job_id": None, "target_job_title": None, "recommendations": recommendations}
