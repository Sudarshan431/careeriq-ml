"""
Trains a baseline supervised matching classifier (Logistic Regression) on
the synthetic dataset, compares it against a simple thresholded-baseline
(skill overlap >= 0.5), evaluates both, and persists the trained model.

Usage:
    python scripts/generate_synthetic_data.py   # if not already run
    python scripts/train_matching.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

from app.ml.evaluation.metrics import classification_metrics
from app.utils.model_utils import save_model

RNG_SEED = 42
FEATURE_COLUMNS = [
    "skill_overlap_ratio",
    "experience_compatibility",
    "same_cluster",
    "candidate_experience_years",
    "job_experience_required",
    "n_candidate_skills",
    "n_required_skills",
]


def load_dataset() -> pd.DataFrame:
    path = Path(__file__).resolve().parent.parent / "data/synthetic/matching_dataset.csv"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run scripts/generate_synthetic_data.py first.")
    return pd.read_csv(path)


def main():
    df = load_dataset()
    X = df[FEATURE_COLUMNS]
    y = df["is_good_match"]

    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=RNG_SEED, stratify=y)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=RNG_SEED, stratify=y_temp)

    print(f"Train/val/test sizes: {len(X_train)}/{len(X_val)}/{len(X_test)}")

    # --- Baseline: threshold on skill_overlap_ratio alone (no training) ---
    baseline_pred = (X_test["skill_overlap_ratio"] >= 0.5).astype(int)
    baseline_metrics = classification_metrics(y_test, baseline_pred)
    print("\n--- Baseline (skill_overlap >= 0.5 threshold) ---")
    for k, v in baseline_metrics.items():
        print(f"  {k}: {v}")

    # --- Candidate model 1: Logistic Regression ---
    logreg = LogisticRegression(max_iter=1000, random_state=RNG_SEED)
    logreg.fit(X_train, y_train)
    logreg_val_pred = logreg.predict(X_val)
    logreg_val_metrics = classification_metrics(y_val, logreg_val_pred)
    print("\n--- Logistic Regression (validation) ---")
    for k, v in logreg_val_metrics.items():
        print(f"  {k}: {v}")

    # --- Candidate model 2: Random Forest ---
    rf = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=RNG_SEED)
    rf.fit(X_train, y_train)
    rf_val_pred = rf.predict(X_val)
    rf_val_metrics = classification_metrics(y_val, rf_val_pred)
    print("\n--- Random Forest (validation) ---")
    for k, v in rf_val_metrics.items():
        print(f"  {k}: {v}")

    # Select the simplest model that performs at least as well (spec: prefer
    # simplest effective model rather than automatically picking the most
    # complex one).
    chosen_name, chosen_model, chosen_val_metrics = (
        ("logistic_regression", logreg, logreg_val_metrics)
        if logreg_val_metrics["f1"] >= rf_val_metrics["f1"] - 0.02
        else ("random_forest", rf, rf_val_metrics)
    )
    print(f"\nSelected model: {chosen_name} (val F1={chosen_val_metrics['f1']})")

    # Final held-out test evaluation of the chosen model.
    test_pred = chosen_model.predict(X_test)
    test_prob = chosen_model.predict_proba(X_test)[:, 1] if hasattr(chosen_model, "predict_proba") else None
    test_metrics = classification_metrics(y_test, test_pred, test_prob)
    print("\n--- Selected model (held-out test) ---")
    for k, v in test_metrics.items():
        print(f"  {k}: {v}")

    model_dir = Path(__file__).resolve().parent.parent / "models" / "matching"
    save_model(
        chosen_model,
        model_dir,
        model_name=chosen_name,
        metrics={"validation": chosen_val_metrics, "test": test_metrics, "baseline_comparison": baseline_metrics},
        config={"features": FEATURE_COLUMNS, "seed": RNG_SEED},
        dataset_version="synthetic-v1",
        feature_version="v1",
    )
    print(f"\nModel saved to {model_dir}")


if __name__ == "__main__":
    main()
