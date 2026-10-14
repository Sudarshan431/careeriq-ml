"""Data access for MatchingResult / SkillGapRecord / Recommendation."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.matching import MatchingResult, SkillGapRecord
from app.db.models.recommendation import Recommendation


class MatchingRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_match_result(self, candidate_id: uuid.UUID, job_id: uuid.UUID, result: dict, model_version_id: uuid.UUID | None = None) -> MatchingResult:
        row = MatchingResult(
            candidate_id=candidate_id,
            job_id=job_id,
            model_version_id=model_version_id,
            overall_score=result["match_score"],
            skill_score=result["skill_score"],
            semantic_score=result.get("semantic_similarity_score"),
            experience_score=result["experience_score"],
            education_score=result["education_score"],
            location_score=result.get("location_score"),
            preference_score=result.get("preference_score"),
            explanation=result.get("explanation", {}),
        )
        gap = result.get("skill_gap", {})
        row.skill_gap = SkillGapRecord(
            matched_skills=gap.get("matched_skills", []),
            partially_matched_skills=gap.get("partially_matched_skills", []),
            critical_missing_skills=gap.get("critical_missing_skills", []),
            optional_missing_skills=gap.get("optional_missing_skills", []),
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def save_recommendations(self, candidate_id: uuid.UUID, recs: list[dict], strategy: str, model_version_id: uuid.UUID | None = None) -> list[Recommendation]:
        """Upserts by (candidate_id, job_id, strategy) to avoid duplicate rows on repeated calls."""
        saved = []
        for rec in recs:
            job_id = rec.get("job_id")
            if not job_id:
                continue
            stmt = select(Recommendation).where(
                Recommendation.candidate_id == candidate_id,
                Recommendation.job_id == job_id,
                Recommendation.strategy == strategy,
            )
            existing = self.db.execute(stmt).scalar_one_or_none()
            if existing:
                existing.score = rec["score"]
                saved.append(existing)
            else:
                row = Recommendation(
                    candidate_id=candidate_id, job_id=job_id, score=rec["score"],
                    strategy=strategy, model_version_id=model_version_id,
                )
                self.db.add(row)
                saved.append(row)
        self.db.commit()
        return saved
