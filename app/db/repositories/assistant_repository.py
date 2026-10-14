"""Data access for AssistantConversation / AssistantMessage."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.assistant import AssistantConversation, AssistantMessage


class AssistantRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_conversation(self, conversation_id: uuid.UUID) -> AssistantConversation | None:
        return self.db.get(AssistantConversation, conversation_id)

    def get_or_create_conversation(self, candidate_id: uuid.UUID, job_id: uuid.UUID | None, conversation_id: uuid.UUID | None) -> AssistantConversation:
        if conversation_id is not None:
            existing = self.get_conversation(conversation_id)
            if existing is not None and existing.candidate_id == candidate_id:
                return existing
        conversation = AssistantConversation(candidate_id=candidate_id, job_id=job_id)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def add_message(self, conversation: AssistantConversation, role: str, content: str, context_snapshot: dict | None = None) -> AssistantMessage:
        message = AssistantMessage(conversation_id=conversation.id, role=role, content=content, context_snapshot=context_snapshot)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def list_messages(self, conversation_id: uuid.UUID) -> list[AssistantMessage]:
        stmt = select(AssistantMessage).where(AssistantMessage.conversation_id == conversation_id).order_by(AssistantMessage.created_at)
        return list(self.db.execute(stmt).scalars().all())
