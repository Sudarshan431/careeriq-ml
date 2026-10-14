"""
Shared, reusable feature computations for candidate-job matching. Both the
transparent baseline scorer and any future supervised ML model should build
features through this module so results stay consistent and testable.
"""
from __future__ import annotations

from app.nlp.skill_normalizer import normalize_skill_list


def skill_overlap_ratio(candidate_skills: list[str], job_skills: list[str]) -> float:
    """Fraction of job_skills present in candidate_skills. 1.0 if job has no requirements listed."""
    job_set = set(normalize_skill_list(job_skills))
    if not job_set:
        return 1.0
    cand_set = set(normalize_skill_list(candidate_skills))
    return len(cand_set & job_set) / len(job_set)


def matched_and_missing(candidate_skills: list[str], job_skills: list[str]) -> tuple[list[str], list[str]]:
    cand_set = set(normalize_skill_list(candidate_skills))
    job_list = normalize_skill_list(job_skills)
    matched = [s for s in job_list if s in cand_set]
    missing = [s for s in job_list if s not in cand_set]
    return matched, missing


def experience_compatibility(candidate_years: float | None, required_years: int | None) -> float:
    """
    1.0 if candidate meets/exceeds requirement. Linearly scaled down if short,
    floor of 0.0 at zero years vs. any real requirement. If either side is
    unknown, return a neutral 0.5 rather than fabricating certainty.
    """
    if required_years is None or required_years == 0:
        return 1.0
    if candidate_years is None:
        return 0.5
    if candidate_years >= required_years:
        return 1.0
    return max(0.0, candidate_years / required_years)


def education_compatibility(candidate_education: list[dict], required_education: list[str]) -> float:
    """1.0 if any required education keyword appears in the candidate's degree(s); 1.0 if job has no requirement."""
    if not required_education:
        return 1.0
    if not candidate_education:
        return 0.0
    candidate_degrees = " ".join(
        f"{e.get('degree') or ''} {e.get('field') or ''}".lower() for e in candidate_education
    )
    hits = sum(1 for req in required_education if req.lower() in candidate_degrees)
    return min(1.0, hits / len(required_education)) if hits else 0.3  # partial credit: has *a* degree, just not matched


def location_compatibility(candidate_location: str | None, job_location: str | None, remote_ok: bool = False) -> float:
    if remote_ok or not job_location:
        return 1.0
    if not candidate_location:
        return 0.5
    return 1.0 if candidate_location.strip().lower() == job_location.strip().lower() else 0.0


def preference_compatibility(candidate_prefs: dict | None, job: dict | None) -> float:
    """
    Compares simple stated preferences (employment_type, remote) if the
    caller supplies them. Neutral 0.7 when no preferences are stated at all
    (absence of a stated preference isn't a mismatch).
    """
    if not candidate_prefs:
        return 0.7
    job = job or {}
    checks = []
    if candidate_prefs.get("employment_type") and job.get("employment_type"):
        checks.append(candidate_prefs["employment_type"].lower() == job["employment_type"].lower())
    if not checks:
        return 0.7
    return sum(checks) / len(checks)
