"""
In-process, DB-backed Retriever implementation (see retriever.py for the
interface). Reuses the existing embedding backend
(app.ml.embeddings.embedding_service) unchanged -- no new embedding model,
no new dependency.

IMPORTANT correctness note on TF-IDF fallback mode: embedding_service falls
back to fitting a fresh TfidfVectorizer per call when sentence-transformers
isn't installed (the actual condition in every environment this project has
been developed in so far). A freshly-fit TF-IDF vector space differs between
calls -- a persisted TF-IDF embedding from one `index()` call is NOT
comparable via cosine similarity to a different call's freshly-embedded
query vector; the vocabularies/IDF weights differ. Comparing them anyway
would silently return wrong "nearest neighbors".

So: at search time, this implementation re-embeds the query together with
the current candidate chunk texts in a single embed_texts() call, computing
similarity in a shared, valid vector space every time -- correct under both
the TF-IDF fallback (freshly consistent each call) and a real
sentence-transformer backend (stable regardless of batching). The persisted
`embedding` column is kept for audit/future-optimization purposes but is
NOT what search() scores against while the fallback is active; see
`embedding_backend` on each chunk for which mode produced the stored value.
This trade-off costs re-embedding on every search instead of reusing stored
vectors, which is fine at this project's corpus size (jobs + career
snippets, not web-scale) and is the honest, correct choice given the
constraint, not a shortcut.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.db.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.ml.embeddings.embedding_service import embed_texts, embedding_backend
from app.rag.access import is_document_visible
from app.rag.chunker import chunk_text
from app.rag.retriever import RetrievedChunk
from app.rag.similarity import rank_texts_by_similarity

logger = get_logger(__name__)


class SimpleVectorRetriever:
    def __init__(self, db: Session):
        self.db = db

    def index(self, *, source_type: str, source_id: str | None, text: str, title: str | None = None,
              candidate_id: uuid.UUID | None = None, job_id: uuid.UUID | None = None, metadata: dict | None = None) -> str:
        chunks = chunk_text(text)
        if not chunks:
            raise ValueError("Cannot index empty or whitespace-only text.")

        backend = embedding_backend()
        embeddings = embed_texts(chunks)

        document = KnowledgeDocument(
            source_type=source_type, source_id=source_id, candidate_id=candidate_id,
            job_id=job_id, title=title, doc_metadata=metadata or {},
        )
        document.chunks = [
            KnowledgeChunk(chunk_index=i, text=chunk, embedding=embeddings[i].tolist(), embedding_backend=backend)
            for i, chunk in enumerate(chunks)
        ]
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        logger.info("rag_index document_id=%s source_type=%s chunks=%d backend=%s", document.id, source_type, len(chunks), backend)
        return str(document.id)

    def search(self, query: str, *, top_k: int = 5, source_types: list[str] | None = None,
               candidate_id: uuid.UUID | None = None, requesting_user_is_admin: bool = False) -> list[RetrievedChunk]:
        if not query or not query.strip():
            return []

        stmt = select(KnowledgeChunk, KnowledgeDocument).join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)

        # Authorization enforced at the query itself, not just filtered
        # after the fact: a private document (candidate_id set) is only
        # ever included when it belongs to the requesting candidate, or the
        # requester is ADMIN. Public documents (candidate_id IS NULL) are
        # always eligible.
        if not requesting_user_is_admin:
            if candidate_id is not None:
                stmt = stmt.where((KnowledgeDocument.candidate_id.is_(None)) | (KnowledgeDocument.candidate_id == candidate_id))
            else:
                stmt = stmt.where(KnowledgeDocument.candidate_id.is_(None))

        if source_types:
            stmt = stmt.where(KnowledgeDocument.source_type.in_(source_types))

        rows = self.db.execute(stmt).all()
        # Defense in depth: re-verify every returned row against the pure
        # authorization predicate even though the SQL above already filtered.
        rows = [r for r in rows if is_document_visible(r[1].candidate_id, candidate_id, requesting_user_is_admin)]
        if not rows:
            return []

        candidate_texts = [row[0].text for row in rows]
        ranked = rank_texts_by_similarity(query, candidate_texts, top_k=top_k)

        return [
            RetrievedChunk(
                chunk_id=str(rows[i][0].id), document_id=str(rows[i][1].id), text=rows[i][0].text,
                score=round(score, 4), source_type=rows[i][1].source_type,
                source_id=rows[i][1].source_id, title=rows[i][1].title, metadata=rows[i][1].doc_metadata,
            )
            for i, score in ranked
        ]

    def delete(self, document_id: str) -> bool:
        document = self.db.get(KnowledgeDocument, uuid.UUID(document_id))
        if document is None:
            return False
        self.db.delete(document)
        self.db.commit()
        return True

    def health_check(self) -> bool:
        try:
            self.db.execute(select(KnowledgeDocument.id).limit(1))
            embed_texts(["health check"])
            return True
        except Exception as e:
            logger.warning("rag_health_check failed: %s: %s", type(e).__name__, e)
            return False
