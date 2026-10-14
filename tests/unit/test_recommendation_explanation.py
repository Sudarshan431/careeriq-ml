import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import unittest

from app.services.recommendation_service import recommend_jobs

CANDIDATE = {"skills": ["Java", "Spring Boot", "PostgreSQL"], "profile_text": "Backend engineer", "experience_years": 3, "education": []}
JOBS = [
    {"job_id": "j1", "title": "Java Backend Engineer", "required_skills": ["Java", "Spring Boot"], "preferred_skills": ["Docker"], "description": "Java Spring Boot backend role", "experience_required": 2, "education": []},
    {"job_id": "j2", "title": "Frontend Developer", "required_skills": ["React"], "preferred_skills": [], "description": "Frontend role", "experience_required": 1, "education": []},
]


class TestRecommendationExplanation(unittest.TestCase):
    def test_explain_false_omits_explanation_fields(self):
        results = recommend_jobs(CANDIDATE, JOBS, top_k=2, strategy="hybrid", explain=False)
        for r in results:
            self.assertNotIn("explanation", r)
            self.assertNotIn("skill_gap", r)
            self.assertNotIn("score_breakdown", r)

    def test_explain_true_adds_explanation_fields(self):
        results = recommend_jobs(CANDIDATE, JOBS, top_k=2, strategy="hybrid", explain=True)
        j1 = next(r for r in results if r["job_id"] == "j1")
        self.assertIsNotNone(j1["explanation"])
        self.assertIn("recommendation", j1["explanation"])
        self.assertIsNotNone(j1["skill_gap"])
        self.assertIn("matched_skills", j1["skill_gap"])
        self.assertIsNotNone(j1["score_breakdown"])

    def test_explanation_matched_skills_are_real(self):
        results = recommend_jobs(CANDIDATE, JOBS, top_k=1, strategy="content", explain=True)
        j1 = results[0]
        for skill in j1["skill_gap"]["matched_skills"]:
            self.assertIn(skill, CANDIDATE["skills"])

    def test_deterministic_across_repeated_calls(self):
        results_a = recommend_jobs(CANDIDATE, JOBS, top_k=2, strategy="content", explain=True)
        results_b = recommend_jobs(CANDIDATE, JOBS, top_k=2, strategy="content", explain=True)
        self.assertEqual([r["job_id"] for r in results_a], [r["job_id"] for r in results_b])
        self.assertEqual([r["score"] for r in results_a], [r["score"] for r in results_b])

    def test_score_breakdown_matches_underlying_matching_service(self):
        from app.services.matching_service import calculate_match

        results = recommend_jobs(CANDIDATE, JOBS, top_k=1, strategy="content", explain=True)
        job = next(j for j in JOBS if j["job_id"] == results[0]["job_id"])
        direct_match = calculate_match(CANDIDATE, job, use_semantic=True)
        self.assertEqual(results[0]["score_breakdown"]["skill_score"], direct_match["skill_score"])


if __name__ == "__main__":
    unittest.main()
