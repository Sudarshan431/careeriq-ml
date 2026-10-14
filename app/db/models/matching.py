"""Persisted matching results and skill-gap breakdowns."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class MatchingResult(Base):
    __tablename__ = "matching_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    model_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("model_versions.id", ondelete="SET NULL"), nullable=True)

    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    skill_score: Mapped[float] = mapped_column(Float, nullable=False)
    semantic_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    experience_score: Mapped[float] = mapped_column(Float, nullable=False)
    education_score: Mapped[float] = mapped_column(Float, nullable=False)
    location_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    preference_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    explanation: Mapped[dict] = mapped_column(JSON, nullable=False)  # strengths/recommendation -- structured, not free text we'd want to query on
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    skill_gap: Mapped["SkillGapRecord"] = relationship(back_populates="matching_result", uselist=False, cascade="all, delete-orphan")


class SkillGapRecord(Base):
    __tablename__ = "skill_gaps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    matching_result_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("matching_results.id", ondelete="CASCADE"), unique=True, nullable=False)

    matched_skills: Mapped[list] = mapped_column(JSON, default=list)
    partially_matched_skills: Mapped[list] = mapped_column(JSON, default=list)
    critical_missing_skills: Mapped[list] = mapped_column(JSON, default=list)
    optional_missing_skills: Mapped[list] = mapped_column(JSON, default=list)

    matching_result: Mapped["MatchingResult"] = relationship(back_populates="skill_gap")
