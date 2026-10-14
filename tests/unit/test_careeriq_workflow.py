import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import unittest

from app.services.careeriq_workflow_service import run_candidate_workflow, build_candidate_input

RESUME = b"""
Ananya Verma
ananya.verma@example.com

Summary
Backend engineer with 3 years experience building scalable Java services.

Skills
Java, Spring Boot, PostgreSQL, Docker, Kafka, Git

Experience
Software Engineer at TechNova Solutions
Jan 2022 - Present
Built microservices using Java, Spring Boot, PostgreSQL and Docker.

Education
B.Tech Computer Science
ABC Institute of Technology
2021
"""

JOB = """
Java Backend Engineer

Required Skills:
Java, Spring Boot, PostgreSQL, Kafka

Preferred Skills:
Docker, Kubernetes, AWS

Experience: 3+ years experience required
"""

OTHER_JOBS = [
    {"title": "Frontend Developer", "description": "Required Skills: JavaScript, React, TypeScript, CSS"},
    {"title": "DevOps Engineer", "description": "Required Skills: Docker, Kubernetes, AWS, Terraform"},
]


class TestCareerIQWorkflow(unittest.TestCase):
    def test_full_workflow_end_to_end(self):
        result = run_candidate_workflow(RESUME, "resume.txt", JOB, OTHER_JOBS, use_semantic=False)

        # Candidate profile stage
        self.assertIn("Java", result["candidate_profile"]["skills"])
        self.assertIn("Spring Boot", result["candidate_profile"]["skills"])

        # Job analysis stage
        self.assertIn("Java", result["job"]["required_skills"])

        # Matching + skill gap + explanation stage
        match = result["match"]
        self.assertGreater(match["match_score"], 0)
        self.assertIn("Java", match["skill_gap"]["matched_skills"])
        self.assertIn("recommendation", match["explanation"])

        # Recommendation stage
        self.assertGreater(len(result["recommendations"]), 0)
        titles = [r.get("title") for r in result["recommendations"]]
        self.assertIn("DevOps Engineer", titles)  # shares Docker/Kubernetes/AWS -- should rank above pure-frontend

    def test_workflow_without_other_jobs_skips_recommendations(self):
        result = run_candidate_workflow(RESUME, "resume.txt", JOB, other_jobs_raw=None, use_semantic=False)
        self.assertEqual(result["recommendations"], [])

    def test_build_candidate_input_shape(self):
        profile = {"skills": ["Java"], "total_years_experience": 2.0, "education": [], "summary": "A backend dev"}
        candidate = build_candidate_input(profile, location="Bangalore")
        self.assertEqual(candidate["skills"], ["Java"])
        self.assertEqual(candidate["experience_years"], 2.0)
        self.assertEqual(candidate["location"], "Bangalore")


if __name__ == "__main__":
    unittest.main()
