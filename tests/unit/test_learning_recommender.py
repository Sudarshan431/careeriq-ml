import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import unittest

from app.ml.matching.skill_gap import analyze_skill_gap
from app.ml.learning.learning_recommender import build_learning_recommendations


class TestLearningRecommender(unittest.TestCase):
    def test_prerequisite_ordered_before_dependent_skill(self):
        # "Spring Boot"'s taxonomy parent is "Spring" -- if "Spring" is ALSO
        # a gap skill, it must be scheduled before "Spring Boot".
        candidate_skills = []
        gap = analyze_skill_gap(candidate_skills, ["Spring", "Spring Boot"])
        items = build_learning_recommendations(candidate_skills, gap)
        order = {i["skill"]: i["recommended_order"] for i in items}
        self.assertLess(order["Spring"], order["Spring Boot"])

    def test_unmet_prerequisite_marks_foundational_difficulty(self):
        gap = analyze_skill_gap([], ["AWS"])
        items = build_learning_recommendations([], gap)
        aws_item = next(i for i in items if i["skill"] == "AWS")
        self.assertEqual(aws_item["difficulty"], "FOUNDATIONAL")
        self.assertIn("Cloud", aws_item["prerequisite_skills"])

    def test_met_prerequisite_not_foundational(self):
        # Candidate already has "Cloud" -> AWS shouldn't need it as an unmet prerequisite
        gap = analyze_skill_gap(["Cloud"], ["Cloud", "AWS"])
        items = build_learning_recommendations(["Cloud"], gap)
        aws_item = next(i for i in items if i["skill"] == "AWS")
        self.assertEqual(aws_item["prerequisite_skills"], [])
        self.assertNotEqual(aws_item["difficulty"], "FOUNDATIONAL")

    def test_priority_ordering_among_independent_skills(self):
        gap = analyze_skill_gap(["Java"], ["Java", "Kafka"], preferred_skills=["Redis"])
        items = build_learning_recommendations(["Java"], gap)
        priorities_in_order = [i["priority"] for i in items]
        self.assertEqual(priorities_in_order, sorted(priorities_in_order, key=lambda p: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[p]))

    def test_recommended_order_is_sequential_starting_at_one(self):
        gap = analyze_skill_gap([], ["Java", "Kafka", "AWS"])
        items = build_learning_recommendations([], gap)
        self.assertEqual([i["recommended_order"] for i in items], list(range(1, len(items) + 1)))

    def test_empty_gap_returns_empty_list(self):
        gap = analyze_skill_gap(["Java"], ["Java"])
        self.assertEqual(build_learning_recommendations(["Java"], gap), [])

    def test_no_fabricated_resource_urls(self):
        gap = analyze_skill_gap([], ["Java"])
        items = build_learning_recommendations([], gap)
        for item in items:
            for resource_type in item["suggested_resource_types"]:
                self.assertNotIn("http", resource_type.lower())


if __name__ == "__main__":
    unittest.main()
