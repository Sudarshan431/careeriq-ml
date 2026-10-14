"""Helpers for saving/loading joblib model artifacts + metadata, used by training scripts and inference."""
from __future__ import annotations

import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib


def save_model(model, model_dir: str | Path, model_name: str, metrics: dict, config: dict, dataset_version: str = "v1", feature_version: str = "v1"):
    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    model_path = model_dir / "model.joblib"
    joblib.dump(model, model_path)

    metadata = {
        "model_name": model_name,
        "version": datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
        "training_date": datetime.now(timezone.utc).isoformat(),
        "dataset_version": dataset_version,
        "feature_version": feature_version,
        "metrics": metrics,
        "configuration": config,
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
    }
    with open(model_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return model_path, metadata


def load_model(model_dir: str | Path):
    model_dir = Path(model_dir)
    model = joblib.load(model_dir / "model.joblib")
    metadata = {}
    meta_path = model_dir / "metadata.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    return model, metadata
