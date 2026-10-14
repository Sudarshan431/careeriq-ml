"""
Best-effort retrieval for the assistant's context. Lives in the rag
package (not in app.ai.context_builder) so the fallback behavior --
"if retrieval is unavailable for ANY reason, return no retrieved
knowledge and let the non-RAG assistant carry on" -- is independently
testable, and so this module has no module-level database import: the
retriever (and with it SQLAlchemy) is imported lazily inside the
function, so an unavailable backend is caught right here instead of
breaking whatever imported this module.
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from app.core.logging_config import get_logger

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = get_logger(__name__)


def retrieve_knowledge(db: "Session", query: str, candidate_id: uuid.UUID, top_k: int = 3) -> list[dict]:
    try:
        from app.rag.simple_vector_retriever import SimpleVectorRetriever

        retriever = SimpleVectorRetriever(db)
        chunks = retriever.search(query, top_k=top_k, candidate_id=candidate_id)
        return [
            {"text": c.text, "source_type": c.source_type, "source_id": c.source_id, "title": c.title, "relevance_score": c.score}
            for c in chunks
        ]
    except Exception as e:
        logger.warning("rag_retrieval_unavailable, falling back to non-RAG context: %s: %s", type(e).__name__, e)
        return []
