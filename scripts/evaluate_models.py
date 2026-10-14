"""
Loads the persisted matching model and re-evaluates it on the full dataset,
and separately compares the TF-IDF-fallback semantic scorer's latency to
the baseline scorer's latency. Writes a small evaluation report to reports/.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from app.utils.model_utils import load_model
from app.ml.evaluation.metrics import classification_metrics
from app.ml.matching.baseline import baseline_match
from app.ml.matching.hybrid import hybrid_match
from scripts.train_matching import FEATURE_COLUMNS


def main():
    root = Path(__file__).resolve().parent.parent
    df = pd.read_csv(root / "data/synthetic/matching_dataset.csv")
    model, metadata = load_model(root / "models/matching")

    X = df[FEATURE_COLUMNS]
    y = df["is_good_match"]
    pred = model.predict(X)
    prob = model.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else None
    full_metrics = classification_metrics(y, pred, prob)

    print(f"Loaded model: {metadata.get('model_name')} (trained {metadata.get('training_date')})")
    print("Full-dataset metrics (note: includes training data, so this is an upper bound, not a generalization estimate):")
    for k, v in full_metrics.items():
        print(f"  {k}: {v}")

    # --- Latency comparison: baseline (rules-only) vs hybrid (adds semantic step) ---
    sample_candidate = {"skills": ["Java", "Spring Boot", "PostgreSQL"], "experience_years": 3, "education": [], "location": None}
    sample_job = {"required_skills": ["Java", "Spring Boot", "Kafka"], "preferred_skills": ["Docker"], "experience_required": 2, "education": [], "location": None, "description": "We need a Java Spring Boot backend engineer with Kafka experience."}

    n_runs = 20
    t0 = time.perf_counter()
    for _ in range(n_runs):
        baseline_match(sample_candidate, sample_job)
    baseline_latency_ms = (time.perf_counter() - t0) / n_runs * 1000

    t0 = time.perf_counter()
    for _ in range(n_runs):
        hybrid_match(sample_candidate, sample_job)
    hybrid_latency_ms = (time.perf_counter() - t0) / n_runs * 1000

    print(f"\nBaseline matcher latency: {baseline_latency_ms:.2f} ms/call (avg of {n_runs} runs)")
    print(f"Hybrid matcher latency (TF-IDF fallback embeddings): {hybrid_latency_ms:.2f} ms/call (avg of {n_runs} runs)")

    report_path = root / "reports" / "evaluation_report.md"
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# CareerIQ Matching Model Evaluation\n\n")
        f.write(f"Model: `{metadata.get('model_name')}`  \nTrained: {metadata.get('training_date')}\n\n")
        f.write("## Full-dataset metrics\n\n")
        for k, v in full_metrics.items():
            f.write(f"- **{k}**: {v}\n")
        f.write("\n## Latency (rules-based baseline vs hybrid w/ semantic step)\n\n")
        f.write(f"- Baseline matcher: {baseline_latency_ms:.2f} ms/call\n")
        f.write(f"- Hybrid matcher: {hybrid_latency_ms:.2f} ms/call\n")
        f.write(
            "\n_Note: this environment does not have `sentence-transformers` installed, so the "
            "hybrid matcher's semantic component is running on the TF-IDF cosine-similarity fallback, "
            "not true sentence embeddings. Latency and quality will differ once the real embedding "
            "model is installed._\n"
        )
    print(f"\nReport written to {report_path}")


if __name__ == "__main__":
    main()
