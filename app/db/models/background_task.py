"""
Background task tracking (Phase 6). No Redis/Celery dependency is added --
inspection confirmed neither is an existing project dependency and this
sandbox cannot install new packages, so the simplest production-appropriate
implementation per the task's own guidance is: a DB-backed task table +
an in-process thread-pool runner (see app/jobs/task_queue.py), behind the
same `TaskQueue` interface a real Redis+RQ/Celery backend would implement
later -- callers (routes/services) never change when that swap happens.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base

TASK_STATUSES = ("QUEUED", "RUNNING", "COMPLETED", "FAILED")


class BackgroundTask(Base):
    __tablename__ = "background_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # e.g. "career_plan_generation"
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="QUEUED", server_default="QUEUED")

    # Who requested it, for ownership checks on GET /tasks/{id} -- not a
    # FK to a specific domain table since task_type varies; validated by
    # the service layer against the caller's own identity instead.
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # Idempotency: a hash of (task_type, payload) so re-submitting the same
    # request while one is already queued/running returns the existing task
    # instead of enqueuing a duplicate expensive job.
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
