import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import unittest

from app.ml.matching.skill_gap import analyze_skill_gap
from app.ml.matching.skill_priority import prioritize_skill_gaps


class TestSkillPriority(unittest.TestCase):
    def test_critical_missing_is_high_priority(self):
        gap = analyze_skill_gap(["Java"], ["Java", "Kafka"])
        priorities = prioritize_skill_gaps(gap)
        kafka = next(p for p in priorities if p["skill"] == "Kafka")
        self.assertEqual(kafka["priority"], "HIGH")

    def test_partially_matched_is_medium_priority(self):
        # Candidate has "Spring" (parent), job wants "Spring Boot" -> related skill present -> MEDIUM
        gap = analyze_skill_gap(["Spring"], ["Spring Boot"])
        priorities = prioritize_skill_gaps(gap)
        self.assertEqual(priorities[0]["priority"], "MEDIUM")
        self.assertIn("Spring", priorities[0]["related_skills_present"])

    def test_preferred_only_missing_is_low_priority(self):
        gap = analyze_skill_gap(["Java"], ["Java"], preferred_skills=["Docker"])
        priorities = prioritize_skill_gaps(gap)
        self.assertEqual(priorities[0]["priority"], "LOW")

    def test_ordering_high_before_medium_before_low(self):
        gap = analyze_skill_gap(["Spring"], ["Java", "Spring Boot"], preferred_skills=["Docker"])
        priorities = prioritize_skill_gaps(gap)
        priority_sequence = [p["priority"] for p in priorities]
        self.assertEqual(priority_sequence, sorted(priority_sequence, key=lambda p: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[p]))

    def test_no_gaps_returns_empty(self):
        gap = analyze_skill_gap(["Java", "Spring Boot"], ["Java", "Spring Boot"])
        self.assertEqual(prioritize_skill_gaps(gap), [])

    def test_empty_candidate_skills_all_high(self):
        gap = analyze_skill_gap([], ["Java", "Python"])
        priorities = prioritize_skill_gaps(gap)
        self.assertTrue(all(p["priority"] == "HIGH" for p in priorities))
        self.assertEqual(len(priorities), 2)


if __name__ == "__main__":
    unittest.main()
