"""Service layer for job recommendations."""
from __future__ import annotations

from app.core.logging_config import get_logger, Timer
from app.ml.recommendation.content_based import recommend_jobs_content_based, recommend_jobs_semantic
from app.services.matching_service import calculate_match

logger = get_logger(__name__)

_SCORE_BREAKDOWN_KEYS = ("skill_score", "semantic_similarity_score", "experience_score", "education_score")


def _enrich_with_explanations(candidate: dict, jobs: list[dict], recommendations: list[dict]) -> list[dict]:
    """
    Adds explanation/skill_gap/score_breakdown to each recommendation by
    reusing the existing matching pipeline (app.services.matching_service),
    computed only for the jobs actually being returned -- not the whole
    pool -- so this stays cheap even for a large candidate job list.
    """
    jobs_by_id = {(j.get("job_id") or j.get("title")): j for j in jobs}
    enriched = []
    for rec in recommendations:
        job = jobs_by_id.get(rec.get("job_id"))
        if job is None:
            enriched.append(rec)
            continue
        match_result = calculate_match(candidate, job, use_semantic=True)
        rec = {
            **rec,
            "explanation": match_result.get("explanation"),
            "skill_gap": match_result.get("skill_gap"),
            "score_breakdown": {k: match_result.get(k) for k in _SCORE_BREAKDOWN_KEYS if k in match_result},
        }
        enriched.append(rec)
    return enriched


def recommend_jobs(candidate: dict, jobs: list[dict], top_k: int = 5, strategy: str = "hybrid", explain: bool = False) -> list[dict]:
    with Timer(logger, f"recommendation_{strategy}"):
        if strategy == "content":
            results = recommend_jobs_content_based(candidate, jobs, top_k)
        elif strategy == "semantic":
            results = recommend_jobs_semantic(candidate, jobs, top_k)
        else:
            # hybrid: blend content-based and semantic rank by averaging scores
            content = {r["job_id"]: r["score"] for r in recommend_jobs_content_based(candidate, jobs, top_k=len(jobs))}
            semantic = {r["job_id"]: r["score"] for r in recommend_jobs_semantic(candidate, jobs, top_k=len(jobs))}
            blended = []
            for job in jobs:
                jid = job.get("job_id") or job.get("title")
                score = 0.5 * content.get(jid, 0.0) + 0.5 * semantic.get(jid, 0.0)
                blended.append({"job_id": jid, "title": job.get("title"), "score": round(score, 4)})
            blended.sort(key=lambda r: (-r["score"], r["job_id"] or ""))
            results = blended[:top_k]

        if explain:
            results = _enrich_with_explanations(candidate, jobs, results)
        return results
