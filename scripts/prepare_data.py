"""
Data-quality pipeline for the synthetic matching dataset (spec section 6).

Runs missing-value handling, duplicate removal, and range/outlier checks on
data/synthetic/matching_dataset.csv, logs exactly what is removed and why
(never silently discards rows), and writes a data-quality report.

Usage:
    python scripts/prepare_data.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

RAW_PATH = Path(__file__).resolve().parent.parent / "data/synthetic/matching_dataset.csv"
OUT_PATH = Path(__file__).resolve().parent.parent / "data/processed/matching_dataset_clean.csv"
REPORT_PATH = Path(__file__).resolve().parent.parent / "reports/data_quality_report.md"

EXPECTED_RANGES = {
    "skill_overlap_ratio": (0.0, 1.0),
    "experience_compatibility": (0.0, 1.0),
    "candidate_experience_years": (0.0, 60.0),
    "job_experience_required": (0.0, 40.0),
}


def main():
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"{RAW_PATH} not found. Run scripts/generate_synthetic_data.py first.")

    df = pd.read_csv(RAW_PATH)
    n_start = len(df)
    log_lines = [f"Loaded {n_start} rows from {RAW_PATH.relative_to(RAW_PATH.parent.parent)}"]

    # 1. Missing values -- report per-column counts; for this dataset every
    #    column is derived deterministically so we expect zero, but we check
    #    rather than assume.
    missing = df.isna().sum()
    missing_cols = missing[missing > 0]
    if len(missing_cols):
        log_lines.append(f"Missing values found in columns: {missing_cols.to_dict()}")
        # Numeric feature columns: impute with column median (documented, not silent).
        for col in missing_cols.index:
            if pd.api.types.is_numeric_dtype(df[col]):
                median = df[col].median()
                n_filled = df[col].isna().sum()
                df[col] = df[col].fillna(median)
                log_lines.append(f"  Imputed {n_filled} missing values in '{col}' with median={median}")
            else:
                n_dropped = df[col].isna().sum()
                df = df.dropna(subset=[col])
                log_lines.append(f"  Dropped {n_dropped} rows with missing non-numeric '{col}'")
    else:
        log_lines.append("No missing values found.")

    # 2. Duplicate removal (exact duplicate candidate-job pairs).
    n_before = len(df)
    df = df.drop_duplicates(subset=["candidate_id", "job_id"])
    n_dupes = n_before - len(df)
    log_lines.append(f"Removed {n_dupes} duplicate candidate-job pairs.")

    # 3. Range / outlier checks -- flag and clip rather than silently drop,
    #    since these are engineered features with known valid ranges.
    for col, (low, high) in EXPECTED_RANGES.items():
        if col not in df.columns:
            continue
        out_of_range = ((df[col] < low) | (df[col] > high)).sum()
        if out_of_range:
            df[col] = df[col].clip(lower=low, upper=high)
            log_lines.append(f"Clipped {out_of_range} out-of-range values in '{col}' to [{low}, {high}]")

    # 4. Label sanity check.
    invalid_labels = (~df["is_good_match"].isin([0, 1])).sum()
    if invalid_labels:
        df = df[df["is_good_match"].isin([0, 1])]
        log_lines.append(f"Dropped {invalid_labels} rows with invalid 'is_good_match' label.")

    n_end = len(df)
    log_lines.append(f"Final dataset: {n_end} rows ({n_start - n_end} removed total).")
    log_lines.append(f"Positive label rate after cleaning: {df['is_good_match'].mean():.3f}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    log_lines.append(f"Saved cleaned dataset to {OUT_PATH.relative_to(OUT_PATH.parent.parent)}")

    REPORT_PATH.parent.mkdir(exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# Data Quality Report\n\n")
        f.write("Source: `data/synthetic/matching_dataset.csv` (synthetic, deterministic seed=42)\n\n")
        f.write("## Steps performed\n\n")
        for line in log_lines:
            f.write(f"- {line}\n")

    for line in log_lines:
        print(line)
    print(f"\nReport written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
