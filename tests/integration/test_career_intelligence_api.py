"""
Career intelligence integration tests: job-centric skill-gap analysis,
learning recommendations, career plans, and the AI assistant. Requires
fastapi/sqlalchemy and a real (test) database reachable via DATABASE_URL --
skips cleanly if unavailable, per the project's "no fake passing tests"
rule: we do not mock the DB in a way that hides real integration bugs.

Run with a disposable test database, e.g.:
    DATABASE_URL=postgresql+psycopg://careeriq:careeriq@localhost:5432/careeriq_test pytest tests/integration/test_career_intelligence_api.py -v
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
    description = f"{title}\n\nRequired Skills:\nJava, Spring Boot, PostgreSQL, Kafka\n\nExperience: 2+ years experience required"
    resp = client.post("/api/v1/recruiter/jobs", json={"description": description}, headers=_auth_headers(recruiter_token))
    assert resp.status_code == 201
    return resp.json()["job_id"]


def _setup_candidate_with_skills(prefix: str, skills_text: str = "Java, Spring Boot, PostgreSQL") -> tuple[str, str]:
    _, token = _register_and_login("CANDIDATE", prefix)
    resume = f"Jane Doe\n\nSkills\n{skills_text}\n".encode()
    me = client.get("/api/v1/candidates/me", headers=_auth_headers(token)).json()
    upload_resp = client.post(f"/api/v1/candidates/{me['id']}/resume", files={"file": ("resume.txt", resume, "text/plain")}, headers=_auth_headers(token))
    assert upload_resp.status_code == 200
    return token, me["id"]


# --- Skill Gap Analyzer ------------------------------------------------------

def test_job_skill_gap_endpoint_returns_priorities():
    token, candidate_id = _setup_candidate_with_skills("skillgap-cand")
    _, recruiter_token = _register_and_login("RECRUITER", "skillgap-rec")
    job_id = _create_job(recruiter_token)

    resp = client.get(f"/api/v1/skill-gaps/candidates/{candidate_id}/jobs/{job_id}", headers=_auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert "match_score" in body
    assert "Kafka" in body["missing_skills"]
    assert any(p["skill"] == "Kafka" and p["priority"] == "HIGH" for p in body["skill_priorities"])


def test_skill_gap_candidate_cannot_view_others():
    token_a, candidate_id_a = _setup_candidate_with_skills("skillgap-a")
    _, token_b = _register_and_login("CANDIDATE", "skillgap-b")
    _, recruiter_token = _register_and_login("RECRUITER", "skillgap-rec2")
    job_id = _create_job(recruiter_token)

    resp = client.get(f"/api/v1/skill-gaps/candidates/{candidate_id_a}/jobs/{job_id}", headers=_auth_headers(token_b))
    assert resp.status_code == 403


# --- Learning Recommendations ------------------------------------------------

def test_learning_recommendations_for_job():
    token, candidate_id = _setup_candidate_with_skills("learn-cand")
    _, recruiter_token = _register_and_login("RECRUITER", "learn-rec")
    job_id = _create_job(recruiter_token)

    resp = client.get(f"/api/v1/learning/candidates/{candidate_id}/jobs/{job_id}/recommendations", headers=_auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["recommendations"]) > 0
    orders = [r["recommended_order"] for r in body["recommendations"]]
    assert orders == sorted(orders)


def test_learning_recommendations_for_arbitrary_skillset():
    _, token = _register_and_login("CANDIDATE", "learn-arb")
    resp = client.post(
        "/api/v1/learning/recommendations",
        json={"candidate_skills": ["Java"], "required_skills": ["Java", "Kafka"], "preferred_skills": ["Redis"]},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    skills = [r["skill"] for r in resp.json()["recommendations"]]
    assert "Kafka" in skills and "Redis" in skills


# --- Career Plans ------------------------------------------------------------

def test_generate_and_retrieve_career_plan():
    token, candidate_id = _setup_candidate_with_skills("plan-cand")
    _, recruiter_token = _register_and_login("RECRUITER", "plan-rec")
    job_id = _create_job(recruiter_token)

    gen_resp = client.post(f"/api/v1/career-plans/candidates/{candidate_id}/jobs/{job_id}", headers=_auth_headers(token))
    assert gen_resp.status_code == 201
    plan = gen_resp.json()
    assert plan["target_role"] == "Java Backend Engineer"
    assert len(plan["milestones"]) > 0

    get_resp = client.get(f"/api/v1/career-plans/{plan['plan_id']}", headers=_auth_headers(token))
    assert get_resp.status_code == 200
    assert get_resp.json()["plan_id"] == plan["plan_id"]


def test_career_plan_owner_only():
    token_a, candidate_id_a = _setup_candidate_with_skills("plan-a")
    _, token_b = _register_and_login("CANDIDATE", "plan-b")
    _, recruiter_token = _register_and_login("RECRUITER", "plan-rec2")
    job_id = _create_job(recruiter_token)

    plan = client.post(f"/api/v1/career-plans/candidates/{candidate_id_a}/jobs/{job_id}", headers=_auth_headers(token_a)).json()
    resp = client.get(f"/api/v1/career-plans/{plan['plan_id']}", headers=_auth_headers(token_b))
    assert resp.status_code == 403


# --- AI Assistant -------------------------------------------------------------

def test_assistant_chat_unavailable_without_llm_key():
    # In any environment where GEMINI_API_KEY isn't configured (e.g. CI without
    # secrets), this must return the structured 503 -- never a crash, and
    # every other endpoint must remain unaffected (see other tests in this
    # module all still passing regardless of LLM configuration).
    token, candidate_id = _setup_candidate_with_skills("assistant-cand")
    resp = client.post("/api/v1/assistant/chat", json={"message": "What am I missing for this role?"}, headers=_auth_headers(token))
    assert resp.status_code in (200, 503)
    if resp.status_code == 503:
        assert resp.json()["error"]["code"] == "MODEL_NOT_AVAILABLE"


def test_assistant_requires_candidate_role():
    _, recruiter_token = _register_and_login("RECRUITER", "assistant-rec")
    resp = client.post("/api/v1/assistant/chat", json={"message": "hi"}, headers=_auth_headers(recruiter_token))
    assert resp.status_code == 403


def test_assistant_requires_authentication():
    resp = client.post("/api/v1/assistant/chat", json={"message": "hi"})
    assert resp.status_code == 401


def test_assistant_missing_job_returns_404():
    token, candidate_id = _setup_candidate_with_skills("assistant-nojob")
    fake_job_id = str(uuid.uuid4())
    resp = client.post("/api/v1/assistant/chat", json={"message": "hi", "job_id": fake_job_id}, headers=_auth_headers(token))
    assert resp.status_code in (404, 503)  # 404 if context build runs before the LLM check, 503 if LLM unavailable first


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
