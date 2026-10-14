"""
Pure similarity-ranking logic, deliberately separated from any DB access
(see simple_vector_retriever.py, which is the only caller) so the actual
ranking algorithm can be unit-tested without SQLAlchemy/a database --
consistent with this project's existing pattern of keeping ML/matching
logic DB-free (app/ml/matching/, app/ml/recommendation/, etc.).
"""
from __future__ import annotations

from app.ml.embeddings.embedding_service import embed_texts


def rank_texts_by_similarity(query: str, candidate_texts: list[str], top_k: int = 5) -> list[tuple[int, float]]:
    """
    Returns up to top_k (index_into_candidate_texts, similarity_score) pairs,
    sorted by descending similarity. Embeds query + candidates together in
    one call -- see simple_vector_retriever.py's module docstring for why
    that matters under the TF-IDF fallback embedding backend.
    """
    if not query or not query.strip() or not candidate_texts:
        return []

    import numpy as np

    vectors = embed_texts([query] + candidate_texts)
    query_vector, candidate_vectors = vectors[0], vectors[1:]

    scored = []
    for i, vector in enumerate(candidate_vectors):
        denom = (np.linalg.norm(query_vector) * np.linalg.norm(vector)) or 1e-9
        similarity = float(np.dot(query_vector, vector) / denom)
        scored.append((i, max(0.0, min(1.0, similarity))))

    scored.sort(key=lambda item: -item[1])
    return scored[:top_k]
