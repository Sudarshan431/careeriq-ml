"""
Trains and evaluates the content-based recommendation approach using
ranking metrics (spec section 24: Precision@K, Recall@K, MAP@K, NDCG@K).

There is no separately "trained" model here beyond the persisted matching
classifier -- content-based recommendation (TF-IDF + skill overlap) is a
deterministic scoring function, not a supervised model, so what we validate
is its RANKING QUALITY against the synthetic ground truth (is_good_match),
using the same candidate/job pairs as the matching dataset. This keeps the
evaluation honest: we do not claim to have "trained a recommender" when the
underlying scorer has no learned parameters.

Usage:
    python scripts/train_recommendation.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from app.ml.evaluation.metrics import mean_average_precision_at_k, ndcg_at_k, precision_at_k, recall_at_k
from app.ml.recommendation.content_based import recommend_jobs_content_based
from scripts.generate_synthetic_data import SKILL_CLUSTERS, TITLES, RNG_SEED
import random


def rebuild_candidates_and_jobs(rng: random.Random, n_candidates=40, n_jobs=15):
    """Rebuild a smaller candidate/job pool (with full skill lists, not just the flattened
    CSV features) so we can actually call the content-based recommender end-to-end."""
    from scripts.generate_synthetic_data import generate_candidates, generate_jobs

    candidates = generate_candidates(rng, n_candidates)
    jobs = generate_jobs(rng, n_jobs)
    for j in jobs:
        j["preferred_skills"] = []
        j["description"] = f"{j['title']} role requiring " + ", ".join(j["required_skills"])
    return candidates, jobs


def relevant_jobs_for(candidate: dict, jobs: list[dict], overlap_threshold: float = 0.5) -> set:
    from app.ml.features.feature_builder import skill_overlap_ratio

    return {
        j["job_id"]
        for j in jobs
        if skill_overlap_ratio(candidate["skills"], j["required_skills"]) >= overlap_threshold
    }


def main():
    rng = random.Random(RNG_SEED)
    candidates, jobs = rebuild_candidates_and_jobs(rng)

    k = 5
    all_recommended = []
    all_relevant = []
    p_at_k_scores, r_at_k_scores, ndcg_scores = [], [], []

    for cand in candidates:
        cand_input = {"skills": cand["skills"], "profile_text": " ".join(cand["skills"])}
        recs = recommend_jobs_content_based(cand_input, jobs, top_k=k)
        recommended_ids = [r["job_id"] for r in recs]
        relevant_ids = relevant_jobs_for(cand, jobs)

        if not relevant_ids:
            continue  # skip candidates with no relevant job in this small pool -- undefined recall

        all_recommended.append(recommended_ids)
        all_relevant.append(relevant_ids)
        p_at_k_scores.append(precision_at_k(recommended_ids, relevant_ids, k))
        r_at_k_scores.append(recall_at_k(recommended_ids, relevant_ids, k))
        ndcg_scores.append(ndcg_at_k(recommended_ids, relevant_ids, k))

    n_eval = len(all_recommended)
    mean_p = sum(p_at_k_scores) / n_eval if n_eval else 0.0
    mean_r = sum(r_at_k_scores) / n_eval if n_eval else 0.0
    mean_ndcg = sum(ndcg_scores) / n_eval if n_eval else 0.0
    map_at_k = mean_average_precision_at_k(all_recommended, all_relevant, k)

    print(f"Evaluated content-based recommender on {n_eval}/{len(candidates)} candidates (k={k})")
    print(f"  Precision@{k}: {mean_p:.4f}")
    print(f"  Recall@{k}:    {mean_r:.4f}")
    print(f"  MAP@{k}:       {map_at_k:.4f}")
    print(f"  NDCG@{k}:      {mean_ndcg:.4f}")

    report_path = Path(__file__).resolve().parent.parent / "reports" / "recommendation_evaluation.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Recommendation Ranking Evaluation\n\n")
        f.write(
            "Content-based recommender (TF-IDF + skill overlap) evaluated against synthetic "
            "ground truth (jobs with >=50% skill overlap treated as relevant).\n\n"
        )
        f.write(f"- Candidates evaluated: {n_eval}/{len(candidates)}\n")
        f.write(f"- Precision@{k}: {mean_p:.4f}\n")
        f.write(f"- Recall@{k}: {mean_r:.4f}\n")
        f.write(f"- MAP@{k}: {map_at_k:.4f}\n")
        f.write(f"- NDCG@{k}: {mean_ndcg:.4f}\n")
    print(f"\nReport written to {report_path}")


if __name__ == "__main__":
    main()
