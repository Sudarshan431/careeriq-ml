import json
from pathlib import Path

from fastapi import APIRouter

from app.core.config import settings
from app.db.session import database_is_reachable

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness/readiness check")
def health_check():
    """
    Public, unauthenticated. Reports service status and whether the
    database is reachable -- never the connection string, credentials, or
    any other config value.
    """
    db_ok = database_is_reachable()
    return {
        "status": "ok" if db_ok else "degraded",
        "service": "careeriq-ml",
        "database": "up" if db_ok else "down",
    }


@router.get("/api/v1/models")
def list_models():
    """Returns metadata for every persisted model artifact under MODEL_DIR."""
    model_dir = Path(settings.model_dir)
    artifacts = []
    if model_dir.exists():
        for meta_file in model_dir.rglob("metadata.json"):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    artifacts.append(json.load(f))
            except Exception:
                continue
    return {"models": artifacts}
