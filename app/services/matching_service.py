"""Service layer for matching: baseline, hybrid, explanation, candidate ranking."""
from __future__ import annotations

from app.core.logging_config import get_logger, Timer
from app.ml.matching.baseline import baseline_match
from app.ml.matching.hybrid import hybrid_match
from app.ml.matching.explanation import explain_match
from app.ml.matching.skill_gap import analyze_skill_gap
from app.ml.matching.candidate_ranking import rank_candidates

logger = get_logger(__name__)


def calculate_match(candidate: dict, job: dict, use_semantic: bool = True) -> dict:
    with Timer(logger, "matching_calculate"):
        result = hybrid_match(candidate, job) if use_semantic else baseline_match(candidate, job)
        gap = analyze_skill_gap(
            candidate.get("skills", []), job.get("required_skills", []), job.get("preferred_skills", [])
        )
        explanation = explain_match(
            result,
            matched_skills=gap["matched_skills"],
            missing_skills=gap["critical_missing_skills"],
            experience_score=result.get("experience_score"),
        )
    return {**result, "explanation": explanation, "skill_gap": gap}


def rank_candidates_for_job(job: dict, candidates: list[dict]) -> list[dict]:
    with Timer(logger, "matching_rank_candidates"):
        return rank_candidates(job, candidates)
