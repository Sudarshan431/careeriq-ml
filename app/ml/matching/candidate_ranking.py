"""Ranks a list of candidates against a single job using the hybrid matcher.
Deterministic: identical input always produces identical, stably-ordered output."""
from __future__ import annotations

from app.ml.matching.hybrid import hybrid_match
from app.ml.matching.skill_gap import analyze_skill_gap


def rank_candidates(job: dict, candidates: list[dict]) -> list[dict]:
    ranked = []
    for candidate in candidates:
        result = hybrid_match(candidate, job)
        gap = analyze_skill_gap(
            candidate.get("skills", []), job.get("required_skills", []), job.get("preferred_skills", [])
        )
        ranked.append(
            {
                "candidate_id": candidate.get("candidate_id") or candidate.get("name"),
                "match_score": result["match_score"],
                "semantic_similarity_score": result["semantic_similarity_score"],
                "matched_skills": gap["matched_skills"],
                "missing_skills": gap["critical_missing_skills"],
                "experience_score": result["experience_score"],
            }
        )

    # Sort by score desc; tie-break on candidate_id for determinism.
    ranked.sort(key=lambda r: (-r["match_score"], str(r["candidate_id"])))
    for idx, entry in enumerate(ranked, start=1):
        entry["rank"] = idx
    return ranked
