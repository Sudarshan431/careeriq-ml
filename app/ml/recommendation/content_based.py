"""
Content-based job recommendation engine.

MVP scope (see master spec section 21): content-based + semantic
recommendation only. Interfaces are kept separate from any future
collaborative-filtering signal (applications, saved/viewed/rejected jobs)
so that can be added later without rewriting this module -- see
`RecommendationSignal` below as the extension point.

Note on imports: scikit-learn (and its scipy dependency, which ships
native/compiled extensions) is imported lazily inside
`recommend_jobs_content_based`, not at module level. A module-level import
here would be pulled in transitively the moment this module is imported
(app.main -> recommendation_routes -> recommendation_service ->
this module), forcing every app startup to load scipy's native extensions
even for requests that never call this function. Some locked-down
environments (e.g. Windows Application Control / WDAC policies) block
those extensions from loading at all, which turned a startup-time
dependency into an application-crashing one. Importing lazily means
FastAPI startup no longer requires scikit-learn/scipy to succeed; only an
actual call to this function does, and a failure there is caught and
turned into the project's normal structured error response instead of an
unhandled crash.

The availability check itself goes through
`app.ml.sklearn_capability.check_sklearn_text_capability`, which caches
the result for the process lifetime -- see that module's docstring. This
matters because a blocked native extension doesn't just fail to import,
it can take tens of seconds to multiple minutes to fail under some
Application Control policies; without caching, every recommendation
request would re-pay that cost.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.core.exceptions import ModelNotAvailableError
from app.core.logging_config import get_logger
from app.ml.embeddings.embedding_service import semantic_similarity
from app.ml.features.feature_builder import skill_overlap_ratio
from app.ml.sklearn_capability import check_sklearn_text_capability

logger = get_logger(__name__)


@dataclass
class RecommendationSignal:
    """
    Extension point for future collaborative-filtering signals (e.g. an
    'applied', 'saved', or 'viewed' boost). Content-based recommendation
    ignores this today; a future hybrid recommender can weight it in
    without changing this module's public interface.
    """
    job_id: str
    behavioral_boost: float = 0.0


def _job_text(job: dict) -> str:
    parts = [
        job.get("title") or "",
        " ".join(job.get("required_skills", [])),
        " ".join(job.get("preferred_skills", [])),
        job.get("description") or "",
    ]
    return " ".join(p for p in parts if p)


def recommend_jobs_content_based(candidate: dict, jobs: list[dict], top_k: int = 5) -> list[dict]:
    """
    TF-IDF cosine similarity over (job title + skills + description) vs. the
    candidate's profile text, blended with explicit skill overlap.
    """
    if not jobs:
        return []

    available, TfidfVectorizer, cosine_similarity, reason = check_sklearn_text_capability()
    if not available:
        # No import is attempted here -- check_sklearn_text_capability()
        # already made the one real attempt (on first call, ever) and
        # cached the failure. This raise is immediate.
        raise ModelNotAvailableError(
            "Content-based recommendation requires scikit-learn, which could not be loaded in this environment."
        )

    candidate_text = candidate.get("profile_text") or " ".join(candidate.get("skills", []))
    job_texts = [_job_text(job) for job in jobs]

    corpus = [candidate_text] + job_texts
    vectorizer = TfidfVectorizer(stop_words="english", min_df=1)
    matrix = vectorizer.fit_transform(corpus)
    similarities = cosine_similarity(matrix[0:1], matrix[1:]).flatten()

    results = []
    for job, tfidf_sim in zip(jobs, similarities):
        all_job_skills = list(dict.fromkeys(job.get("required_skills", []) + job.get("preferred_skills", [])))
        overlap = skill_overlap_ratio(candidate.get("skills", []), all_job_skills)
        blended = 0.5 * float(tfidf_sim) + 0.5 * overlap
        results.append(
            {
                "job_id": job.get("job_id") or job.get("title"),
                "title": job.get("title"),
                "score": round(blended, 4),
                "tfidf_similarity": round(float(tfidf_sim), 4),
                "skill_overlap": round(overlap, 4),
                "reason": _reason(job, candidate, overlap),
            }
        )

    results.sort(key=lambda r: (-r["score"], r["job_id"] or ""))
    return results[:top_k]


def recommend_jobs_semantic(candidate: dict, jobs: list[dict], top_k: int = 5) -> list[dict]:
    """Semantic-embedding variant of the same interface (uses the embedding service, which
    gracefully falls back to TF-IDF cosine similarity if sentence-transformers isn't installed)."""
    candidate_text = candidate.get("profile_text") or " ".join(candidate.get("skills", []))
    results = []
    for job in jobs:
        sim = semantic_similarity(candidate_text, _job_text(job))
        results.append(
            {
                "job_id": job.get("job_id") or job.get("title"),
                "title": job.get("title"),
                "score": round(sim, 4),
                "reason": f"Semantic similarity between your profile and this role's description: {round(sim * 100, 1)}%",
            }
        )
    results.sort(key=lambda r: (-r["score"], r["job_id"] or ""))
    return results[:top_k]


def _reason(job: dict, candidate: dict, overlap: float) -> str:
    all_job_skills = list(dict.fromkeys(job.get("required_skills", []) + job.get("preferred_skills", [])))
    cand_skills = set(candidate.get("skills", []))
    shared = [s for s in all_job_skills if s in cand_skills][:3]
    if shared:
        return f"Strong match for {', '.join(shared)} experience"
    return f"Overall profile similarity to this role ({round(overlap * 100)}% skill overlap)"
