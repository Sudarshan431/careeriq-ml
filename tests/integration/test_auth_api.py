"""
Auth + RBAC integration tests. Requires fastapi/httpx/sqlalchemy and a real
(test) database reachable via DATABASE_URL -- skips cleanly if unavailable,
per the project's "no fake passing tests" rule (Rule 3): we do not mock the
DB in a way that hides real integration bugs, so this suite is honestly
opt-in rather than mocked-to-always-pass.

Run with a disposable test database, e.g.:
    DATABASE_URL=postgresql+psycopg://careeriq:careeriq@localhost:5432/careeriq_test pytest tests/integration/test_auth_api.py -v
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest

fastapi = pytest.importorskip("fastapi", reason="fastapi not installed in this environment")
sqlalchemy = pytest.importorskip("sqlalchemy", reason="sqlalchemy not installed in this environment")

from fastapi.testclient import TestClient  # noqa: E402

# Requires a reachable test database; skip rather than silently fail against
# a missing/unreachable DB (which would give false confidence).
try:
    from app.db.session import database_is_reachable

    _DB_UP = database_is_reachable()
except Exception:
    _DB_UP = False

pytestmark = pytest.mark.skipif(not _DB_UP, reason="No reachable test database (set DATABASE_URL)")

from app.main import app  # noqa: E402
from app.db.session import Base, engine  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def _setup_schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _unique_email(prefix: str) -> str:
    import uuid

    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def test_register_success():
    email = _unique_email("cand")
    resp = client.post("/api/v1/auth/register", json={"email": email, "password": "StrongPass1", "role": "CANDIDATE"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == email
    assert "password" not in body
    assert "password_hash" not in body


def test_register_duplicate_rejected():
    email = _unique_email("dupe")
    client.post("/api/v1/auth/register", json={"email": email, "password": "StrongPass1", "role": "CANDIDATE"})
    resp = client.post("/api/v1/auth/register", json={"email": email, "password": "StrongPass1", "role": "CANDIDATE"})
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "DUPLICATE_USER"


def test_register_invalid_email_rejected():
    resp = client.post("/api/v1/auth/register", json={"email": "not-an-email", "password": "StrongPass1"})
    assert resp.status_code == 422


def test_register_weak_password_rejected():
    email = _unique_email("weak")
    resp = client.post("/api/v1/auth/register", json={"email": email, "password": "short"})
    assert resp.status_code == 422


def test_login_success_and_me():
    email = _unique_email("login")
    client.post("/api/v1/auth/register", json={"email": email, "password": "StrongPass1", "role": "CANDIDATE"})
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPass1"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == email


def test_login_wrong_password_rejected():
    email = _unique_email("wrongpw")
    client.post("/api/v1/auth/register", json={"email": email, "password": "StrongPass1", "role": "CANDIDATE"})
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPassword1"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_unknown_user_rejected():
    resp = client.post("/api/v1/auth/login", json={"email": _unique_email("ghost"), "password": "StrongPass1"})
    assert resp.status_code == 401


def test_protected_endpoint_without_token_rejected():
    resp = client.post("/api/v1/job/analyze", json={"description": "Java role"})
    assert resp.status_code == 401


def test_protected_endpoint_with_invalid_token_rejected():
    resp = client.post(
        "/api/v1/job/analyze", json={"description": "Java role"}, headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert resp.status_code == 401


def test_candidate_cannot_access_recruiter_endpoint():
    email = _unique_email("cand2")
    client.post("/api/v1/auth/register", json={"email": email, "password": "StrongPass1", "role": "CANDIDATE"})
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPass1"}).json()["access_token"]

    resp = client.post(
        "/api/v1/matching/rank-candidates",
        json={"job": {"required_skills": ["Java"]}, "candidates": []},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


def test_recruiter_can_access_recruiter_endpoint():
    email = _unique_email("recruiter")
    client.post("/api/v1/auth/register", json={"email": email, "password": "StrongPass1", "role": "RECRUITER"})
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPass1"}).json()["access_token"]

    resp = client.post(
        "/api/v1/matching/rank-candidates",
        json={"job": {"required_skills": ["Java"]}, "candidates": []},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


def test_candidate_a_cannot_access_candidate_b_profile():
    email_a = _unique_email("a")
    email_b = _unique_email("b")
    client.post("/api/v1/auth/register", json={"email": email_a, "password": "StrongPass1", "role": "CANDIDATE"})
    client.post("/api/v1/auth/register", json={"email": email_b, "password": "StrongPass1", "role": "CANDIDATE"})
    token_a = client.post("/api/v1/auth/login", json={"email": email_a, "password": "StrongPass1"}).json()["access_token"]

    from app.db.session import SessionLocal
    from app.db.repositories.user_repository import UserRepository
    from app.db.repositories.candidate_repository import CandidateRepository

    db = SessionLocal()
    user_b = UserRepository(db).get_by_email(email_b)
    candidate_b = CandidateRepository(db).get_by_user_id(user_b.id)
    db.close()

    resp = client.get(f"/api/v1/candidates/{candidate_b.id}", headers={"Authorization": f"Bearer {token_a}"})
    assert resp.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
