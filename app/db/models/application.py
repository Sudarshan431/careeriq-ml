"""Candidate job applications -- also the extension point for future collaborative-filtering
signals (applied/saved/viewed/rejected), referenced as RecommendationSignal in the ML layer."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base

# Valid values for Application.status. Kept as a plain String column (not a
# Postgres ENUM type) so extending the vocabulary never risks the
# CREATE TYPE double-creation issue already hit once with user_role --
# validity is enforced at the Pydantic/service layer instead.
APPLICATION_STATUSES = ("APPLIED", "REVIEWING", "SHORTLISTED", "REJECTED", "INTERVIEW", "HIRED")


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("candidate_id", "job_id", name="uq_application_candidate_job"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="APPLIED", server_default="APPLIED")

    # Match score captured at application time (see app/services/application_service.py) --
    # never recomputed on subsequent reads, so a recruiter reviewing an
    # applicant later sees the score as of when they applied.
    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("model_versions.id", ondelete="SET NULL"), nullable=True
    )

    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
