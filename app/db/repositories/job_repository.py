"""Data access for Job + JobSkill."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.job import Job, JobSkill


class JobRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, job_id: uuid.UUID) -> Job | None:
        return self.db.get(Job, job_id)

    def list_all(self, limit: int = 100) -> list[Job]:
        stmt = select(Job).order_by(Job.created_at.desc()).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def create_from_parsed_job(self, recruiter_id: uuid.UUID, raw_description: str, parsed: dict) -> Job:
        job = Job(
            recruiter_id=recruiter_id,
            title=parsed.get("title") or "Untitled role",
            description=raw_description,
            location=parsed.get("location"),
            employment_type=parsed.get("employment_type"),
            experience_required=parsed.get("experience_required"),
        )
        job.skills = [
            JobSkill(skill_name=s, requirement_type="required") for s in parsed.get("required_skills", [])
        ] + [
            JobSkill(skill_name=s, requirement_type="preferred") for s in parsed.get("preferred_skills", [])
        ]
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def to_matching_input(self, job: Job) -> dict:
        return {
            "job_id": str(job.id),
            "title": job.title,
            "required_skills": [s.skill_name for s in job.skills if s.requirement_type == "required"],
            "preferred_skills": [s.skill_name for s in job.skills if s.requirement_type == "preferred"],
            "experience_required": job.experience_required,
            "education": [],
            "location": job.location,
            "employment_type": job.employment_type,
            "description": job.description,
        }
