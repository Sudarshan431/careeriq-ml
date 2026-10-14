"""
Structured logging setup.

Rules enforced by convention throughout the codebase (see docstrings on
callers): never log full resume/job text, credentials, or tokens. Log
request id, endpoint, operation, latency, and error class/message only.
"""
from __future__ import annotations

import logging
import sys
import time
import uuid
from contextvars import ContextVar
from typing import Optional

from app.core.config import settings

_request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id_ctx.get()
        return True


def new_request_id() -> str:
    rid = uuid.uuid4().hex[:12]
    _request_id_ctx.set(rid)
    return rid


def get_request_id() -> str:
    return _request_id_ctx.get()


def configure_logging() -> None:
    level = getattr(logging, str(settings.log_level).upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | rid=%(request_id)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.filters:
        logger.addFilter(RequestIdFilter())
    return logger


class Timer:
    """Context manager to measure and log operation latency in milliseconds."""

    def __init__(self, logger: logging.Logger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start: Optional[float] = None
        self.elapsed_ms: float = 0.0

    def __enter__(self) -> "Timer":
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.elapsed_ms = (time.perf_counter() - self.start) * 1000
        if exc_type is None:
            self.logger.info("operation=%s latency_ms=%.2f", self.operation, self.elapsed_ms)
        else:
            self.logger.error(
                "operation=%s latency_ms=%.2f failed error=%s", self.operation, self.elapsed_ms, exc_type.__name__
            )
