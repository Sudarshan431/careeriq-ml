"""
RAG retrieval endpoints. Search is candidate-scoped: a candidate's query
only ever returns public documents (e.g. job postings) plus documents
explicitly tied to their own candidate_id -- enforced inside
SimpleVectorRetriever.search() itself (retrieval-time authorization),
not only by this route.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_authenticated
from app.auth.models import CurrentUser, Role
from app.db.session import get_db
from app.db.repositories.candidate_repository import CandidateRepository
from app.rag.simple_vector_retriever import SimpleVectorRetriever
from app.schemas.rag import RagHealthResponse, RagSearchRequest, RagSearchResponse

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])


@router.post(
    "/search",
    response_model=RagSearchResponse,
    summary="Semantic search over the CareerIQ knowledge store",
    description="Candidate-scoped: only public documents (e.g. indexed job postings) and documents "
    "belonging to the caller's own candidate_id are ever returned. ADMIN sees everything.",
)
def search_endpoint(payload: RagSearchRequest, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_authenticated)):
    candidate = CandidateRepository(db).get_by_user_id(current_user.id)
    candidate_id = candidate.id if candidate else None
    retriever = SimpleVectorRetriever(db)
    results = retriever.search(
        payload.query, top_k=payload.top_k, source_types=payload.source_types,
        candidate_id=candidate_id, requesting_user_is_admin=(current_user.role == Role.ADMIN),
    )
    return {
        "results": [
            {
                "chunk_id": r.chunk_id, "document_id": r.document_id, "text": r.text, "score": r.score,
                "source_type": r.source_type, "source_id": r.source_id, "title": r.title, "metadata": r.metadata,
            }
            for r in results
        ]
    }


@router.get(
    "/health",
    response_model=RagHealthResponse,
    summary="Check whether the RAG retrieval backend is currently usable",
)
def health_endpoint(db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_authenticated)):
    retriever = SimpleVectorRetriever(db)
    return {"available": retriever.health_check()}
