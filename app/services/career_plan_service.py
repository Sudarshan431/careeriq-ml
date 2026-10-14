"""
Personalized career/learning plan service.

Built entirely on top of already-existing pieces -- no new matching or
skill logic here:
  - app.ml.matching.skill_gap.analyze_skill_gap        (matched/missing skills)
  - app.ml.matching.baseline.baseline_match             (job-readiness score)
  - app.ml.learning.learning_recommender                (priority + ordering)

This module's only new logic is grouping the ordered learning items into
milestones and generating a practice-project suggestion per item from the
candidate's *actual* existing skills (never fabricated technology names).
"""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.logging_config import get_logger, Timer
from app.db.repositories.candidate_repository import CandidateRepository
from app.db.repositories.job_repository import JobRepository
from app.db.repositories.learning_plan_repository import LearningPlanRepository
from app.ml.matching.baseline import baseline_match
from app.ml.matching.skill_gap import analyze_skill_gap
from app.ml.learning.learning_recommender import build_learning_recommendations

logger = get_logger(__name__)

_MILESTONE_LABELS = {"HIGH": "Milestone 1: Close critical gaps", "MEDIUM": "Milestone 2: Build on related skills", "LOW": "Milestone 3: Round out preferred skills"}


def _practice_suggestion(item: dict, candidate_skills: list[str]) -> str:
    """Suggests combining the new skill with the candidate's own existing skills --
    never invents a technology the candidate doesn't actually have."""
    anchors = [s for s in candidate_skills if s != item["skill"]][:2]
    if anchors:
        return f"Practice project: build something that combines {item['skill']} with your existing {', and '.join(anchors)} experience."
    return f"Practice project: build a small, focused project that uses {item['skill']} on its own."


def _group_into_milestones(items: list[dict], candidate_skills: list[str]) -> list[dict]:
    milestones: dict[str, list[dict]] = {}
    for item in items:
        milestones.setdefault(item["priority"], []).append(item)

    result = []
    for priority in ("HIGH", "MEDIUM", "LOW"):
        group = milestones.get(priority)
        if not group:
            continue
        result.append(
            {
                "label": _MILESTONE_LABELS[priority],
                "skills": [i["skill"] for i in group],
                "steps": [
                    {**i, "practice_suggestion": _practice_suggestion(i, candidate_skills)} for i in group
                ],
            }
        )
    return result


def _job_readiness_assessment(job_readiness_percent: float) -> str:
    if job_readiness_percent >= 85:
        return "Job-ready now -- strong alignment with this target."
    if job_readiness_percent >= 60:
        return "Close to job-ready -- closing the priority gaps below would meaningfully strengthen fit."
    if job_readiness_percent >= 35:
        return "Meaningful gaps remain -- following this plan builds toward readiness over time."
    return "Early stage for this target -- treat this as a longer-term learning roadmap, not a near-term application goal."


def generate_plan_for_job(db: Session, candidate_id: uuid.UUID, job_id: uuid.UUID, persist: bool = True) -> dict:
    candidate_repo = CandidateRepository(db)
    job_repo = JobRepository(db)

    candidate = candidate_repo.get_by_id(candidate_id)
    if candidate is None:
        raise NotFoundError("Candidate not found.")
    job = job_repo.get_by_id(job_id)
    if job is None:
        raise NotFoundError("Job not found.")

    with Timer(logger, "career_plan_generate"):
        candidate_input = candidate_repo.to_matching_input(candidate)
        job_input = job_repo.to_matching_input(job)

        gap = analyze_skill_gap(candidate_input["skills"], job_input["required_skills"], job_input["preferred_skills"])
        match = baseline_match(candidate_input, job_input)
        learning_items = build_learning_recommendations(candidate_input["skills"], gap)
        milestones = _group_into_milestones(learning_items, candidate_input["skills"])

        strengths = gap["matched_skills"] + gap["matched_preferred_skills"]
        summary = (
            f"Plan to close the gap toward {job.title}: {len(learning_items)} skill(s) to develop, "
            f"starting from {match['match_score']}% current alignment."
        )

        plan_dict = {
            "target_role": job.title,
            "target_job_id": str(job.id),
            "strengths": strengths,
            "job_readiness_percent": match["match_score"],
            "job_readiness_assessment": _job_readiness_assessment(match["match_score"]),
            "summary": summary,
            "milestones": milestones,
            "learning_items": learning_items,
        }

        if persist:
            plan_row = LearningPlanRepository(db).create(
                candidate_id=candidate_id, target_role=job.title, strengths=strengths,
                job_readiness_percent=match["match_score"], summary=summary,
                items=learning_items, job_id=job_id,
            )
            plan_dict["plan_id"] = str(plan_row.id)
            plan_dict["created_at"] = plan_row.created_at

    return plan_dict


def get_plan(db: Session, plan_id: uuid.UUID) -> dict:
    plan = LearningPlanRepository(db).get_by_id(plan_id)
    if plan is None:
        raise NotFoundError("Career plan not found.")
    return _plan_row_to_dict(plan)


def list_plans_for_candidate(db: Session, candidate_id: uuid.UUID) -> list[dict]:
    plans = LearningPlanRepository(db).list_by_candidate(candidate_id)
    return [_plan_row_to_dict(p) for p in plans]


def _plan_row_to_dict(plan) -> dict:
    items = [
        {
            "skill": i.skill, "priority": i.priority, "difficulty": i.difficulty, "reason": i.reason,
            "prerequisite_skills": i.prerequisite_skills, "suggested_resource_types": i.suggested_resource_types,
            "recommended_order": i.step_order, "is_completed": i.is_completed,
        }
        for i in plan.items
    ]
    return {
        "plan_id": str(plan.id),
        "target_role": plan.target_role,
        "target_job_id": str(plan.job_id) if plan.job_id else None,
        "strengths": plan.strengths,
        "job_readiness_percent": plan.job_readiness_percent,
        "job_readiness_assessment": _job_readiness_assessment(plan.job_readiness_percent) if plan.job_readiness_percent is not None else None,
        "summary": plan.summary,
        "milestones": _group_into_milestones(items, plan.strengths),
        "learning_items": items,
        "created_at": plan.created_at,
    }
