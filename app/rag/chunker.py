"""
Deterministic chunking for RAG ingestion. No randomness, no LLM calls --
same input always produces the same chunks, which matters for the
"duplicate chunks" and "malformed documents" test cases and for keeping
re-ingestion idempotent.

Strategy: split on paragraph boundaries first (natural semantic units for
job descriptions / career text), then greedily pack paragraphs into chunks
up to max_chars, splitting an over-long single paragraph on sentence
boundaries as a fallback. This avoids both "arbitrarily huge chunks" and
pointlessly tiny one-line chunks.
"""
from __future__ import annotations

import re

_PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n+")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

DEFAULT_MAX_CHARS = 800
DEFAULT_MIN_CHARS = 40  # avoid a trailing near-empty chunk merging awkwardly


def chunk_text(text: str, max_chars: int = DEFAULT_MAX_CHARS) -> list[str]:
    if not text or not text.strip():
        return []

    paragraphs = [p.strip() for p in _PARAGRAPH_SPLIT_RE.split(text) if p.strip()]
    if not paragraphs:
        return []

    chunks: list[str] = []
    current = ""

    def flush():
        nonlocal current
        if current.strip():
            chunks.append(current.strip())
        current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue

        # Current buffer is full -- flush it, then handle this paragraph on its own.
        flush()
        if len(paragraph) <= max_chars:
            current = paragraph
            continue

        # A single paragraph longer than max_chars -- split on sentences.
        sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(paragraph) if s.strip()]
        for sentence in sentences:
            candidate = f"{current} {sentence}".strip() if current else sentence
            if len(candidate) <= max_chars:
                current = candidate
            else:
                flush()
                current = sentence[:max_chars]  # a single sentence longer than max_chars: hard-truncate, don't silently drop it

    flush()

    # Merge a too-small trailing chunk into the previous one rather than
    # leaving a near-empty fragment as its own retrievable unit -- but ONLY
    # if the merged chunk still fits the size budget. (An earlier version
    # merged unconditionally and could push a chunk past max_chars; the size
    # budget is the invariant, a tidy tail is just a nicety.)
    if len(chunks) >= 2 and len(chunks[-1]) < DEFAULT_MIN_CHARS:
        merged = f"{chunks[-2]}\n\n{chunks[-1]}"
        if len(merged) <= max_chars:
            chunks[-2] = merged
            chunks.pop()

    return chunks
