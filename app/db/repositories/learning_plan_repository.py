"""Data access for LearningPlan / LearningPlanItem."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.learning_plan import LearningPlan, LearningPlanItem


class LearningPlanRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, plan_id: uuid.UUID) -> LearningPlan | None:
        return self.db.get(LearningPlan, plan_id)

    def list_by_candidate(self, candidate_id: uuid.UUID) -> list[LearningPlan]:
        stmt = select(LearningPlan).where(LearningPlan.candidate_id == candidate_id).order_by(LearningPlan.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def create(
        self,
        candidate_id: uuid.UUID,
        target_role: str,
        strengths: list[str],
        job_readiness_percent: float | None,
        summary: str | None,
        items: list[dict],
        job_id: uuid.UUID | None = None,
    ) -> LearningPlan:
        plan = LearningPlan(
            candidate_id=candidate_id, job_id=job_id, target_role=target_role,
            strengths=strengths, job_readiness_percent=job_readiness_percent, summary=summary,
        )
        plan.items = [
            LearningPlanItem(
                step_order=item["recommended_order"],
                skill=item["skill"],
                priority=item["priority"],
                difficulty=item["difficulty"],
                reason=item["reason"],
                prerequisite_skills=item["prerequisite_skills"],
                suggested_resource_types=item["suggested_resource_types"],
            )
            for item in items
        ]
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return plan
