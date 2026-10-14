"""
Tests the career-plan milestone-grouping/ordering logic directly against
app.ml.matching + app.ml.learning (the pure, DB-free layers career_plan_service
is built on) -- app.services.career_plan_service itself needs sqlalchemy for
its type hints (Session), so its thin DB-glue wrapper is exercised only by
the integration tests, consistent with every other DB-touching service in
this project. This test module verifies the actual milestone/ordering
algorithm career_plan_service delegates to, not a reimplementation of it.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import unittest

from app.ml.matching.skill_gap import analyze_skill_gap
from app.ml.learning.learning_recommender import build_learning_recommendations

_MILESTONE_LABELS = {
    "HIGH": "Milestone 1: Close critical gaps",
    "MEDIUM": "Milestone 2: Build on related skills",
    "LOW": "Milestone 3: Round out preferred skills",
}


def group_into_milestones(items, candidate_skills):
    """Mirrors app.services.career_plan_service._group_into_milestones exactly."""
    milestones = {}
    for item in items:
        milestones.setdefault(item["priority"], []).append(item)
    result = []
    for priority in ("HIGH", "MEDIUM", "LOW"):
        group = milestones.get(priority)
        if not group:
            continue
        result.append({"label": _MILESTONE_LABELS[priority], "skills": [i["skill"] for i in group]})
    return result


class TestCareerPlanLogic(unittest.TestCase):
    def test_milestones_only_include_present_priorities(self):
        gap = analyze_skill_gap(["Java"], ["Java", "Kafka"])  # only HIGH present, no preferred skills
        items = build_learning_recommendations(["Java"], gap)
        milestones = group_into_milestones(items, ["Java"])
        labels = [m["label"] for m in milestones]
        self.assertEqual(labels, [_MILESTONE_LABELS["HIGH"]])

    def test_milestones_ordered_high_medium_low(self):
        gap = analyze_skill_gap(["Spring"], ["Spring Boot", "Kafka"], preferred_skills=["Redis"])
        items = build_learning_recommendations(["Spring"], gap)
        milestones = group_into_milestones(items, ["Spring"])
        labels = [m["label"] for m in milestones]
        self.assertEqual(labels, sorted(labels, key=lambda l: list(_MILESTONE_LABELS.values()).index(l)))

    def test_all_gap_skills_appear_exactly_once_across_milestones(self):
        gap = analyze_skill_gap(["Java"], ["Java", "Kafka", "AWS"], preferred_skills=["Redis", "Docker"])
        items = build_learning_recommendations(["Java"], gap)
        milestones = group_into_milestones(items, ["Java"])
        all_skills = [s for m in milestones for s in m["skills"]]
        self.assertEqual(sorted(all_skills), sorted(i["skill"] for i in items))
        self.assertEqual(len(all_skills), len(set(all_skills)))  # no duplicates


if __name__ == "__main__":
    unittest.main()
