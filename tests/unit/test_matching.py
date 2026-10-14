import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import unittest

from app.ml.matching.baseline import baseline_match
from app.ml.matching.skill_gap import analyze_skill_gap
from app.ml.features.feature_builder import skill_overlap_ratio, experience_compatibility


class TestBaselineMatching(unittest.TestCase):
    def test_perfect_skill_match_scores_high(self):
        candidate = {"skills": ["Java", "Spring Boot", "PostgreSQL"], "experience_years": 5, "education": [], "location": None}
        job = {"required_skills": ["Java", "Spring Boot", "PostgreSQL"], "preferred_skills": [], "experience_required": 2, "education": [], "location": None}
        result = baseline_match(candidate, job)
        self.assertGreaterEqual(result["skill_score"], 99)

    def test_no_overlap_scores_low(self):
        candidate = {"skills": ["JavaScript", "React"], "experience_years": 2, "education": [], "location": None}
        job = {"required_skills": ["Java", "Spring Boot"], "preferred_skills": [], "experience_required": 2, "education": [], "location": None}
        result = baseline_match(candidate, job)
        self.assertEqual(result["skill_score"], 0.0)

    def test_no_job_requirements_is_full_score(self):
        self.assertEqual(skill_overlap_ratio(["Java"], []), 1.0)

    def test_experience_compatibility_meets_requirement(self):
        self.assertEqual(experience_compatibility(5, 3), 1.0)

    def test_experience_compatibility_falls_short(self):
        self.assertAlmostEqual(experience_compatibility(1, 2), 0.5)

    def test_experience_compatibility_unknown_candidate_years(self):
        self.assertEqual(experience_compatibility(None, 3), 0.5)


class TestSkillGap(unittest.TestCase):
    def test_matched_and_missing(self):
        result = analyze_skill_gap(
            candidate_skills=["Java", "Spring Boot", "PostgreSQL", "Docker"],
            required_skills=["Java", "Spring Boot", "PostgreSQL", "Docker", "Kafka", "Kubernetes", "AWS"],
        )
        self.assertEqual(set(result["matched_skills"]), {"Java", "Spring Boot", "PostgreSQL", "Docker"})
        self.assertIn("Kafka", result["critical_missing_skills"] + [p["skill"] for p in result["partially_matched_skills"]])

    def test_related_skill_marks_partial_match(self):
        # Candidate has "Spring" (parent), job wants "Spring Boot" -> should be partially matched, not fully missing
        result = analyze_skill_gap(candidate_skills=["Spring"], required_skills=["Spring Boot"])
        partial_skills = [p["skill"] for p in result["partially_matched_skills"]]
        self.assertIn("Spring Boot", partial_skills)
        self.assertNotIn("Spring Boot", result["critical_missing_skills"])

    def test_empty_required_skills(self):
        result = analyze_skill_gap(candidate_skills=["Java"], required_skills=[])
        self.assertEqual(result["match_coverage_percent"], 100.0)


if __name__ == "__main__":
    unittest.main()
