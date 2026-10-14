"""Small generic text helpers used across services."""
from __future__ import annotations


def truncate(text: str | None, max_chars: int = 500) -> str | None:
    if text is None:
        return None
    return text if len(text) <= max_chars else text[:max_chars].rsplit(" ", 1)[0] + "..."


def safe_join(items: list[str], sep: str = ", ") -> str:
    return sep.join(i for i in items if i)
