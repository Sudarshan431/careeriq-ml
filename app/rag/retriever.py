"""
Retrieval abstraction. Every caller (context_builder, agent tools) depends
on this interface, never on a concrete storage/search implementation --
see app/rag/simple_vector_retriever.py for the one implementation this
project currently ships, and the module docstring on
app/db/models/knowledge.py for why it's DB+in-process rather than a
dedicated vector database.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    text: str
    score: float
    source_type: str
    source_id: str | None
    title: str | None
    metadata: dict = field(default_factory=dict)


class Retriever(Protocol):
    def index(self, *, source_type: str, source_id: str | None, text: str, title: str | None = None,
              candidate_id: uuid.UUID | None = None, job_id: uuid.UUID | None = None, metadata: dict | None = None) -> str:
        """Chunks + embeds + persists `text` as a new KnowledgeDocument. Returns the document_id."""
        ...

    def search(self, query: str, *, top_k: int = 5, source_types: list[str] | None = None,
               candidate_id: uuid.UUID | None = None, requesting_user_is_admin: bool = False) -> list[RetrievedChunk]:
        """
        Returns the top_k most relevant chunks for `query`.

        Authorization is enforced HERE, not just by the caller: any chunk
        whose document has a non-null candidate_id is only returned when
        `candidate_id` matches it (or `requesting_user_is_admin` is True).
        Chunks with a null candidate_id (public job descriptions, generic
        career knowledge) are always eligible.
        """
        ...

    def delete(self, document_id: str) -> bool:
        """Deletes a document and all its chunks. Returns False if it didn't exist."""
        ...

    def health_check(self) -> bool:
        """Returns True if the retrieval backend is currently usable (DB reachable, embedding backend loadable)."""
        ...
