from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class RetrievedChunkResponse(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    score: float
    source_type: str
    source_id: Optional[str] = None
    title: Optional[str] = None
    metadata: Dict[str, Any] = {}


class RagSearchRequest(BaseModel):
    query: str
    top_k: int = 5
    source_types: Optional[List[str]] = None


class RagSearchResponse(BaseModel):
    results: List[RetrievedChunkResponse]


class RagHealthResponse(BaseModel):
    available: bool
