"""Resume analysis endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.auth.dependencies import require_candidate
from app.auth.models import CurrentUser
from app.schemas.resume import ResumeAnalyzeResponse
from app.services.resume_service import analyze_resume

router = APIRouter(prefix="/api/v1/resume", tags=["resume"])


@router.post(
    "/analyze",
    response_model=ResumeAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse a resume file into a structured candidate profile",
    description=(
        "Accepts a .pdf, .docx, or .txt resume file and returns extracted "
        "skills, education, experience, projects, and certifications. "
        "Requires an authenticated CANDIDATE or ADMIN."
    ),
    responses={
        415: {"description": "Unsupported file type"},
        413: {"description": "File exceeds the configured size limit"},
        422: {"description": "Empty or corrupted document"},
    },
)
async def analyze_resume_endpoint(
    file: UploadFile = File(..., description="Resume file (.pdf, .docx, or .txt)"),
    current_user: CurrentUser = Depends(require_candidate),
):
    file_bytes = await file.read()
    profile = analyze_resume(file_bytes, file.filename)
    return {"profile": profile}
