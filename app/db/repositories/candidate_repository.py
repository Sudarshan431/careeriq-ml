"""Data access for Candidate + child entities (skills/education/experience/projects/certs)."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.candidate import (
    Candidate,
    CandidateCertification,
    CandidateEducation,
    CandidateExperience,
    CandidateProject,
    CandidateSkill,
)


class CandidateRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: uuid.UUID) -> Candidate | None:
        stmt = select(Candidate).where(Candidate.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id(self, candidate_id: uuid.UUID) -> Candidate | None:
        return self.db.get(Candidate, candidate_id)

    def list_all(self, limit: int = 100) -> list[Candidate]:
        stmt = select(Candidate).order_by(Candidate.created_at.desc()).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def create_for_user(self, user_id: uuid.UUID) -> Candidate:
        candidate = Candidate(user_id=user_id)
        self.db.add(candidate)
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def replace_profile_from_parsed_resume(self, candidate: Candidate, profile: dict) -> Candidate:
        """
        Overwrites the candidate's skill/education/experience/project/cert
        rows with what was just extracted from a resume upload. Wrapped in a
        single transaction so a partial resume (e.g. no certifications
        section) never leaves the candidate's other data half-updated.
        """
        candidate.summary = profile.get("summary") or candidate.summary
        candidate.total_years_experience = profile.get("total_years_experience") or candidate.total_years_experience

        candidate.skills = [CandidateSkill(skill_name=s, source="resume") for s in profile.get("skills", [])]
        candidate.education = [
            CandidateEducation(
                degree=e.get("degree"), field=e.get("field"),
                institution=e.get("institution"), graduation_year=e.get("graduation_year"),
            )
            for e in profile.get("education", [])
        ]
        candidate.experience = [
            CandidateExperience(
                role=e.get("role"), company=e.get("company"),
                duration_text=e.get("duration_text"), technologies=e.get("technologies", []),
            )
            for e in profile.get("experience", [])
        ]
        candidate.projects = [
            CandidateProject(title=p["title"], technologies=p.get("technologies", []), description=p.get("description"))
            for p in profile.get("projects", [])
        ]
        candidate.certifications = [
            CandidateCertification(name=c["name"], year=c.get("year")) for c in profile.get("certifications", [])
        ]

        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def to_matching_input(self, candidate: Candidate) -> dict:
        """Shapes a Candidate ORM object into the plain dict the existing (unchanged) matching/ML layer expects."""
        return {
            "candidate_id": str(candidate.id),
            "skills": [s.skill_name for s in candidate.skills],
            "experience_years": candidate.total_years_experience,
            "education": [
                {"degree": e.degree, "field": e.field, "institution": e.institution, "graduation_year": e.graduation_year}
                for e in candidate.education
            ],
            "location": candidate.location,
            "summary": candidate.summary,
            "preferences": candidate.preferences,
        }
