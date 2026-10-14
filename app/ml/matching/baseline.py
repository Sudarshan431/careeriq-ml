"""
Baseline (fully transparent, no-ML) matching engine. Weights are pulled
from app.core.config so they're configurable via environment variables
rather than hardcoded here.
"""
from __future__ import annotations

from app.core.config import settings
from app.ml.features.feature_builder import (
    skill_overlap_ratio,
    experience_compatibility,
    education_compatibility,
    location_compatibility,
    preference_compatibility,
)


def baseline_match(candidate: dict, job: dict) -> dict:
    """
    candidate: {skills, experience_years, education, location, preferences}
    job: {required_skills, preferred_skills, experience_required, education, location, employment_type}
    """
    required = job.get("required_skills", [])
    preferred = job.get("preferred_skills", [])
    all_job_skills = list(dict.fromkeys(required + preferred))

    skill_score = skill_overlap_ratio(candidate.get("skills", []), all_job_skills)
    experience_score = experience_compatibility(candidate.get("experience_years"), job.get("experience_required"))
    education_score = education_compatibility(candidate.get("education", []), job.get("education", []))
    location_score = location_compatibility(candidate.get("location"), job.get("location"))
    preference_score = preference_compatibility(candidate.get("preferences"), job)

    weights = {
        "skill": settings.match_skill_weight,
        "experience": settings.match_experience_weight,
        "education": settings.match_education_weight,
        "location": settings.match_location_weight,
        "preference": settings.match_preference_weight,
    }
    weight_sum = sum(weights.values()) or 1.0

    overall = (
        skill_score * weights["skill"]
        + experience_score * weights["experience"]
        + education_score * weights["education"]
        + location_score * weights["location"]
        + preference_score * weights["preference"]
    ) / weight_sum

    return {
        "match_score": round(overall * 100, 1),
        "skill_score": round(skill_score * 100, 1),
        "experience_score": round(experience_score * 100, 1),
        "education_score": round(education_score * 100, 1),
        "location_score": round(location_score * 100, 1),
        "preference_score": round(preference_score * 100, 1),
        "weights_used": weights,
    }
