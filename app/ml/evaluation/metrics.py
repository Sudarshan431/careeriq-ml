"""
Evaluation metrics. Only report the metric family appropriate to the task
(classification / ranking / regression) -- see MODEL_CARD.md and section 24
of the spec.
"""
from __future__ import annotations

import numpy as np


# --- Classification --------------------------------------------------------

def classification_metrics(y_true, y_pred, y_prob=None) -> dict:
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

    metrics = {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }
    if y_prob is not None:
        from sklearn.metrics import roc_auc_score

        try:
            metrics["roc_auc"] = round(float(roc_auc_score(y_true, y_prob)), 4)
        except ValueError:
            metrics["roc_auc"] = None  # e.g. only one class present in y_true
    return metrics


# --- Regression / scoring ---------------------------------------------------

def regression_metrics(y_true, y_pred) -> dict:
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    return {
        "mae": round(float(mean_absolute_error(y_true, y_pred)), 4),
        "rmse": round(rmse, 4),
        "r2": round(float(r2_score(y_true, y_pred)), 4) if len(set(y_true.tolist())) > 1 else None,
    }


# --- Ranking / recommendation -----------------------------------------------

def precision_at_k(recommended: list, relevant: set, k: int) -> float:
    top_k = recommended[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for item in top_k if item in relevant)
    return hits / len(top_k)


def recall_at_k(recommended: list, relevant: set, k: int) -> float:
    if not relevant:
        return 0.0
    top_k = recommended[:k]
    hits = sum(1 for item in top_k if item in relevant)
    return hits / len(relevant)


def average_precision_at_k(recommended: list, relevant: set, k: int) -> float:
    top_k = recommended[:k]
    hits = 0
    precisions = []
    for i, item in enumerate(top_k, start=1):
        if item in relevant:
            hits += 1
            precisions.append(hits / i)
    return float(np.mean(precisions)) if precisions else 0.0


def mean_average_precision_at_k(list_of_recommended: list[list], list_of_relevant: list[set], k: int) -> float:
    aps = [average_precision_at_k(rec, rel, k) for rec, rel in zip(list_of_recommended, list_of_relevant)]
    return round(float(np.mean(aps)), 4) if aps else 0.0


def ndcg_at_k(recommended: list, relevant: set, k: int) -> float:
    top_k = recommended[:k]
    dcg = sum((1.0 if item in relevant else 0.0) / np.log2(i + 1) for i, item in enumerate(top_k, start=1))
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / np.log2(i + 1) for i in range(1, ideal_hits + 1))
    return round(float(dcg / idcg), 4) if idcg > 0 else 0.0
