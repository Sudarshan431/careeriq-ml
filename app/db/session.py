"""
SQLAlchemy 2.x engine/session setup. DATABASE_URL comes entirely from
settings/environment -- never hardcoded here (spec requirement).

NOTE: `sqlalchemy` and `psycopg` are not installed in the sandbox this was
authored in (no network access to pip), so this module is written to spec
and syntax-checked but has not been executed against a real PostgreSQL
instance. See README.md "What's verified vs. written" table.
"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a request-scoped session, always closed afterward."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def database_is_reachable() -> bool:
    """Used by /health -- never raises, never leaks the connection string or credentials."""
    try:
        from sqlalchemy import text

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
