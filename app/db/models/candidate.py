"""Candidate profile + child entities (skills, education, experience, projects, certifications)."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_years_experience: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Preferences are genuinely free-form/sparse (employment type, remote, salary
    # band, etc.) so a JSON column is appropriate here rather than a rigid schema.
    preferences: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="candidate")
    skills: Mapped[list["CandidateSkill"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    education: Mapped[list["CandidateEducation"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    experience: Mapped[list["CandidateExperience"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    projects: Mapped[list["CandidateProject"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    certifications: Mapped[list["CandidateCertification"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")
    resumes: Mapped[list["Resume"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)  # canonical taxonomy name
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    source: Mapped[str] = mapped_column(String(30), default="resume")  # resume | manual

    candidate: Mapped["Candidate"] = relationship(back_populates="skills")


class CandidateEducation(Base):
    __tablename__ = "candidate_education"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    degree: Mapped[str | None] = mapped_column(String(120), nullable=True)
    field: Mapped[str | None] = mapped_column(String(120), nullable=True)
    institution: Mapped[str | None] = mapped_column(String(255), nullable=True)
    graduation_year: Mapped[str | None] = mapped_column(String(10), nullable=True)

    candidate: Mapped["Candidate"] = relationship(back_populates="education")


class CandidateExperience(Base):
    __tablename__ = "candidate_experience"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str | None] = mapped_column(String(150), nullable=True)
    company: Mapped[str | None] = mapped_column(String(150), nullable=True)
    duration_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    technologies: Mapped[list | None] = mapped_column(JSON, nullable=True)  # small, genuinely list-shaped -> JSON is fine

    candidate: Mapped["Candidate"] = relationship(back_populates="experience")


class CandidateProject(Base):
    __tablename__ = "candidate_projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    technologies: Mapped[list | None] = mapped_column(JSON, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    candidate: Mapped["Candidate"] = relationship(back_populates="projects")


class CandidateCertification(Base):
    __tablename__ = "candidate_certifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    year: Mapped[str | None] = mapped_column(String(10), nullable=True)

    candidate: Mapped["Candidate"] = relationship(back_populates="certifications")
