"""applications: add match_score, model_version_id; normalize status vocabulary

Revision ID: 0002_applications_match_score
Revises: 0001_initial
Create Date: 2026-08-23

Adds two columns needed for Phase 8 (job application workflow) without
touching 0001_initial.py, since that migration may already be applied
against a real database. Also normalizes any existing lowercase status
values (applied/viewed/rejected/withdrawn) to the new uppercase vocabulary
(APPLIED/REVIEWING/SHORTLISTED/REJECTED/INTERVIEW/HIRED) used going
forward -- see app/db/models/application.py:APPLICATION_STATUSES.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_applications_match_score"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STATUS_MAP = {
    "applied": "APPLIED",
    "viewed": "REVIEWING",
    "rejected": "REJECTED",
    "withdrawn": "REJECTED",
}


def upgrade() -> None:
    op.add_column("applications", sa.Column("match_score", sa.Float, nullable=True))
    op.add_column(
        "applications",
        sa.Column(
            "model_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("model_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    applications = sa.table(
        "applications",
        sa.column("status", sa.String),
    )
    bind = op.get_bind()
    for old_value, new_value in _STATUS_MAP.items():
        bind.execute(applications.update().where(applications.c.status == old_value).values(status=new_value))
    # Anything else already uppercase, or unrecognized, is left as-is rather
    # than guessed -- this is a fresh/dev database in every environment this
    # was authored against, so no rows are expected to exist yet.

    op.alter_column("applications", "status", server_default="APPLIED")


def downgrade() -> None:
    op.alter_column("applications", "status", server_default="applied")

    applications = sa.table(
        "applications",
        sa.column("status", sa.String),
    )
    bind = op.get_bind()
    reverse_map = {"APPLIED": "applied", "REVIEWING": "viewed", "REJECTED": "rejected"}
    for new_value, old_value in reverse_map.items():
        bind.execute(applications.update().where(applications.c.status == new_value).values(status=old_value))
    # SHORTLISTED, INTERVIEW, HIRED have no pre-Phase-8 equivalent; leave as-is.

    op.drop_column("applications", "model_version_id")
    op.drop_column("applications", "match_score")
