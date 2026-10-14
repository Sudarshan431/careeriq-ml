"""
Integration tests for the FastAPI layer, using FastAPI's TestClient (httpx
under the hood). These require `fastapi`, `pydantic`, and `httpx` to be
installed -- if they aren't (e.g. in a sandbox with no package registry
access), the whole module is skipped rather than failing, so `pytest` still
exits cleanly and reports what *was* runnable.

Run with:
    pytest tests/integration/test_api.py -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest

fastapi = pytest.importorskip("fastapi", reason="fastapi not installed in this environment")
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_job_analyze():
    payload = {
        "description": "Java Backend Engineer\n\nRequired Skills:\nJava, Spring Boot, PostgreSQL\n\nExperience: 2+ years experience required"
    }
    resp = client.post("/api/v1/job/analyze", json=payload)
    assert resp.status_code == 200
    job = resp.json()["job"]
    assert "Java" in job["required_skills"]


def test_job_analyze_empty_description_returns_422():
    resp = client.post("/api/v1/job/analyze", json={"description": ""})
    assert resp.status_code == 422


def test_matching_calculate():
    payload = {
        "candidate": {"skills": ["Java", "Spring Boot", "PostgreSQL"], "experience_years": 3},
        "job": {"required_skills": ["Java", "Spring Boot", "Kafka"], "preferred_skills": ["Docker"], "experience_required": 2},
        "use_semantic": False,
    }
    resp = client.post("/api/v1/matching/calculate", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert 0 <= body["match_score"] <= 100
    assert "explanation" in body


def test_skill_gap_endpoint():
    payload = {
        "candidate_skills": ["Java", "Spring Boot"],
        "required_skills": ["Java", "Spring Boot", "Kafka"],
    }
    resp = client.post("/api/v1/skills/gap", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert "Kafka" in body["critical_missing_skills"] or any(
        p["skill"] == "Kafka" for p in body["partially_matched_skills"]
    )


def test_recommendations_endpoint():
    payload = {
        "candidate": {"skills": ["Java", "Spring Boot"]},
        "jobs": [
            {"job_id": "j1", "title": "Java Dev", "required_skills": ["Java", "Spring Boot"]},
            {"job_id": "j2", "title": "Frontend Dev", "required_skills": ["React", "CSS"]},
        ],
        "top_k": 2,
        "strategy": "content",
    }
    resp = client.post("/api/v1/recommendations/jobs", json=payload)
    assert resp.status_code == 200
    recs = resp.json()["recommendations"]
    assert recs[0]["job_id"] == "j1"  # should rank the closer skill match first


def test_resume_analyze_rejects_bad_extension():
    resp = client.post(
        "/api/v1/resume/analyze",
        files={"file": ("resume.exe", b"not a real resume", "application/octet-stream")},
    )
    assert resp.status_code in (415, 422)


def test_models_endpoint():
    resp = client.get("/api/v1/models")
    assert resp.status_code == 200
    assert "models" in resp.json()
