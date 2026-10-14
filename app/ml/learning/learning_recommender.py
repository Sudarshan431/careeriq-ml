"""
Learning recommendation engine.

Takes the prioritized skill gaps (app.ml.matching.skill_priority) for a
candidate + target job, and turns them into an ordered, dependency-aware
learning plan using the *same* skill_relationships.json taxonomy already
used for partial-match detection in app.ml.matching.skill_gap -- no new
relationship data, no duplicated taxonomy.

Design notes:
- Difficulty and ordering are derived deterministically from the
  taxonomy's parent/child structure and the candidate's current skills,
  never fabricated or hard-coded per skill name.
- No external learning-resource URLs are invented. The project has no
  learning-resource content of its own yet, so each recommendation
  instead carries `suggested_resource_types` (generic categories like
  "official documentation", "hands-on project") -- the extension point
  for real resource data (e.g. a `learning_resources` table/service)
  without rewriting this module when that data becomes available.
"""
from __future__ import annotations

from app.ml.matching.skill_priority import prioritize_skill_gaps
from app.ml.matching.skill_gap import _relationships  # reuse the same cached taxonomy load, not a copy

_DIFFICULTY_RESOURCE_TYPES = {
    "FOUNDATIONAL": ["official documentation", "beginner tutorial", "guided course"],
    "STANDARD": ["official documentation", "hands-on project"],
    "FOCUSED": ["official documentation", "hands-on project", "certification"],
}


def _parent_of(skill: str) -> str | None:
    return _relationships().get(skill, {}).get("parent")


def _has_children(skill: str) -> bool:
    return bool(_relationships().get(skill, {}).get("children"))


def build_learning_recommendations(candidate_skills: list[str], gap: dict) -> list[dict]:
    """
    candidate_skills: the candidate's current (normalized) skill list.
    gap: the dict returned by app.ml.matching.skill_gap.analyze_skill_gap.

    Returns a list of learning recommendations, each with skill, priority,
    reason (from prioritize_skill_gaps), prerequisite_skills, difficulty,
    recommended_order, and suggested_resource_types -- ordered so that any
    prerequisite among the gap skills themselves comes before the skill
    that depends on it, and HIGH-priority skills are preferred among
    otherwise-independent skills.
    """
    candidate_set = set(candidate_skills)
    prioritized = prioritize_skill_gaps(gap)
    gap_skill_names = {item["skill"] for item in prioritized}

    enriched = []
    for item in prioritized:
        skill = item["skill"]
        parent = _parent_of(skill)

        # A prerequisite only matters for ordering if the candidate doesn't
        # already have it -- if they do, there's nothing to sequence first.
        unmet_prerequisite = parent if parent and parent not in candidate_set else None
        prerequisite_skills = [unmet_prerequisite] if unmet_prerequisite else []

        if unmet_prerequisite:
            difficulty = "FOUNDATIONAL"  # needs a broader/foundational skill first
        elif _has_children(skill):
            difficulty = "STANDARD"  # a broad topic in its own right
        else:
            difficulty = "FOCUSED"  # a specific, addressable skill with no missing foundation

        enriched.append(
            {
                **item,
                "prerequisite_skills": prerequisite_skills,
                # If the prerequisite is itself one of the gap skills, note
                # that explicitly -- the topological sort below uses this.
                "prerequisite_in_gap": unmet_prerequisite in gap_skill_names if unmet_prerequisite else False,
                "difficulty": difficulty,
                "suggested_resource_types": _DIFFICULTY_RESOURCE_TYPES[difficulty],
            }
        )

    ordered = _topological_priority_sort(enriched)
    for idx, entry in enumerate(ordered, start=1):
        entry["recommended_order"] = idx
    return ordered


def _topological_priority_sort(items: list[dict]) -> list[dict]:
    """
    Orders learning items so that any prerequisite skill which is ALSO in
    this gap list is scheduled before the skill that depends on it, using
    priority (HIGH before MEDIUM before LOW) then skill name to break ties
    among items with no unresolved dependency. Simple, deterministic
    Kahn's-algorithm-style topological sort -- the taxonomy is shallow
    (parent chains are at most a couple of levels deep) so this never
    needs to handle deep or cyclic graphs.
    """
    by_skill = {i["skill"]: i for i in items}
    remaining = {i["skill"] for i in items}
    scheduled: list[dict] = []

    priority_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

    while remaining:
        ready = [
            skill
            for skill in remaining
            if not (by_skill[skill]["prerequisite_in_gap"] and by_skill[skill]["prerequisite_skills"][0] in remaining)
        ]
        if not ready:
            # Defensive fallback only -- shouldn't happen given the taxonomy's
            # shallow, acyclic structure, but never hang if it somehow did.
            ready = list(remaining)

        ready.sort(key=lambda s: (priority_rank[by_skill[s]["priority"]], s))
        next_skill = ready[0]
        scheduled.append(by_skill[next_skill])
        remaining.discard(next_skill)

    return scheduled
