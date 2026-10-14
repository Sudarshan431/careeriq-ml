"""
Process-lifetime cache of scikit-learn's text/TF-IDF capability
(`TfidfVectorizer` + `cosine_similarity`), shared by every call site that
would otherwise import them directly.

Why this exists: under some locked-down environments (e.g. Windows
Application Control / WDAC policies blocking a native .pyd such as
scipy's `_ni_label` or `_rotation_cy`), `import sklearn...` doesn't just
fail -- the OS intercepting the blocked native extension load has been
observed taking anywhere from seconds to multiple *minutes* per attempt.
A failed import is not cached by Python itself (unlike a successful one,
which sys.modules caches), so naively wrapping the import in a bare
try/except on every request means every request that touches
scikit-learn re-pays that full multi-second-to-multi-minute cost, even
once the environment is known to be broken.

This module runs the actual import exactly once per process, caches
whichever outcome it gets (available -- with direct references to the
classes, so callers never need to re-import at all -- or unavailable, with
the reason), and every call after the first is an in-memory dict/bool
lookup: no import statement, no OS-level DLL probe, no meaningful latency.

Deliberately NOT persisted to disk or the database: a process restart
(e.g. after an admin allow-lists the DLL, or the app is redeployed
somewhere the extension isn't blocked) re-runs the real check from
scratch, so a fixed environment recovers automatically without any manual
cache-busting step.
"""
from __future__ import annotations

import threading

from app.core.logging_config import get_logger

logger = get_logger(__name__)

_lock = threading.Lock()
_checked = False
_available = False
_reason: str | None = None
_TfidfVectorizer = None
_cosine_similarity = None


def check_sklearn_text_capability():
    """
    Returns (available, TfidfVectorizer, cosine_similarity, reason).

    `TfidfVectorizer`/`cosine_similarity` are the real, already-imported
    classes when available=True (nothing else needs to import them again);
    both are None when available=False, and `reason` explains why.

    The actual `import sklearn...` is attempted at most once per process,
    regardless of how many times this function is called or how many
    threads call it concurrently.
    """
    global _checked, _available, _reason, _TfidfVectorizer, _cosine_similarity

    if _checked:
        return _available, _TfidfVectorizer, _cosine_similarity, _reason

    with _lock:
        if _checked:  # another thread may have finished the check while we waited for the lock
            return _available, _TfidfVectorizer, _cosine_similarity, _reason

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            _TfidfVectorizer = TfidfVectorizer
            _cosine_similarity = cosine_similarity
            _available = True
            _reason = None
            logger.info("scikit-learn text/TF-IDF capability check: available (cached for process lifetime)")
        except (ImportError, OSError) as e:
            # Application Control / WDAC blocking a native extension can
            # surface as either ImportError or OSError depending on how far
            # the loader got before being intercepted -- handle both the
            # same way. Logged once, here, on the single real attempt --
            # never again for the rest of the process's life.
            _available = False
            _reason = f"{type(e).__name__}: {e}"
            logger.error(
                "scikit-learn unavailable; caching this result for the process lifetime so no "
                "further requests re-attempt the native import. Reason: %s",
                _reason,
            )
        finally:
            _checked = True

    return _available, _TfidfVectorizer, _cosine_similarity, _reason
