"""
AI Career Assistant chat endpoint.

Security: candidate_id is ALWAYS resolved from the caller's own JWT (same
pattern as GET /api/v1/candidates/me) -- the request body never accepts a
client-supplied candidate_id, so there is no IDOR surface here: a
candidate can only ever chat about their own data, full stop.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_candidate
from app.auth.models import CurrentUser
from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.db.repositories.candidate_repository import CandidateRepository
from app.schemas.assistant import AssistantChatRequest, AssistantChatResponse
from app.services.assistant_service import chat

router = APIRouter(prefix="/api/v1/assistant", tags=["assistant"])


@router.post(
    "/chat",
    response_model=AssistantChatResponse,
    summary="Ask the AI Career Assistant a question grounded in the caller's own CareerIQ data",
    description="The assistant only ever answers from real, structured CareerIQ context (skills, match "
    "score, skill gaps) for the authenticated candidate -- it cannot access another candidate's data, and "
    "it never invents candidate facts. Returns the exact structured context used, alongside the answer. "
    "If no LLM provider is configured/reachable, returns a 503 without affecting any other endpoint.",
    responses={503: {"description": "AI Career Assistant unavailable (not configured, or the provider call failed)"}},
)
def assistant_chat_endpoint(payload: AssistantChatRequest, db: Session = Depends(get_db), current_user: CurrentUser = Depends(require_candidate)):
    candidate = CandidateRepository(db).get_by_user_id(current_user.id)
    if candidate is None:
        raise NotFoundError("Candidate profile not found.")
    return chat(db, candidate.id, payload.message, job_id=payload.job_id, conversation_id=payload.conversation_id)
