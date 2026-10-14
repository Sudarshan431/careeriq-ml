"""
CareerIQ orchestration service (Phase 2).

Chains the existing resume/job/matching/recommendation services into the
single candidate journey described in the spec:

    resume -> candidate profile -> job analysis -> matching
    -> skill gap -> recommendations -> explanation

This module contains NO new NLP/ML logic of its own -- it only sequences
calls to the existing `app.services.*` modules (which in turn call the
existing `app.nlp` / `app.ml` layers), per Rule 2 ("do not duplicate
existing NLP/ML logic"; Rule 2 of the spec: preserve existing functionality).

Works with plain dicts so it can run standalone (as in `scripts/demo.py`
and the test below) or be wired into DB-backed routes (`app/api/candidate_routes.py`)
that convert ORM rows to/from these same dict shapes via the repository layer.
"""
from __future__ import annotations

from app.core.logging_config import Timer, get_logger
from app.services.job_service import analyze_job
from app.services.matching_service import calculate_match
from app.services.recommendation_service import recommend_jobs
from app.services.resume_service import analyze_resume

logger = get_logger(__name__)


def build_candidate_input(profile: dict, location: str | None = None, preferences: dict | None = None) -> dict:
    """Shapes a parsed resume profile (from resume_service.analyze_resume) into the
    dict shape the matching/recommendation layer expects."""
    return {
        "skills": profile.get("skills", []),
        "experience_years": profile.get("total_years_experience"),
        "education": profile.get("education", []),
        "location": location,
        "summary": profile.get("summary"),
        "profile_text": profile.get("summary") or " ".join(profile.get("skills", [])),
        "preferences": preferences,
    }


def run_candidate_workflow(
    resume_bytes: bytes,
    filename: str,
    job_description_raw: str,
    other_jobs_raw: list[dict] | None = None,
    use_semantic: bool = True,
    location: str | None = None,
    preferences: dict | None = None,
) -> dict:
    """
    Full candidate journey for a single target job, optionally plus a
    recommendation pass over a pool of other jobs.

    other_jobs_raw: list of {"job_id"/"title": str, "description": str} --
    each is run through the same job parser as the primary job.
    """
    with Timer(logger, "careeriq_workflow_candidate"):
        # 1. Resume -> candidate profile (reuses resume_service, which reuses
        #    the existing resume_parser / skill / education / experience /
        #    project / certification extractors unchanged).
        profile = analyze_resume(resume_bytes, filename)

        # 2. Job description -> structured requirements (reuses job_service /
        #    job_parser unchanged).
        job = analyze_job(job_description_raw)

        candidate = build_candidate_input(profile, location=location, preferences=preferences)

        # 3. Matching + skill gap + explanation in one call (reuses
        #    matching_service, which reuses baseline/hybrid/skill_gap/explanation unchanged).
        match_result = calculate_match(candidate, job, use_semantic=use_semantic)

        # 4. Optional recommendation pass over a pool of other jobs (reuses
        #    recommendation_service / content_based.py unchanged).
        recommendations = []
        if other_jobs_raw:
            parsed_other_jobs = []
            for raw in other_jobs_raw:
                parsed = analyze_job(raw["description"])
                parsed["job_id"] = raw.get("job_id") or raw.get("title") or parsed.get("title")
                parsed["title"] = raw.get("title") or parsed.get("title")
                parsed_other_jobs.append(parsed)
            recommendations = recommend_jobs(candidate, parsed_other_jobs, top_k=5, strategy="hybrid")

    return {
        "candidate_profile": profile,
        "job": job,
        "match": match_result,
        "recommendations": recommendations,
    }
