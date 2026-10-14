"""
Maps raw skill mentions (varied casing, aliases, abbreviations) onto a
canonical taxonomy skill name. Loads app/taxonomy/skills.json and
skill_aliases.json once and caches the lookup tables.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.core.config import settings


@lru_cache(maxsize=1)
def _load_taxonomy() -> dict:
    path = Path(settings.taxonomy_dir) / "skills.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _load_aliases() -> dict:
    path = Path(settings.taxonomy_dir) / "skill_aliases.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def canonical_skill_set() -> set[str]:
    taxonomy = _load_taxonomy()
    skills = set()
    for category_skills in taxonomy.values():
        skills.update(category_skills)
    return skills


@lru_cache(maxsize=1)
def _lower_to_canonical() -> dict[str, str]:
    """Every canonical skill, lowercased, maps to itself; every alias maps to its canonical form."""
    mapping = {s.lower(): s for s in canonical_skill_set()}
    mapping.update(_load_aliases())
    return mapping


@lru_cache(maxsize=1)
def skill_category_map() -> dict[str, str]:
    taxonomy = _load_taxonomy()
    out = {}
    for category, skills in taxonomy.items():
        for s in skills:
            out[s] = category
    return out


def normalize_skill(raw: str) -> str | None:
    """Return the canonical skill name for a raw mention, or None if unrecognized."""
    if not raw:
        return None
    key = raw.strip().lower()
    return _lower_to_canonical().get(key)


def normalize_skill_list(raw_skills: list[str]) -> list[str]:
    """Normalize a list, de-duplicating while preserving first-seen order."""
    seen = []
    for raw in raw_skills:
        canon = normalize_skill(raw)
        if canon and canon not in seen:
            seen.append(canon)
    return seen


def category_for(skill: str) -> str | None:
    return skill_category_map().get(skill)
