"""Service layer for resume analysis. API routes call this, never NLP internals directly."""
from __future__ import annotations

from app.core.config import settings
from app.core.exceptions import FileTooLargeError, UnsupportedFileTypeError
from app.core.logging_config import get_logger, Timer
from app.nlp.resume_parser import parse_resume

logger = get_logger(__name__)


def analyze_resume(file_bytes: bytes, filename: str) -> dict:
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise FileTooLargeError(f"File exceeds {settings.max_file_size_mb}MB limit.")

    allowed = [e.strip() for e in settings.allowed_extensions.split(",")]
    ext = "." + filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext not in allowed:
        raise UnsupportedFileTypeError(f"Unsupported file extension: {ext}")

    with Timer(logger, "resume_analyze"):
        profile = parse_resume(file_bytes, filename)
    return profile
