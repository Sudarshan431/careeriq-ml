from __future__ import annotations
import uuid
from typing import Any, Dict, Optional
from pydantic import BaseModel


class AssistantChatRequest(BaseModel):
    message: str
    job_id: Optional[uuid.UUID] = None
    conversation_id: Optional[uuid.UUID] = None


class AssistantChatResponse(BaseModel):
    answer: str
    context: Dict[str, Any]
    conversation_id: str
