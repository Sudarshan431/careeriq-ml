"""Job recommendation endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.auth.dependencies import require_candidate
from app.auth.models import CurrentUser
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services.recommendation_service import recommend_jobs

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@router.post(
    "/jobs",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Recommend jobs for a candidate",
    description="Content-based / semantic / hybrid job recommendations for a candidate profile. "
    "Restricted to CANDIDATE and ADMIN roles.",
)
def recommend_jobs_endpoint(payload: RecommendationRequest, current_user: CurrentUser = Depends(require_candidate)):
    jobs = [j.model_dump() for j in payload.jobs]
    recs = recommend_jobs(payload.candidate.model_dump(), jobs, payload.top_k, payload.strategy, payload.explain)
    return {"recommendations": recs}
