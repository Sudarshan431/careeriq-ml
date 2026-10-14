"""
FastAPI entrypoint for the CareerIQ ML microservice.

Run locally:  uvicorn app.main:app --reload --port 8000
Run in Docker: see Dockerfile / docker-compose.yml
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import CareerIQError
from app.core.logging_config import configure_logging, get_logger, get_request_id, new_request_id
from app.api import (
    resume_routes,
    job_routes,
    jobs_routes,
    matching_routes,
    recommendation_routes,
    skill_routes,
    health_routes,
    auth_routes,
    candidate_routes,
    recruiter_routes,
    applications_routes,
    skill_gap_routes,
    learning_routes,
    career_plan_routes,
    assistant_routes,
    rag_routes,
)

configure_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description=(
        "CareerIQ ML microservice: resume parsing, job description parsing, "
        "candidate-job matching, skill-gap analysis, job recommendations, "
        "PostgreSQL persistence, and JWT-based authentication with RBAC "
        "(CANDIDATE / RECRUITER / ADMIN)."
    ),
)

origins = [o.strip() for o in settings.cors_origins.split(",")] if settings.cors_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Assigns a request ID to every inbound request so it can be correlated
    across logs and echoed back in the structured error envelope."""
    new_request_id()
    response = await call_next(request)
    response.headers["X-Request-ID"] = get_request_id()
    return response


def _error_envelope(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message, "request_id": get_request_id()}}


@app.exception_handler(CareerIQError)
async def careeriq_error_handler(request: Request, exc: CareerIQError):
    # Auth/permission errors are logged at INFO (expected, routine); everything
    # else at ERROR. Never log request bodies, tokens, or resume content here.
    log_fn = logger.info if exc.status_code in (401, 403, 404, 409) else logger.error
    log_fn("Handled error on %s: code=%s message=%s", request.url.path, exc.code, exc.message)
    return JSONResponse(status_code=exc.status_code, content=_error_envelope(exc.code, exc.message))


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    # Pydantic gives detailed per-field errors; we log them (safe -- field
    # names/types, not values) but return a clean, non-leaky summary to the client.
    logger.info("Validation error on %s: %s", request.url.path, exc.errors())
    return JSONResponse(status_code=422, content=_error_envelope("VALIDATION_ERROR", "Invalid request payload."))


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Safety net for any HTTPException raised outside our CareerIQError
    # hierarchy (e.g. by third-party dependencies) -- wraps it in the same
    # structured envelope instead of returning FastAPI's default {"detail": ...}.
    code = {401: "AUTH_ERROR", 403: "FORBIDDEN", 404: "NOT_FOUND"}.get(exc.status_code, "ERROR")
    return JSONResponse(status_code=exc.status_code, content=_error_envelope(code, str(exc.detail)))


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    # Never leak stack traces, file paths, or exception internals to the client.
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content=_error_envelope("INTERNAL_ERROR", "An internal error occurred."))


app.include_router(health_routes.router)
app.include_router(auth_routes.router)
app.include_router(resume_routes.router)
app.include_router(job_routes.router)
app.include_router(jobs_routes.router)
app.include_router(matching_routes.router)
app.include_router(recommendation_routes.router)
app.include_router(skill_routes.router)
app.include_router(candidate_routes.router)
app.include_router(recruiter_routes.router)
app.include_router(applications_routes.router)
app.include_router(skill_gap_routes.router)
app.include_router(learning_routes.router)
app.include_router(career_plan_routes.router)
app.include_router(assistant_routes.router)
app.include_router(rag_routes.router)


@app.get("/", tags=["health"])
def root():
    return {"service": settings.app_name, "docs": "/docs", "health": "/health"}
