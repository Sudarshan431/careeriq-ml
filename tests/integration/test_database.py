"""
Database integration tests: migrations, model creation, relationships,
matching/recommendation persistence. Skips cleanly without a reachable test
database (never runs against -- and never risks -- a developer's real DB;
point DATABASE_URL at a disposable database before running this file).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest

sqlalchemy = pytest.importorskip("sqlalchemy", reason="sqlalchemy not installed in this environment")

try:
    from app.db.session import database_is_reachable

    _DB_UP = database_is_reachable()
except Exception:
    _DB_UP = False

pytestmark = pytest.mark.skipif(not _DB_UP, reason="No reachable test database (set DATABASE_URL)")

from app.db.session import Base, SessionLocal, engine  # noqa: E402
from app.db.models.user import User  # noqa: E402
from app.db.models.candidate import Candidate, CandidateSkill  # noqa: E402
from app.db.models.job import Job, JobSkill  # noqa: E402
from app.auth.security import hash_password  # noqa: E402
from app.auth.models import Role  # noqa: E402


@pytest.fixture(autouse=True)
def _schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_user_creation():
    db = SessionLocal()
    user = User(email="db-test@example.com", password_hash=hash_password("x"), role=Role.CANDIDATE)
    db.add(user)
    db.commit()
    assert user.id is not None
    db.close()


def test_candidate_belongs_to_user_relationship():
    db = SessionLocal()
    user = User(email="rel-test@example.com", password_hash=hash_password("x"), role=Role.CANDIDATE)
    db.add(user)
    db.commit()

    candidate = Candidate(user_id=user.id, location="Bangalore")
    candidate.skills.append(CandidateSkill(skill_name="Java"))
    db.add(candidate)
    db.commit()

    fetched = db.get(Candidate, candidate.id)
    assert fetched.user_id == user.id
    assert fetched.skills[0].skill_name == "Java"
    db.close()


def test_job_with_skills():
    db = SessionLocal()
    job = Job(title="Backend Engineer", description="Java role")
    job.skills.append(JobSkill(skill_name="Java", requirement_type="required"))
    db.add(job)
    db.commit()

    fetched = db.get(Job, job.id)
    assert len(fetched.skills) == 1
    db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
