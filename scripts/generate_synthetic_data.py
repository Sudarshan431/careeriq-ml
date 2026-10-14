"""
Generates a synthetic candidate-job matching dataset with realistic skill
co-occurrence structure (not random noise) so a trained classifier has real
signal to learn. Uses a deterministic seed for reproducibility.

Usage:
    python scripts/generate_synthetic_data.py --n-candidates 300 --n-jobs 60 --out data/synthetic/matching_dataset.csv

Design (see master spec section 5): candidates and jobs are drawn from a
small number of realistic "skill clusters" (Java backend, Python/ML,
frontend, DevOps/cloud). A candidate-job pair's label (is_good_match) is
derived from actual skill/experience overlap plus a controlled amount of
label noise, rather than being purely random.
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from app.ml.features.feature_builder import skill_overlap_ratio, experience_compatibility

RNG_SEED = 42

SKILL_CLUSTERS = {
    "java_backend": ["Java", "Spring", "Spring Boot", "Hibernate", "PostgreSQL", "Docker", "Kafka", "Microservices", "Maven"],
    "python_ml": ["Python", "Pandas", "NumPy", "scikit-learn", "TensorFlow", "PyTorch", "NLP", "FastAPI", "Docker"],
    "frontend": ["JavaScript", "TypeScript", "React", "Redux", "HTML", "CSS", "Next.js", "REST"],
    "devops_cloud": ["Docker", "Kubernetes", "AWS", "Terraform", "Jenkins", "CI/CD", "Azure", "Prometheus"],
    "fullstack": ["Java", "Spring Boot", "React", "PostgreSQL", "JavaScript", "Docker", "REST", "Git"],
}

TITLES = {
    "java_backend": ["Java Backend Engineer", "Backend Developer", "Spring Boot Developer"],
    "python_ml": ["Machine Learning Engineer", "Data Scientist", "Python ML Engineer"],
    "frontend": ["Frontend Developer", "React Developer", "UI Engineer"],
    "devops_cloud": ["DevOps Engineer", "Cloud Engineer", "Site Reliability Engineer"],
    "fullstack": ["Full Stack Developer", "Full-Stack Engineer"],
}

EDUCATION_OPTIONS = ["Bachelor of Technology", "Bachelor of Science", "Master of Technology", "Bachelor of Engineering"]


def _sample_skills(rng: random.Random, cluster: str, n_min: int = 4, n_max: int = 8) -> list[str]:
    pool = SKILL_CLUSTERS[cluster]
    n = rng.randint(min(n_min, len(pool)), min(n_max, len(pool)))
    return rng.sample(pool, n)


def generate_candidates(rng: random.Random, n: int) -> list[dict]:
    candidates = []
    clusters = list(SKILL_CLUSTERS.keys())
    for i in range(n):
        cluster = rng.choice(clusters)
        candidates.append(
            {
                "candidate_id": f"cand_{i:04d}",
                "cluster": cluster,
                "skills": _sample_skills(rng, cluster),
                "experience_years": round(rng.uniform(0, 10), 1),
                "education": rng.choice(EDUCATION_OPTIONS),
            }
        )
    return candidates


def generate_jobs(rng: random.Random, n: int) -> list[dict]:
    jobs = []
    clusters = list(SKILL_CLUSTERS.keys())
    for i in range(n):
        cluster = rng.choice(clusters)
        required = _sample_skills(rng, cluster, 3, 6)
        jobs.append(
            {
                "job_id": f"job_{i:04d}",
                "cluster": cluster,
                "title": rng.choice(TITLES[cluster]),
                "required_skills": required,
                "experience_required": rng.choice([0, 1, 2, 3, 5]),
            }
        )
    return jobs


def build_pairs(candidates: list[dict], jobs: list[dict], rng: random.Random, pairs_per_candidate: int = 3) -> pd.DataFrame:
    rows = []
    for cand in candidates:
        sampled_jobs = rng.sample(jobs, min(pairs_per_candidate, len(jobs)))
        for job in sampled_jobs:
            overlap = skill_overlap_ratio(cand["skills"], job["required_skills"])
            exp_compat = experience_compatibility(cand["experience_years"], job["experience_required"])
            same_cluster = int(cand["cluster"] == job["cluster"])

            # Ground-truth label: a "good match" requires decent skill overlap
            # AND experience compatibility, with a small amount of random
            # label noise to keep the classification task non-trivial.
            base_score = 0.6 * overlap + 0.3 * exp_compat + 0.1 * same_cluster
            noisy_score = min(1.0, max(0.0, base_score + rng.gauss(0, 0.07)))
            label = int(noisy_score >= 0.55)

            rows.append(
                {
                    "candidate_id": cand["candidate_id"],
                    "job_id": job["job_id"],
                    "skill_overlap_ratio": round(overlap, 4),
                    "experience_compatibility": round(exp_compat, 4),
                    "same_cluster": same_cluster,
                    "candidate_experience_years": cand["experience_years"],
                    "job_experience_required": job["experience_required"],
                    "n_candidate_skills": len(cand["skills"]),
                    "n_required_skills": len(job["required_skills"]),
                    "is_good_match": label,
                }
            )
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-candidates", type=int, default=300)
    parser.add_argument("--n-jobs", type=int, default=60)
    parser.add_argument("--pairs-per-candidate", type=int, default=3)
    parser.add_argument("--out", type=str, default="data/synthetic/matching_dataset.csv")
    args = parser.parse_args()

    rng = random.Random(RNG_SEED)
    candidates = generate_candidates(rng, args.n_candidates)
    jobs = generate_jobs(rng, args.n_jobs)
    df = build_pairs(candidates, jobs, rng, args.pairs_per_candidate)

    out_path = Path(__file__).resolve().parent.parent / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    print(f"Generated {len(df)} candidate-job pairs from {len(candidates)} candidates x {len(jobs)} jobs")
    print(f"Positive label rate: {df['is_good_match'].mean():.3f}")
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
