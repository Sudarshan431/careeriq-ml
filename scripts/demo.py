"""
End-to-end demo of the CareerIQ ML pipeline: parses a sample resume + job
description, computes a match with explanation, runs skill-gap analysis,
and generates job recommendations -- all without needing the FastAPI layer
running (useful for quick sanity checks / this sandbox).

Usage:
    python scripts/demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.nlp.resume_parser import parse_resume
from app.nlp.job_parser import parse_job_description
from app.ml.matching.hybrid import hybrid_match
from app.ml.matching.skill_gap import analyze_skill_gap
from app.ml.matching.explanation import explain_match
from app.ml.recommendation.content_based import recommend_jobs_content_based

SAMPLE_RESUME = """
Ananya Verma
ananya.verma@example.com | +91 90000 11122

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

Projects
CareerIQ Backend - Java, Spring Boot, PostgreSQL, Docker
Candidate-job matching backend service.

Certifications
AWS Certified Solutions Architect - 2023
"""

SAMPLE_JOB = """
Java Backend Engineer

Required Skills:
Java, Spring Boot, PostgreSQL, Kafka

Preferred Skills:
Docker, Kubernetes, AWS

Responsibilities:
- Design and build backend services
- Own microservices in production

Experience: 3+ years experience required
Education: Bachelor degree in Computer Science
Location: Bangalore, India
Employment Type: Full-time
"""

OTHER_JOBS_RAW = [
    ("Spring Boot Developer", "Required Skills: Java, Spring Boot, Hibernate, Maven\nExperience: 2+ years experience required"),
    ("Backend Engineer", "Required Skills: Java, Spring, PostgreSQL, Docker\nExperience: 1+ years experience required"),
    ("Frontend Developer", "Required Skills: JavaScript, React, TypeScript, CSS\nExperience: 2+ years experience required"),
    ("DevOps Engineer", "Required Skills: Docker, Kubernetes, AWS, Terraform\nExperience: 3+ years experience required"),
]


def line():
    print("=" * 44)


def main():
    line()
    print("CareerIQ AI Demo")
    line()

    profile = parse_resume(SAMPLE_RESUME.encode("utf-8"), "resume.txt")
    print(f"\nCandidate: {profile['name']}")
    print(f"\nExtracted Skills:\n" + "\n".join(profile["skills"]))

    job = parse_job_description(SAMPLE_JOB)

    candidate = {
        "skills": profile["skills"],
        "experience_years": profile["total_years_experience"],
        "education": profile["education"],
        "summary": profile["summary"],
        "location": None,
    }

    print("\n---\n\n## JOB MATCH\n")
    match = hybrid_match(candidate, job)
    gap = analyze_skill_gap(candidate["skills"], job["required_skills"], job["preferred_skills"])
    explanation = explain_match(match, gap["matched_skills"], gap["critical_missing_skills"], match["experience_score"])

    print(f"Match Score: {match['match_score']}%\n")
    print("Matched Skills:")
    for s in gap["matched_skills"]:
        print(f"  \u2713 {s}")
    print("\nMissing Skills:")
    for s in gap["critical_missing_skills"]:
        print(f"  \u26a0 {s}")
    print(f"\nSemantic Similarity ({match['embedding_backend']}):\n{match['semantic_similarity_score']}%")
    print(f"\nRecommendation:\n{explanation['recommendation']}")

    print("\n---\n\n## SKILL GAP\n")
    for i, s in enumerate(gap["critical_missing_skills"], start=1):
        print(f"{i}. {s}")

    print("\n---\n\n## RECOMMENDED JOBS\n")
    jobs = [{**parse_job_description(text), "title": title, "job_id": title} for title, text in OTHER_JOBS_RAW]
    recs = recommend_jobs_content_based({**candidate, "profile_text": candidate["summary"]}, jobs, top_k=3)
    for i, r in enumerate(recs, start=1):
        print(f"{i}. {r['title']} — {round(r['score'] * 100)}%")

    line()


if __name__ == "__main__":
    main()
