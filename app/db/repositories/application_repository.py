"""Data access for Application. Routers/services never build SQLAlchemy queries directly."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateApplicationError
from app.db.models.application import Application


class ApplicationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, application_id: uuid.UUID) -> Application | None:
        return self.db.get(Application, application_id)

    def get_by_candidate_and_job(self, candidate_id: uuid.UUID, job_id: uuid.UUID) -> Application | None:
        stmt = select(Application).where(Application.candidate_id == candidate_id, Application.job_id == job_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_by_candidate(self, candidate_id: uuid.UUID) -> list[Application]:
        stmt = select(Application).where(Application.candidate_id == candidate_id).order_by(Application.applied_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def list_by_job(self, job_id: uuid.UUID) -> list[Application]:
        stmt = select(Application).where(Application.job_id == job_id).order_by(Application.applied_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def create(
        self,
        candidate_id: uuid.UUID,
        job_id: uuid.UUID,
        match_score: float | None = None,
        model_version_id: uuid.UUID | None = None,
    ) -> Application:
        """
        Application-level pre-check (get_by_candidate_and_job) gives a clean
        error message in the common case; the try/except around the actual
        insert is the real guarantee -- it relies on the DB-level unique
        constraint (candidate_id, job_id) so a race between two concurrent
        requests for the same candidate+job can never create two rows, even
        if both requests passed the pre-check.
        """
        application = Application(
            candidate_id=candidate_id, job_id=job_id, status="APPLIED",
            match_score=match_score, model_version_id=model_version_id,
        )
        self.db.add(application)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise DuplicateApplicationError()
        self.db.refresh(application)
        return application

    def update_status(self, application: Application, new_status: str) -> Application:
        application.status = new_status
        self.db.commit()
        self.db.refresh(application)
        return application
