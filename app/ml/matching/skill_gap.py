"""
Skill-gap engine: given a candidate's skills and a job's required/preferred
skills, computes matched / missing / critical-missing / optional-missing,
using taxonomy relationships to note when a candidate has a *related* skill
even if not an exact match (e.g. has "Spring" when job wants "Spring Boot").
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.core.config import settings
from app.nlp.skill_normalizer import normalize_skill_list


@lru_cache(maxsize=1)
def _relationships() -> dict:
    path = Path(settings.taxonomy_dir) / "skill_relationships.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _related_skills(skill: str) -> set[str]:
    rel = _relationships().get(skill, {})
    related = set(rel.get("children", [])) | set(rel.get("related", []))
    if rel.get("parent"):
        related.add(rel["parent"])
    return related


def analyze_skill_gap(candidate_skills: list[str], required_skills: list[str], preferred_skills: list[str] | None = None) -> dict:
    preferred_skills = preferred_skills or []
    cand = set(normalize_skill_list(candidate_skills))
    required = normalize_skill_list(required_skills)
    preferred = [s for s in normalize_skill_list(preferred_skills) if s not in required]

    matched = [s for s in required if s in cand]
    missing_required = [s for s in required if s not in cand]

    partially_matched = []
    fully_missing = []
    for skill in missing_required:
        if cand & _related_skills(skill):
            partially_matched.append(
                {"skill": skill, "related_skills_present": sorted(cand & _related_skills(skill))}
            )
        else:
            fully_missing.append(skill)

    matched_preferred = [s for s in preferred if s in cand]
    missing_preferred = [s for s in preferred if s not in cand]

    return {
        "matched_skills": matched,
        "matched_preferred_skills": matched_preferred,
        "partially_matched_skills": partially_matched,
        "critical_missing_skills": fully_missing,  # required, no related skill present
        "optional_missing_skills": missing_preferred,  # preferred only
        "match_coverage_percent": round(100 * len(matched) / len(required), 1) if required else 100.0,
    }
