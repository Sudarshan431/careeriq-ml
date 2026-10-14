"""Resume metadata (not raw file contents -- see file_storage.py for the storage abstraction)."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)  # sanitized, never a raw path
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # pdf | docx | txt
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # bytes
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)  # opaque key -- see file_storage.py
    processing_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|processing|processed|failed
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    candidate: Mapped["Candidate"] = relationship(back_populates="resumes")
