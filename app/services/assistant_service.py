"""
AI Career Assistant service. Orchestrates (never duplicates):
  1. app.ai.context_builder  -- pulls real, authorized CareerIQ data
  2. app.ai.prompt_builder   -- turns that into a grounded prompt
  3. app.ai.llm_provider     -- calls the configured LLM (or raises a
     structured ModelNotAvailableError if none is configured/reachable)
  4. app.db.repositories.assistant_repository -- persists the conversation

Authorization is enforced by the route (see app.api.assistant_routes),
which resolves candidate_id from the caller's own JWT -- this service
never trusts a client-supplied candidate_id.
"""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.ai.context_builder import build_context
from app.ai.llm_provider import get_llm_provider
from app.ai.prompt_builder import build_messages
from app.core.logging_config import Timer, get_logger
from app.db.repositories.assistant_repository import AssistantRepository

logger = get_logger(__name__)


def chat(
    db: Session,
    candidate_id: uuid.UUID,
    message: str,
    job_id: uuid.UUID | None = None,
    conversation_id: uuid.UUID | None = None,
) -> dict:
    assistant_repo = AssistantRepository(db)

    with Timer(logger, "assistant_chat"):
        context = build_context(db, candidate_id, job_id, user_question=message)

        conversation = assistant_repo.get_or_create_conversation(candidate_id, job_id, conversation_id)
        history = [{"role": m.role, "content": m.content} for m in assistant_repo.list_messages(conversation.id)]

        assistant_repo.add_message(conversation, role="user", content=message)

        provider = get_llm_provider()
        messages = build_messages(message, context, history)
        answer = provider.chat(messages)

        assistant_repo.add_message(conversation, role="assistant", content=answer, context_snapshot=context)

    logger.info("assistant_chat: conversation_id=%s job_id=%s answer_length=%d", conversation.id, job_id, len(answer))

    return {
        "answer": answer,
        "context": context,
        "conversation_id": str(conversation.id),
    }
