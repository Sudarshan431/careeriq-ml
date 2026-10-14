"""
Embedding service with a singleton-loaded Sentence Transformer model
(never re-loaded per request). Falls back to a fitted TF-IDF vectorizer +
cosine similarity when sentence-transformers isn't installed -- this
environment does not have it, so the fallback path is what's actually
exercised and tested here. Both paths are exposed through the same
interface so callers don't need to know which is active.

Terminology note (see MODEL_CARD.md): this produces a "semantic similarity
score" in [0, 1]. It is NOT a probability of any real-world outcome (e.g.
hire success) and must not be presented as one.
"""
from __future__ import annotations

import re
import threading
from functools import lru_cache

import numpy as np

from app.core.config import settings
from app.core.exceptions import ModelNotAvailableError
from app.core.logging_config import get_logger
from app.ml.sklearn_capability import check_sklearn_text_capability

logger = get_logger(__name__)

_lock = threading.Lock()
_sentence_model = None
_sentence_model_load_attempted = False


def _try_load_sentence_transformer():
    global _sentence_model, _sentence_model_load_attempted
    if _sentence_model_load_attempted:
        return _sentence_model
    with _lock:
        if _sentence_model_load_attempted:
            return _sentence_model
        _sentence_model_load_attempted = True
        try:
            from sentence_transformers import SentenceTransformer

            _sentence_model = SentenceTransformer(settings.embedding_model)
            logger.info("Loaded sentence-transformer model=%s", settings.embedding_model)
        except Exception as e:
            logger.warning(
                "sentence-transformers unavailable (%s); falling back to TF-IDF cosine similarity. "
                "Install `sentence-transformers` and set EMBEDDING_MODEL to enable true semantic embeddings.",
                type(e).__name__,
            )
            _sentence_model = None
    return _sentence_model


def embedding_backend() -> str:
    """Returns 'sentence-transformer' or 'tfidf-fallback' -- surfaced in API responses for transparency."""
    return "sentence-transformer" if _try_load_sentence_transformer() is not None else "tfidf-fallback"


def embed_texts(texts: list[str]) -> np.ndarray:
    """Returns an (n_texts, dim) array of embeddings using whichever backend is available."""
    model = _try_load_sentence_transformer()
    if model is not None:
        return np.asarray(model.encode(texts, show_progress_bar=False))
    return _tfidf_embed(texts)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9\+\#\.]{2,}", text.lower())


def _tfidf_embed(texts: list[str]) -> np.ndarray:
    # This is the fallback path used when sentence-transformers isn't
    # available. Goes through the shared, process-cached capability check
    # (app.ml.sklearn_capability) rather than its own try/except import --
    # a blocked native extension can take seconds to minutes to fail, so
    # every caller of this fallback must share one cached outcome, not each
    # re-attempt the import independently.
    available, TfidfVectorizer, _cosine_similarity, reason = check_sklearn_text_capability()
    if not available:
        raise ModelNotAvailableError(
            "No embedding backend is available: sentence-transformers is not loaded and the "
            "scikit-learn fallback could not be loaded in this environment."
        )

    vectorizer = TfidfVectorizer(tokenizer=_tokenize, lowercase=False, min_df=1)
    matrix = vectorizer.fit_transform(texts)
    return matrix.toarray()


def semantic_similarity(text_a: str, text_b: str) -> float:
    """
    Cosine similarity between the two texts' embeddings, clipped to [0, 1].
    Returns 0.0 for empty input rather than raising, since callers (e.g. a
    resume with no summary) shouldn't crash the whole matching pipeline.
    """
    if not text_a or not text_b:
        return 0.0
    vectors = embed_texts([text_a, text_b])
    a, b = vectors[0], vectors[1]
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1e-9
    cosine = float(np.dot(a, b) / denom)
    return max(0.0, min(1.0, cosine))
