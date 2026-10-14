"""
RAG knowledge store: documents (a job description, a resume, a learning
resource, etc.) split into deterministic chunks, each with its own
embedding. Deliberately NOT a dedicated vector database -- per the task's
own guidance ("do not introduce a vector database merely because it is
fashionable"), this project has no existing vector-store dependency, and
the corpus size here (jobs + career-knowledge snippets, not millions of
web documents) does not justify adding one. Embeddings are stored as a
plain JSON array of floats and searched via in-process cosine similarity
(see app/rag/simple_vector_retriever.py) -- the exact same embedding
backend already used for matching (app.ml.embeddings.embedding_service),
reused rather than duplicated.

The `Retriever` abstraction in app/rag/retriever.py is what the rest of
the app depends on, not this storage choice directly -- swapping in a real
vector database (pgvector, a managed service) later means implementing
that one interface, not touching any caller.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # e.g. "job_description", "career_knowledge", "learning_resource" -- open vocabulary,
    # validated at the ingestion call site (app/rag/ingestion.py), not by a DB constraint,
    # so new source types don't need a migration.
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)  # e.g. the Job.id this came from

    # Ownership scoping for retrieval-time authorization (see app/rag/simple_vector_retriever.py):
    # a document tied to a candidate_id is only ever retrievable by that candidate (or ADMIN).
    # NULL means "not candidate-private" (e.g. a public job description or generic career knowledge).
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=True, index=True)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True, index=True)

    title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    doc_metadata: Mapped[dict] = mapped_column(JSON, default=dict)  # small, genuinely free-form -> JSON is appropriate here

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    chunks: Mapped[list["KnowledgeChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan", order_by="KnowledgeChunk.chunk_index")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (UniqueConstraint("document_id", "chunk_index", name="uq_chunk_document_index"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # Plain JSON float array -- see module docstring for why not a native vector column.
    embedding: Mapped[list] = mapped_column(JSON, nullable=False)
    embedding_backend: Mapped[str] = mapped_column(String(30), nullable=False)  # "sentence-transformer" | "tfidf-fallback" -- see embedding_service

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["KnowledgeDocument"] = relationship(back_populates="chunks")
