# CareerIQ ML Engine — Phases 1–4

Python backend for the CareerIQ AI career intelligence platform: resume/job
NLP, candidate-job matching, skill-gap analysis, recommendations, PostgreSQL
persistence, and JWT authentication with role-based access control
(CANDIDATE / RECRUITER / ADMIN).

> **Environment note (read this first)**: this repository was extended in a
> sandbox with **no network access to PyPI** (confirmed blocked at the
> egress proxy) and **no PostgreSQL server**. Only `numpy`, `pandas`,
> `scikit-learn`, `joblib`, `pdfplumber`, `python-docx`, and `PyJWT` were
> installed — not `fastapi`, `sqlalchemy`, `alembic`, `passlib`, or
> `pytest`. Everything below is either (a) real code that was actually run
> and verified in this sandbox, or (b) written correctly to spec and
> syntax-checked (`python -m py_compile`) but **not yet executed** — see the
> table under "What's verified vs. written" for exactly which is which
> before you rely on any specific claim.

---

## Architecture

```text
React/client
     |
FastAPI (app/main.py)
     |
Auth / RBAC (app/auth/)  -->  JWT (PyJWT) + password hashing (passlib/argon2, PBKDF2 fallback)
     |
API routers (app/api/)  -->  never contain business logic directly
     |
Services (app/services/)  -->  orchestration; careeriq_workflow_service.py chains the full candidate journey
     |
NLP / ML (app/nlp/, app/ml/)  -->  unchanged from Phase 1, reused everywhere
     |
Repositories (app/db/repositories/)  -->  the only place SQLAlchemy queries live
     |
SQLAlchemy models (app/db/models/) + Alembic migrations (alembic/)
     |
PostgreSQL
```

---

## Local setup

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m spacy download en_core_web_sm
cp .env.example .env          # edit JWT_SECRET_KEY and DATABASE_URL for your machine
docker compose up -d postgres # or point DATABASE_URL at your own Postgres instance
alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m spacy download en_core_web_sm
Copy-Item .env.example .env    # edit JWT_SECRET_KEY and DATABASE_URL
docker compose up -d postgres
alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

Then open Swagger at `http://127.0.0.1:8000/docs`.

### Running the ML training/demo scripts (no DB required)

```bash
python scripts/generate_synthetic_data.py
python scripts/prepare_data.py
python scripts/train_matching.py
python scripts/evaluate_models.py
python scripts/train_recommendation.py
python scripts/demo.py
```

### Tests

```bash
python -m unittest discover -s tests/unit -v   # 42 tests, no external services needed
pytest -v                                       # full suite; DB-dependent tests skip cleanly without DATABASE_URL reachable
```

To actually run the DB-backed tests (`tests/integration/test_auth_api.py`,
`tests/integration/test_database.py`), point `DATABASE_URL` at a
**disposable** database before running `pytest` — they create and drop
tables in whatever database `DATABASE_URL` points to, so never point it at
a database with real data:

```bash
export DATABASE_URL=postgresql+psycopg://careeriq:careeriq@localhost:5432/careeriq_test
pytest tests/integration/test_auth_api.py tests/integration/test_database.py -v
```

---

## Authentication

### Register

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "candidate@example.com", "password": "StrongPass1", "role": "CANDIDATE"}'
```

Passwords must be 8+ characters with both letters and numbers. `ADMIN`
cannot be created through this endpoint (spec requirement) — provision
admin accounts directly in the database or via a separate internal script.

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "candidate@example.com", "password": "StrongPass1"}'
# -> {"access_token": "...", "token_type": "bearer", "expires_in_minutes": 30}
```

### Use the token

```bash
curl http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer <token>"
```

There is no `/logout` or `/refresh` endpoint. Per the spec ("do not create
fake logout semantics for stateless JWTs"), a stateless JWT can't be
revoked without a server-side blacklist/session store, which wasn't part of
this scope — logout is a client-side "discard the token" operation, and
tokens simply expire after `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`.

---

## RBAC — endpoint to required role

| Endpoint | Required role |
|---|---|
| `GET /health` | public |
| `GET /` | public |
| `POST /api/v1/auth/register` | public |
| `POST /api/v1/auth/login` | public |
| `GET /api/v1/auth/me` | any authenticated user |
| `GET /api/v1/models` | public (reads on-disk model metadata only, no secrets) |
| `POST /api/v1/resume/analyze` | CANDIDATE or ADMIN |
| `POST /api/v1/job/analyze` | any authenticated user |
| `GET /api/v1/jobs` | any authenticated user |
| `GET /api/v1/jobs/{job_id}` | any authenticated user |
| `POST /api/v1/jobs/{job_id}/apply` | CANDIDATE or ADMIN (applies as the caller's own candidate_id only) |
| `GET /api/v1/jobs/{job_id}/applications` | the recruiter who owns the job, or ADMIN (ownership check) |
| `POST /api/v1/skills/gap` | any authenticated user |
| `POST /api/v1/matching/calculate` | any authenticated user |
| `POST /api/v1/matching/rank-candidates` | RECRUITER or ADMIN |
| `POST /api/v1/recommendations/jobs` | CANDIDATE or ADMIN |
| `GET /api/v1/candidates/me` | CANDIDATE or ADMIN (resolves the caller's own candidate_id) |
| `GET /api/v1/candidates/{id}` | the candidate themself, or ADMIN (ownership check) |
| `POST /api/v1/candidates/{id}/resume` | the candidate themself, or ADMIN |
| `POST /api/v1/candidates/{id}/workflow` | the candidate themself, or ADMIN |
| `GET /api/v1/applications/me` | CANDIDATE or ADMIN (resolves the caller's own candidate_id) |
| `PATCH /api/v1/applications/{id}/status` | the recruiter who owns the job the application is for, or ADMIN (ownership check; CANDIDATE can never reach this regardless of ownership) |
| `GET /api/v1/skill-gaps/candidates/{id}/jobs/{job_id}` | the candidate themself, or ADMIN (ownership check) |
| `GET /api/v1/learning/candidates/{id}/jobs/{job_id}/recommendations` | the candidate themself, or ADMIN (ownership check) |
| `POST /api/v1/learning/recommendations` | any authenticated user (career-level, no persisted job/candidate involved) |
| `POST /api/v1/career-plans/candidates/{id}/jobs/{job_id}` | the candidate themself, or ADMIN (ownership check) |
| `GET /api/v1/career-plans/candidates/{id}` | the candidate themself, or ADMIN (ownership check) |
| `GET /api/v1/career-plans/{plan_id}` | the plan's own candidate, or ADMIN (ownership resolved from the plan itself) |
| `POST /api/v1/assistant/chat` | CANDIDATE or ADMIN (candidate_id always resolved from the caller's own JWT -- never client-supplied) |
| `POST /api/v1/recruiter/jobs` | RECRUITER or ADMIN |
| `GET /api/v1/recruiter/candidates` | RECRUITER or ADMIN |
| `POST /api/v1/recruiter/jobs/{id}/rank-candidates` | RECRUITER or ADMIN |

ADMIN is never granted automatically to RECRUITER or vice versa. Ownership
checks (candidate-scoped routes) are enforced server-side regardless of
role — a CANDIDATE token for user A returns `403 FORBIDDEN` when used
against candidate B's resources, even though both hold valid CANDIDATE-role
tokens.

Errors use a consistent envelope:

```json
{"error": {"code": "FORBIDDEN", "message": "...", "request_id": "..."}}
```

---

## Job application workflow (Phase 8)

Candidate: `GET /jobs` → `GET /jobs/{id}` → `POST /jobs/{id}/apply` → `GET /applications/me`.
Recruiter: `POST /recruiter/jobs` → `GET /jobs/{id}/applications` → `PATCH /applications/{id}/status`.

- Statuses: `APPLIED`, `REVIEWING`, `SHORTLISTED`, `REJECTED`, `INTERVIEW`, `HIRED` (validated by `ApplicationStatusUpdateRequest`; stored as a plain `String` column, not a Postgres `ENUM` type, deliberately — see the `user_role` `DuplicateObject` incident earlier in this project's history for why extending an enum-typed column is worth avoiding).
- The match score is computed **once**, via the existing unmodified `matching_service.calculate_match`, at the moment a candidate applies, and persisted on the `applications` row (`match_score`) — never recomputed on later reads. A recruiter viewing an applicant sees the score as of application time, not today's score.
- `(candidate_id, job_id)` has a database-level `UniqueConstraint`, applied in `0001_initial.py` and unchanged since. The service layer does a pre-check for a clean error message, but the actual duplicate-prevention guarantee is the DB constraint (protects against a race between two concurrent requests) — see `test_database_unique_constraint_prevents_duplicate` in `tests/integration/test_applications_api.py`.
- A candidate can only ever apply as themselves and view only their own applications — every candidate-facing application endpoint resolves `candidate_id` from the caller's JWT server-side; none accept a client-supplied `candidate_id`.
- A recruiter can only view/update applications for jobs where `job.recruiter_id == current_user.id` (or ADMIN); this is enforced in `application_service._require_job_owner`, not just at the route layer.
- New migration `0002_applications_match_score.py` adds `match_score`/`model_version_id` to `applications` and normalizes any pre-Phase-8 lowercase status values — additive, doesn't touch `0001_initial.py`.

---

## Career Intelligence pipeline (Skill Gap → Learning → Career Plan → AI Assistant)

Every layer below is built strictly on top of the ones before it — none duplicate the underlying skill-matching/relationship logic, which remains exactly `app/ml/matching/skill_gap.py` (unchanged since Phase 1):

```text
analyze_skill_gap()          (unchanged)
        |
prioritize_skill_gaps()      HIGH/MEDIUM/LOW, derived from the existing matched/partial/missing categories
        |
build_learning_recommendations()   + taxonomy parent/child dependency ordering (skill_relationships.json, unchanged)
        |
career_plan_service           + milestone grouping + practice-project suggestions (from the candidate's real skills only)
        |
assistant context_builder     same services, packaged as structured JSON -- never raw resume/job text
        |
assistant prompt_builder + llm_provider    grounded, injection-resistant prompt -> LLM -> natural-language answer
```

**Skill Gap Analyzer**: `GET /api/v1/skill-gaps/candidates/{id}/jobs/{job_id}` — matched/partial/missing skills (alias- and taxonomy-relationship-aware, e.g. "Postgres" ≈ "PostgreSQL", having "Spring" partially covers "Spring Boot"), each missing skill classified HIGH/MEDIUM/LOW, plus an overall match score. The existing raw `POST /api/v1/skills/gap` (plain skill lists, no DB lookup) is unchanged and still works.

**Recommendation Explanation**: `POST /api/v1/recommendations/jobs` gained an optional `explain: bool` field (default `false`, fully backward compatible). When `true`, each of the top-k returned recommendations is enriched with `explanation`, `skill_gap`, and `score_breakdown` by calling the existing `matching_service.calculate_match` — computed only for the results actually returned, not the whole job pool.

**Learning Recommendations**: `GET /api/v1/learning/candidates/{id}/jobs/{job_id}/recommendations` (job-specific) and `POST /api/v1/learning/recommendations` (arbitrary target skill set, for a broader career/role target). Dependency ordering comes from the same `skill_relationships.json` parent/child data already used for partial-match detection — e.g. "Spring" is scheduled before "Spring Boot" if both are gaps. No external learning-resource URLs are invented; each item carries `suggested_resource_types` (generic categories) as the documented extension point for real resource content later.

**Career/Learning Plan**: `POST /api/v1/career-plans/candidates/{id}/jobs/{job_id}` generates and persists a plan (new `learning_plans`/`learning_plan_items` tables) grouping the ordered learning items into HIGH/MEDIUM/LOW milestones, with a job-readiness assessment derived from the existing `baseline_match` score and a practice-project suggestion per skill built only from the candidate's actual existing skills (never a fabricated technology).

**AI Career Assistant**: `POST /api/v1/assistant/chat`. Architecture is strictly one-directional — `app/ai/context_builder.py` pulls real, already-authorized data from the existing services (never the LLM), `app/ai/prompt_builder.py` embeds it as clearly-delimited JSON with explicit "treat as data, not instructions" rules (the resume/job-description-derived content is the untrusted-input surface a prompt injection would target), and `app/ai/llm_provider.py` (`app/ai/` package) calls **Google Gemini** over `httpx` (already a dependency — no new package) via Gemini's official OpenAI-compatible chat completions endpoint. `candidate_id` is always resolved from the caller's own JWT, exactly like `/candidates/me`, so there is no way to request another candidate's data through this endpoint. Conversations persist to new `assistant_conversations`/`assistant_messages` tables, including a snapshot of the exact structured context each answer was grounded in.

**Gemini resilience** (retry/backoff/error differentiation): Gemini's flash models return HTTP 503 "model overloaded" under load — this is a normal, documented, *transient* condition, not a bug, and Google's own guidance is to retry with exponential backoff a small number of times. `GeminiProvider.chat()` does exactly that: up to `GEMINI_MAX_RETRIES` (default 2) retries with exponential backoff (capped at 8s) on 429/500/502/503/504 and network errors/timeouts; **never** on 401/403 (auth) or other 4xx, since retrying an identical bad credential or malformed request can't succeed. Auth failures raise a distinct `LLMAuthenticationError` (code `LLM_AUTHENTICATION_ERROR`) instead of the generic `ModelNotAvailableError`, so a misconfigured `GEMINI_API_KEY` is never confused with a transient outage in logs or in the `code` field of the response. Exhausted rate-limiting raises a distinct `LLMRateLimitError` (code `LLM_RATE_LIMITED`, HTTP 429) for the same reason. Every attempt logs `provider=gemini model=<model> attempt=N/M status=<code|timeout> latency_ms=<ms> retrying=<bool>` — never the API key or request/response bodies. Timeouts use `httpx.Timeout` with separate connect/read/write/pool values (`GEMINI_*_TIMEOUT_SECONDS`) rather than one flat number, since the read phase (waiting for generation) is the one that actually needs headroom under load.

**No vector database was introduced.** CareerIQ's candidate/job/skill data is already structured (not free-text documents needing semantic search), so the "retrieval" step is a direct, typed query through the existing repositories — a vector store would add real infrastructure for no corresponding value here. If unstructured content (e.g. full job description bodies) needs semantic retrieval later, `app/ai/context_builder.py` is the seam to extend without touching the prompt-building or provider layers.

Migration `0003_career_intelligence.py` adds the four new tables (`learning_plans`, `learning_plan_items`, `assistant_conversations`, `assistant_messages`) — purely additive, no existing table touched.

---

## Environment variables

All in `.env.example`. New in this upgrade:

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy connection string | `postgresql+psycopg://careeriq:careeriq@localhost:5432/careeriq` |
| `JWT_SECRET_KEY` | Signs/verifies JWTs. **Must be changed** for anything beyond local dev — the app refuses to start with the placeholder value when `DEBUG=false` | insecure placeholder |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `30` |
| `DEBUG` | Gates the insecure-secret startup check | `true` |
| `GEMINI_API_KEY` | Google Gemini API key (get a free one at https://aistudio.google.com/apikey). **Leave empty to run without the AI assistant** — every other feature works fully without it | empty |
| `GEMINI_BASE_URL` | Gemini's OpenAI-compatible chat completions base URL | `https://generativelanguage.googleapis.com/v1beta/openai` |
| `GEMINI_MODEL` | Model name to request | `gemini-3.7-flash` |
| `GEMINI_READ_TIMEOUT_SECONDS` | Timeout waiting for Gemini to generate a reply — the one that matters most under Gemini's documented transient "model overloaded" (503) behavior | `30.0` |
| `GEMINI_CONNECT_TIMEOUT_SECONDS` | TCP connect timeout | `5.0` |
| `GEMINI_WRITE_TIMEOUT_SECONDS` | Request-write timeout | `10.0` |
| `GEMINI_POOL_TIMEOUT_SECONDS` | Connection-pool acquisition timeout | `5.0` |
| `GEMINI_MAX_RETRIES` | Retries on 429/500/502/503/504 or network errors, with exponential backoff (never on 401/403 auth failures, or other 4xx) — small and bounded per Google's own guidance | `2` |
| `GEMINI_RETRY_BASE_DELAY_SECONDS` | Base delay for exponential backoff between retries (capped at 8s) | `1.0` |

No real secrets are committed anywhere in this repo; `.env` remains
git-ignored.

---

## Database schema (Phase 3)

```text
users -+- candidates -+- candidate_skills
       |               +- candidate_education
       |               +- candidate_experience
       |               +- candidate_projects
       |               +- candidate_certifications
       |               +- resumes
       |               +- matching_results -- skill_gaps
       |               +- recommendations
       |               +- applications
       +- jobs ---------+- job_skills
                         +- matching_results
                         +- recommendations
                         +- applications

model_versions  (referenced optionally by matching_results / recommendations)
```

Full detail in `app/db/models/`. Migration: `alembic/versions/0001_initial.py`
(hand-written — `alembic` isn't installed in this sandbox so
`alembic revision --autogenerate` could not be run here; please diff it
against the models and regenerate in a real environment before applying to
a shared database).

```bash
alembic upgrade head      # apply
alembic downgrade -1      # roll back one revision
```

---

## What's verified vs. written

| Component | Status |
|---|---|
| All Phase-1 NLP/ML functionality (resume/job parsing, matching, skill-gap, recommendation) | Verified — unchanged, still passing |
| `careeriq_workflow_service.py` (Phase 2 end-to-end orchestration) | Verified — built + run directly, produces correct pipeline output |
| Structured error envelope, request-ID middleware, global exception handlers | Written to spec, syntax-checked; not runtime-tested (no `fastapi` here) |
| `app/auth/security.py` (password hashing + JWT) | Verified — hash/verify round-trips, JWT issue/decode/expiry/tamper-detection all executed and passing (PyJWT is installed here; passlib isn't, so the tested path is the stdlib PBKDF2 fallback, not argon2) |
| `app/auth/dependencies.py`, RBAC role guards, ownership checks | Written to spec, syntax-checked; not runtime-tested (needs `fastapi` + DB) |
| SQLAlchemy models, repositories, Alembic migration | Written to spec, syntax-checked; **not executed against a real database** (no PostgreSQL/sqlalchemy/psycopg here) |
| `docker-compose.yml` Postgres service, Dockerfile migration step | Written to spec; not built/run here |
| 42 unit tests (`tests/unit/`) | Verified — all passing, `python -m unittest discover -s tests/unit` |
| Integration tests (`tests/integration/`) | Written with `pytest.importorskip` / DB-reachability skips so they fail loudly only when they should, not silently pass; not run here for real |
| Phase 8 job application workflow (routes, service, repository, migration `0002`, frontend apply/applications/applicants UI) | Written to spec, syntax-checked (backend `py_compile` clean, frontend static `tsc` check clean); **not executed against a real database** — `test_applications_api.py`'s 10 required cases have not been run |
| Skill Gap priority classification, Learning Recommendation engine, Career Plan milestone/practice-project logic | **Verified** — pure-logic layers (no DB/network needed) actually executed: 27 new unit tests, including dependency-ordering, priority-ordering, and milestone-grouping checks, all passing |
| Recommendation Explanation (`explain=True` enrichment) | **Verified** — executed directly, confirmed backward-compatible (no new fields when `explain=False`) and that `score_breakdown` matches the underlying `matching_service.calculate_match` output exactly |
| AI Assistant: Gemini provider (`app/ai/llm_provider.py`) + prompt builder | **Verified** — graceful-unavailability path (no API key configured) executed; full mocked-HTTP matrix executed too (successful call, 401 auth failure, 429 rate limit, timeout, malformed response, API key never leaked in error messages — see `tests/unit/test_llm_provider.py`, `httpx` itself isn't installed here so a fake `httpx` module is injected into `sys.modules` for these); prompt-grounding/context-embedding logic executed directly. A real network call to the live Gemini API has **not** been executed (no network access, no API key in this sandbox) |
| AI Assistant context builder, career-plan/skill-gap/learning DB-backed routes, `0003_career_intelligence` migration | Written to spec, syntax-checked; **not executed against a real database** (no PostgreSQL/sqlalchemy here) |

**Before trusting Phases 3-4, the Phase 8 application workflow, or the new
career-intelligence layer in your environment**: run
`pip install -r requirements-dev.txt`, start Postgres
(`docker compose up -d postgres`), run `alembic upgrade head` (now three
migrations: `0001_initial`, `0002_applications_match_score`,
`0003_career_intelligence`), set `GEMINI_API_KEY` if you want to exercise the
AI assistant for real, then run the full `pytest` suite — including
`tests/integration/test_applications_api.py` and
`tests/integration/test_career_intelligence_api.py` — and manually walk
register -> login -> resume upload -> view a job's skill gap -> view
learning recommendations -> generate a career plan -> ask the AI assistant
a question about it. I was not able to do that walk myself in this
sandbox.

---

## ML models used and why

(Unchanged from Phase 1 — see `MODEL_CARD.md` for full detail.)
Skill/entity extraction is taxonomy-driven phrase matching; baseline
matching is a transparent weighted rule combination; the candidate-job
classifier is Logistic Regression (chosen over Random Forest at
near-identical validation F1, preferring the simpler model); semantic
similarity uses Sentence-Transformer embeddings with an automatic TF-IDF
cosine-similarity fallback (the fallback is what's actually exercised in
this sandbox); recommendation is TF-IDF + skill-overlap content-based
scoring with a semantic variant and a hybrid blend.

---

## Testing summary

- **85/85 unit tests passing** (`python -m unittest discover -s tests/unit -v`):
  30 from Phase 1 (NLP/matching/skill-gap/edge cases) + 9 for
  password-hashing/JWT + 3 for the end-to-end workflow orchestration + 43
  for the career-intelligence layer (6 skill-priority tests, 7 learning-recommender
  tests covering dependency ordering/difficulty/no-fabricated-URLs, 5
  recommendation-explanation tests including a check that `score_breakdown`
  matches `matching_service.calculate_match` exactly, 3 career-plan
  milestone-ordering tests, 22 Gemini-provider/prompt-builder tests covering
  all 7 required resilience scenarios — successful call, 503-then-successful-retry,
  repeated 503 exhausting retries, timeout, repeated 429 raising a distinct
  rate-limit error, 401/403 raising a distinct auth error without retrying,
  and a malformed response failing without retrying — plus API-key-never-leaked
  and injection-resistant context embedding).
- **Integration tests written, not run here**: 8 existing FastAPI tests
  (`test_api.py`), 12 auth/RBAC tests (`test_auth_api.py` — registration,
  duplicate/invalid-email/weak-password rejection, login success/failure,
  `/me`, missing/invalid token, candidate-to-recruiter 403, recruiter-to-recruiter
  200, candidate-A-to-candidate-B 403), 3 DB tests (`test_database.py` —
  user creation, candidate/skill relationship, job/skill relationship), 10
  application-workflow tests (`test_applications_api.py`), and 10 new
  career-intelligence tests (`test_career_intelligence_api.py` — job-centric
  skill gap with real priorities, candidate-cannot-view-another's-gap,
  learning recommendations for both a persisted job and an arbitrary skill
  set, career-plan generate/retrieve/ownership, AI assistant graceful
  unavailability/role-enforcement/auth-required/missing-job-404). All
  DB-dependent tests use `pytest.mark.skipif` against a real
  reachability check, not a mock, so they can't silently "pass" against a
  missing database.

---

## Limitations (honest account)

- Everything in the Phase-3/4 "written, not executed" row above needs to be
  validated by you against a real Postgres + full dependency install before
  going further — I built it carefully and syntax-checked the whole tree,
  but I have not seen it run end-to-end against a live database or a live
  FastAPI server.
- No refresh-token / logout endpoint (see Authentication section above for
  why).
- No rate limiting on `/auth/login` or `/auth/register` — worth adding
  before production (e.g. via a reverse proxy or `slowapi`).
- `model_versions` table exists but isn't populated by `train_matching.py`
  yet (see `MODEL_CARD.md`).
- Entity extraction (name/company/institution) remains regex/heuristic
  based, as in Phase 1 — unaffected by this upgrade.
- Candidate-job classifier is trained on synthetic data; the important
  caveat about what its metrics do/don't prove is unchanged and documented
  in `MODEL_CARD.md`.
- Semantic similarity runs on the TF-IDF fallback in this build
  environment, not true sentence embeddings.
- `applications.model_version_id` is always `null` for now, for the same
  reason `model_versions` isn't populated yet.
- No withdraw-application endpoint for candidates, and no way for a
  recruiter to bulk-update applicant status — both reasonable follow-ups,
  neither was in this phase's scope.
- The recruiter's "Rank candidates" (`/recruiter/jobs/{id}/candidates`) and
  "Applicants" (`/recruiter/jobs/{id}/applicants`) views are intentionally
  separate: ranking scores every persisted candidate against the job,
  applicants only shows people who actually applied.
- The AI assistant has never been called against the real Gemini API in
  this environment (no network access, no API key) — the graceful-unavailable
  path and the full HTTP error-handling matrix (auth failure, rate limit,
  timeout, malformed response) are verified against a mocked HTTP layer;
  a real network call is not. Get a free key at
  https://aistudio.google.com/apikey and set `GEMINI_API_KEY` to test it
  for real before relying on it.
- `POST /api/v1/learning/recommendations` (the career-level, no-persisted-job
  variant) is reachable by any authenticated user, not ownership-scoped,
  since it takes a raw skill list rather than a candidate/job id — this is
  intentional (there's no candidate-specific data to protect in that request
  shape) but worth knowing if you extend it to accept a candidate_id later.
- Assistant conversation history is included in the prompt on every turn,
  unbounded — for a very long conversation this will eventually hit the
  provider's context window. No truncation/summarization is implemented.
- Career plan "difficulty" and learning-item "priority" are heuristics
  derived from the taxonomy structure and skill-gap categories, not a
  learned/calibrated model — documented as such in code comments, not
  presented as more precise than that.

## Future improvements

- Populate `model_versions` from the training scripts and wire
  `MatchingResult.model_version_id` / `Recommendation.model_version_id`
  through the live matching/recommendation calls
- Rate limiting + account lockout on repeated failed logins
- Object storage (S3/GCS) behind the existing `LocalResumeStorage`
  interface — no application code changes needed elsewhere
- Collaborative filtering using the `applications` table
  (`RecommendationSignal` extension point already exists in
  `content_based.py`)
- Refresh tokens with a server-side revocation store, if session
  invalidation before expiry becomes a real requirement
