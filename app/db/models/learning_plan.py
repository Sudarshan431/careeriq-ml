"""
Personalized career/learning plan -- persists the output of
app.services.career_plan_service (which itself is built on the existing
skill-gap + learning-recommendation engines, no duplicate logic) so a
candidate's plan survives across sessions and can be revisited.

LearningPlanItem stores each step's content (skill, priority, difficulty,
reason, prerequisites, resource types) as JSON rather than re-normalizing
every field into its own column -- this is genuinely derived/denormalized
output from the ML layer, not independently-editable structured data, so a
JSON column is the right call here (see project convention: "JSON fields
can be used only where they are genuinely appropriate").
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class LearningPlan(Base):
    __tablename__ = "learning_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)

    target_role: Mapped[str] = mapped_column(String(200), nullable=False)  # job title, or a free-text career target when job_id is None
    strengths: Mapped[list] = mapped_column(JSON, default=list)  # candidate's matched/current skills relevant to the target
    job_readiness_percent: Mapped[float | None] = mapped_column(Float, nullable=True)  # the underlying match_score, denormalized for quick display
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    items: Mapped[list["LearningPlanItem"]] = relationship(back_populates="plan", cascade="all, delete-orphan", order_by="LearningPlanItem.step_order")


class LearningPlanItem(Base):
    __tablename__ = "learning_plan_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("learning_plans.id", ondelete="CASCADE"), nullable=False, index=True)

    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    skill: Mapped[str] = mapped_column(String(120), nullable=False)
    priority: Mapped[str] = mapped_column(String(10), nullable=False)  # HIGH | MEDIUM | LOW
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)  # FOUNDATIONAL | STANDARD | FOCUSED
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    prerequisite_skills: Mapped[list] = mapped_column(JSON, default=list)
    suggested_resource_types: Mapped[list] = mapped_column(JSON, default=list)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)  # extension point for progress tracking -- the project has none yet

    plan: Mapped["LearningPlan"] = relationship(back_populates="items")
