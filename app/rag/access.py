"""
Retrieval-time authorization predicate. Pure function, no DB -- so the
single most security-critical RAG property (a candidate must never
retrieve another candidate's private documents) is directly unit-testable.

SimpleVectorRetriever.search() enforces this twice, deliberately:
  1. in the SQL WHERE clause (so private rows are never even loaded), and
  2. via this function as a defense-in-depth re-check on every row that
     comes back -- so a future refactor that accidentally weakens the SQL
     filter still cannot leak a private chunk.
"""
from __future__ import annotations

import uuid


def is_document_visible(
    document_candidate_id: uuid.UUID | None,
    requesting_candidate_id: uuid.UUID | None,
    requesting_user_is_admin: bool = False,
) -> bool:
    if requesting_user_is_admin:
        return True
    if document_candidate_id is None:
        return True  # public document (e.g. a job posting)
    return requesting_candidate_id is not None and document_candidate_id == requesting_candidate_id
