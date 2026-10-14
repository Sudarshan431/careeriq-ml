"""File-handling helpers: validation, safe filename handling."""
from __future__ import annotations

import re
from pathlib import Path

_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9_.\-]")


def sanitize_filename(filename: str) -> str:
    """Strips path components and unsafe characters to prevent path traversal."""
    name = Path(filename).name
    return _SAFE_NAME_RE.sub("_", name)


def has_allowed_extension(filename: str, allowed_extensions: list[str]) -> bool:
    ext = "." + filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    return ext in [e.lower() for e in allowed_extensions]


def file_size_mb(file_bytes: bytes) -> float:
    return len(file_bytes) / (1024 * 1024)
