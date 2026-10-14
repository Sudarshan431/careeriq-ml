"""
Job application workflow integration tests. Requires fastapi/sqlalchemy and
a real (test) database reachable via DATABASE_URL -- skips cleanly if
unavailable, per the project's "no fake passing tests" rule: we do not mock
the DB in a way that hides real integration bugs.

Run with a disposable test database, e.g.:
    DATABASE_URL=postgresql+psycopg://careeriq:careeriq@localhost:5432/careeriq_test pytest tests/integration/test_applications_api.py -v
"""
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest

fastapi = pytest.importorskip("fastapi", reason="fastapi not installed in this environment")
sqlalchemy = pytest.importorskip("sqlalchemy", reason="sqlalchemy not installed in this environment")

from fastapi.testclient import TestClient  # noqa: E402

try:
    from app.db.session import database_is_reachable

    _DB_UP = database_is_reachable()
except Exception:
    _DB_UP = False

pytestmark = pytest.mark.skipif(not _DB_UP, reason="No reachable test database (set DATABASE_URL)")

from app.main import app  # noqa: E402
from app.db.session import Base, engine, SessionLocal  # noqa: E402
from app.core.exceptions import DuplicateApplicationError  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def _setup_schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def _register_and_login(role: str, prefix: str) -> tuple[str, str]:
    email = _unique_email(prefix)
    client.post("/api/v1/auth/register", json={"email": email, "password": "StrongPass1", "role": role})
    token = client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPass1"}).json()["access_token"]
    return email, token


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_job(recruiter_token: str, title: str = "Java Backend Engineer") -> str:
    description = f"{title}\n\nRequired Skills:\nJava, Spring Boot, PostgreSQL\n\nExperience: 2+ years experience required"
    resp = client.post("/api/v1/recruiter/jobs", json={"description": description}, headers=_auth_headers(recruiter_token))
    assert resp.status_code == 201
    return resp.json()["job_id"]


# --- 1. Candidate can apply -------------------------------------------------

def test_candidate_can_apply():
    _, candidate_token = _register_and_login("CANDIDATE", "apply-cand")
    _, recruiter_token = _register_and_login("RECRUITER", "apply-rec")
    job_id = _create_job(recruiter_token)

    resp = client.post(f"/api/v1/jobs/{job_id}/apply", headers=_auth_headers(candidate_token))
    assert resp.status_code == 201
    body = resp.json()
    assert body["job_id"] == job_id
    assert body["status"] == "APPLIED"


# --- 2. Candidate cannot apply twice (via API) ------------------------------

def test_candidate_cannot_apply_twice():
    _, candidate_token = _register_and_login("CANDIDATE", "twice-cand")
    _, recruiter_token = _register_and_login("RECRUITER", "twice-rec")
    job_id = _create_job(recruiter_token)

    first = client.post(f"/api/v1/jobs/{job_id}/apply", headers=_auth_headers(candidate_token))
    assert first.status_code == 201

    second = client.post(f"/api/v1/jobs/{job_id}/apply", headers=_auth_headers(candidate_token))
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "DUPLICATE_APPLICATION"


# --- 3. Candidate can view own applications ---------------------------------

def test_candidate_can_view_own_applications():
    _, candidate_token = _register_and_login("CANDIDATE", "viewown-cand")
    _, recruiter_token = _register_and_login("RECRUITER", "viewown-rec")
    job_id = _create_job(recruiter_token)
    client.post(f"/api/v1/jobs/{job_id}/apply", headers=_auth_headers(candidate_token))

    resp = client.get("/api/v1/applications/me", headers=_auth_headers(candidate_token))
    assert resp.status_code == 200
    apps = resp.json()["applications"]
    assert len(apps) == 1
    assert apps[0]["job_id"] == job_id
    assert apps[0]["job_title"]  # denormalized title populated


# --- 4. Candidate cannot view another candidate's applications -------------

def test_candidate_cannot_view_another_candidates_applications():
    # /applications/me always resolves candidate_id from the caller's own JWT,
    # so there is no endpoint shape that would let candidate A request
    # candidate B's applications in the first place -- verify A only ever
    # sees their own, never B's, even after both have applied.
    _, token_a = _register_and_login("CANDIDATE", "cross-a")
    _, token_b = _register_and_login("CANDIDATE", "cross-b")
    _, recruiter_token = _register_and_login("RECRUITER", "cross-rec")
    job_id = _create_job(recruiter_token)

    client.post(f"/api/v1/jobs/{job_id}/apply", headers=_auth_headers(token_a))
    client.post(f"/api/v1/jobs/{job_id}/apply", headers=_auth_headers(token_b))

    resp_a = client.get("/api/v1/applications/me", headers=_auth_headers(token_a))
    apps_a = resp_a.json()["applications"]
    assert len(apps_a) == 1

    resp_b = client.get("/api/v1/applications/me", headers=_auth_headers(token_b))
    apps_b = resp_b.json()["applications"]
    assert len(apps_b) == 1
    assert apps_a[0]["id"] != apps_b[0]["id"]


# --- 5. Recruiter can view applicants for own job ---------------------------

def test_recruiter_can_view_applicants_for_own_job():
    _, candidate_token = _register_and_login("CANDIDATE", "ownjob-cand")
    _, recruiter_token = _register_and_login("RECRUITER", "ownjob-rec")
    job_id = _create_job(recruiter_token)
    client.post(f"/api/v1/jobs/{job_id}/apply", headers=_auth_headers(candidate_token))

    resp = client.get(f"/api/v1/jobs/{job_id}/applications", headers=_auth_headers(recruiter_token))
    assert resp.status_code == 200
    apps = resp.json()["applications"]
    assert len(apps) == 1
    assert apps[0]["candidate_email"]  # denormalized email populated


# --- 6. Recruiter cannot view applicants for another recruiter's job -------

def test_recruiter_cannot_view_applicants_for_another_recruiters_job():
    _, candidate_token = _register_and_login("CANDIDATE", "otherjob-cand")
    _, recruiter_a_token = _register_and_login("RECRUITER", "otherjob-rec-a")
    _, recruiter_b_token = _register_and_login("RECRUITER", "otherjob-rec-b")
    job_id = _create_job(recruiter_a_token)
    client.post(f"/api/v1/jobs/{job_id}/apply", headers=_auth_headers(candidate_token))

    resp = client.get(f"/api/v1/jobs/{job_id}/applications", headers=_auth_headers(recruiter_b_token))
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


# --- 7. Recruiter can update status for own job -----------------------------

def test_recruiter_can_update_status_for_own_job():
    _, candidate_token = _register_and_login("CANDIDATE", "status-cand")
    _, recruiter_token = _register_and_login("RECRUITER", "status-rec")
    job_id = _create_job(recruiter_token)
    apply_resp = client.post(f"/api/v1/jobs/{job_id}/apply", headers=_auth_headers(candidate_token))
    application_id = apply_resp.json()["id"]

    resp = client.patch(
        f"/api/v1/applications/{application_id}/status",
        json={"status": "SHORTLISTED"},
        headers=_auth_headers(recruiter_token),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "SHORTLISTED"


# --- 8. Candidate cannot update application status --------------------------

def test_candidate_cannot_update_application_status():
    _, candidate_token = _register_and_login("CANDIDATE", "noupdate-cand")
    _, recruiter_token = _register_and_login("RECRUITER", "noupdate-rec")
    job_id = _create_job(recruiter_token)
    apply_resp = client.post(f"/api/v1/jobs/{job_id}/apply", headers=_auth_headers(candidate_token))
    application_id = apply_resp.json()["id"]

    resp = client.patch(
        f"/api/v1/applications/{application_id}/status",
        json={"status": "HIRED"},
        headers=_auth_headers(candidate_token),
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


# --- 9. Database unique constraint prevents duplicate application ----------

def test_database_unique_constraint_prevents_duplicate():
    """
    Exercises ApplicationRepository.create() directly, twice, bypassing the
    service-layer pre-check -- proving the DB-level UniqueConstraint is what
    actually stops the second insert (not just app-level logic), which is
    what protects against a race between two concurrent requests.
    """
    from app.db.repositories.application_repository import ApplicationRepository
    from app.db.repositories.candidate_repository import CandidateRepository
    from app.db.repositories.job_repository import JobRepository
    from app.db.repositories.user_repository import UserRepository

    _, recruiter_token = _register_and_login("RECRUITER", "uniq-rec")
    job_id = _create_job(recruiter_token)
    candidate_email, _ = _register_and_login("CANDIDATE", "uniq-cand")

    db = SessionLocal()
    user = UserRepository(db).get_by_email(candidate_email)
    candidate = CandidateRepository(db).get_by_user_id(user.id)
    job = JobRepository(db).get_by_id(uuid.UUID(job_id))

    repo = ApplicationRepository(db)
    repo.create(candidate_id=candidate.id, job_id=job.id, match_score=50.0)

    with pytest.raises(DuplicateApplicationError):
        repo.create(candidate_id=candidate.id, job_id=job.id, match_score=75.0)
    db.close()


# --- 10. Application stores match score -------------------------------------

def test_application_stores_match_score():
    _, candidate_token = _register_and_login("CANDIDATE", "score-cand")
    _, recruiter_token = _register_and_login("RECRUITER", "score-rec")
    job_id = _create_job(recruiter_token)

    resp = client.post(f"/api/v1/jobs/{job_id}/apply", headers=_auth_headers(candidate_token))
    assert resp.status_code == 201
    body = resp.json()
    assert body["match_score"] is not None
    assert isinstance(body["match_score"], (int, float))
    assert 0 <= body["match_score"] <= 100

    # Confirm it is not recomputed on later reads: the recruiter's view of
    # the same application should show an identical score.
    my_apps = client.get("/api/v1/applications/me", headers=_auth_headers(candidate_token)).json()["applications"]
    applicants = client.get(f"/api/v1/jobs/{job_id}/applications", headers=_auth_headers(recruiter_token)).json()["applications"]
    assert my_apps[0]["match_score"] == applicants[0]["match_score"] == body["match_score"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
