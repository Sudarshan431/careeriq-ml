"""
Priority classification for skill gaps -- built strictly on top of the
existing `analyze_skill_gap` (app.ml.matching.skill_gap), never
duplicating its matching/alias/relationship logic. Every priority is
derived deterministically from the categories that function already
computes:

  critical_missing_skills   (required, no related skill present) -> HIGH
  partially_matched_skills  (required, but a related skill IS present) -> MEDIUM
  optional_missing_skills   (preferred only, not required) -> LOW

This mirrors how a hiring manager would actually reason about gaps: a
required skill you have zero foothold in is the biggest risk; a required
skill where you already have a closely related skill is a smaller gap;
a merely-preferred skill is the least urgent.
"""
from __future__ import annotations

_PRIORITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def prioritize_skill_gaps(gap: dict) -> list[dict]:
    """
    Takes the dict returned by `analyze_skill_gap` and returns a flat,
    deterministically-ordered list of {skill, priority, reason,
    related_skills_present}, ready to drive both the skill-gap API
    response and the learning-recommendation engine.
    """
    items: list[dict] = []

    for skill in gap.get("critical_missing_skills", []):
        items.append(
            {
                "skill": skill,
                "priority": "HIGH",
                "reason": f"{skill} is required by this job and the candidate has no related skill on file.",
                "related_skills_present": [],
            }
        )

    for entry in gap.get("partially_matched_skills", []):
        related = entry.get("related_skills_present", [])
        related_text = ", ".join(related) if related else "a related skill"
        items.append(
            {
                "skill": entry["skill"],
                "priority": "MEDIUM",
                "reason": f"{entry['skill']} is required by this job; the candidate already has {related_text}, "
                "which should make this faster to pick up.",
                "related_skills_present": related,
            }
        )

    for skill in gap.get("optional_missing_skills", []):
        items.append(
            {
                "skill": skill,
                "priority": "LOW",
                "reason": f"{skill} is listed as preferred (not required) for this job.",
                "related_skills_present": [],
            }
        )

    items.sort(key=lambda i: (_PRIORITY_ORDER[i["priority"]], i["skill"]))
    return items
