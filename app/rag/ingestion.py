"""
Ingestion entry points -- what actually gets indexed into the knowledge
store, and when. Kept separate from the retriever itself so indexing
policy (what counts as a document, when to (re-)index it) can change
without touching retrieval or storage code.

Current source: persisted Job rows (real, already-existing CareerIQ data --
required/preferred skills + description), indexed as public documents
(candidate_id=None) since job postings aren't private. This is deliberately
the only source for now rather than a fabricated generic "career knowledge"
corpus -- see Phase 1 requirement not to invent unsupported content.
Candidate-specific private knowledge (e.g. a candidate's own notes) is a
documented extension point: pass candidate_id to index_job_description's
sibling functions the same way once that data exists.
"""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.logging_config import get_logger
from app.rag.simple_vector_retriever import SimpleVectorRetriever

logger = get_logger(__name__)


def index_job_description(db: Session, job) -> str:
    """
    Indexes a persisted Job (see app.db.models.job.Job) as a public
    knowledge document. Called after a job is created (app.api.recruiter_routes)
    so RAG search results stay current with the actual job pool -- no
    separate batch reindex step is required for this source.
    """
    retriever = SimpleVectorRetriever(db)
    required = ", ".join(s.skill_name for s in job.skills if s.requirement_type == "required")
    preferred = ", ".join(s.skill_name for s in job.skills if s.requirement_type == "preferred")
    text = f"{job.title}\n\n{job.description}\n\nRequired skills: {required}\nPreferred skills: {preferred}"
    document_id = retriever.index(
        source_type="job_description",
        source_id=str(job.id),
        text=text,
        title=job.title,
        job_id=job.id,
        metadata={"location": job.location, "employment_type": job.employment_type},
    )
    logger.info("rag_ingest job_id=%s document_id=%s", job.id, document_id)
    return document_id
