"""
Hybrid matching: combines explicit skill overlap, semantic similarity
(candidate summary/profile text vs. job description), experience
compatibility, and education compatibility into one configurable score.
"""
from __future__ import annotations

from app.core.config import settings
from app.ml.embeddings.embedding_service import semantic_similarity, embedding_backend
from app.ml.features.feature_builder import (
    skill_overlap_ratio,
    experience_compatibility,
    education_compatibility,
)


def hybrid_match(candidate: dict, job: dict) -> dict:
    """
    candidate: {skills, experience_years, education, summary/profile_text}
    job: {required_skills, preferred_skills, experience_required, education, description}
    """
    required = job.get("required_skills", [])
    preferred = job.get("preferred_skills", [])
    all_job_skills = list(dict.fromkeys(required + preferred))

    skill_score = skill_overlap_ratio(candidate.get("skills", []), all_job_skills)
    experience_score = experience_compatibility(candidate.get("experience_years"), job.get("experience_required"))
    education_score = education_compatibility(candidate.get("education", []), job.get("education", []))

    candidate_text = candidate.get("profile_text") or candidate.get("summary") or " ".join(candidate.get("skills", []))
    job_text = job.get("description") or " ".join(all_job_skills)
    semantic_score = semantic_similarity(candidate_text, job_text)

    weights = {
        "skill": settings.hybrid_skill_weight,
        "semantic": settings.hybrid_semantic_weight,
        "experience": settings.hybrid_experience_weight,
        "education": settings.hybrid_education_weight,
    }
    weight_sum = sum(weights.values()) or 1.0

    overall = (
        skill_score * weights["skill"]
        + semantic_score * weights["semantic"]
        + experience_score * weights["experience"]
        + education_score * weights["education"]
    ) / weight_sum

    return {
        "match_score": round(overall * 100, 1),
        "skill_score": round(skill_score * 100, 1),
        "semantic_similarity_score": round(semantic_score * 100, 1),
        "experience_score": round(experience_score * 100, 1),
        "education_score": round(education_score * 100, 1),
        "weights_used": weights,
        "embedding_backend": embedding_backend(),
    }
