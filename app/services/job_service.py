"""Service layer for job description analysis."""
from __future__ import annotations

from app.core.exceptions import EmptyDocumentError
from app.core.logging_config import get_logger, Timer
from app.nlp.job_parser import parse_job_description

logger = get_logger(__name__)


def analyze_job(raw_text: str) -> dict:
    if not raw_text or not raw_text.strip():
        raise EmptyDocumentError("Job description text is empty.")
    with Timer(logger, "job_analyze"):
        return parse_job_description(raw_text)
