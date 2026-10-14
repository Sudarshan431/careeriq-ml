"""
Central configuration for the CareerIQ ML service.

All environment-specific values (paths, model names, matching weights, CORS
origins, file-size limits) live here and are sourced from environment
variables / a .env file. Nothing below should be hardcoded elsewhere.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

BASE_DIR = Path(__file__).resolve().parent.parent.parent

try:
    from pydantic_settings import BaseSettings
    from pydantic import Field

    _HAS_PYDANTIC = True
except ImportError:  # pydantic-settings not installed in this environment
    _HAS_PYDANTIC = False


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _env_list(name: str, default: str) -> List[str]:
    return [x.strip() for x in os.getenv(name, default).split(",") if x.strip()]


if _HAS_PYDANTIC:

    class Settings(BaseSettings):
        # --- App ---
        app_name: str = "CareerIQ ML Service"
        api_v1_prefix: str = "/api/v1"
        log_level: str = Field(default="INFO")
        cors_origins: str = Field(default="*")

        # --- Paths ---
        model_dir: str = str(BASE_DIR / "models")
        taxonomy_dir: str = str(BASE_DIR / "app" / "taxonomy")
        data_dir: str = str(BASE_DIR / "data")

        # --- Files ---
        max_file_size_mb: int = 10
        allowed_extensions: str = ".pdf,.docx,.txt"

        # --- Embeddings ---
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

        # --- Baseline matching weights (must sum to 1.0) ---
        match_skill_weight: float = 0.50
        match_experience_weight: float = 0.20
        match_education_weight: float = 0.10
        match_location_weight: float = 0.10
        match_preference_weight: float = 0.10

        # --- Hybrid matching weights (must sum to 1.0) ---
        hybrid_skill_weight: float = 0.50
        hybrid_semantic_weight: float = 0.30
        hybrid_experience_weight: float = 0.15
        hybrid_education_weight: float = 0.05

        # --- Auth / JWT ---
        jwt_secret_key: str = "insecure-dev-secret-key-change-me"
        jwt_algorithm: str = "HS256"
        jwt_access_token_expire_minutes: int = 30
        debug: bool = True

        # --- Database ---
        database_url: str = "postgresql+psycopg://careeriq:careeriq@localhost:5432/careeriq"

        # --- AI Career Assistant / Gemini ---
        # Gemini exposes an OpenAI-compatible chat completions endpoint, so
        # this is the only concrete provider -- see app/ai/llm_provider.py.
        gemini_api_key: str = ""  # empty = assistant reports itself unavailable; never hardcode a real key here
        gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai"
        gemini_model: str = "gemini-3.7-flash"
        # Granular timeouts (httpx.Timeout) rather than one flat value: the
        # "read" phase (waiting for the model to actually generate a reply)
        # is the one that legitimately needs headroom under load -- connect/
        # write to Google's endpoint are normally fast. The old
        # GEMINI_TIMEOUT_SECONDS (flat, applied to everything, default 20s)
        # is replaced by GEMINI_READ_TIMEOUT_SECONDS (default 30s) plus the
        # three dedicated vars below -- this is a deliberate, documented
        # rename, not an oversight: 503/timeout reports traced back to
        # Gemini's own documented "model overloaded" transient behavior,
        # which needs a realistic read deadline to have any chance of
        # succeeding within it, while connect/write never needed 20s.
        gemini_read_timeout_seconds: float = 30.0
        gemini_connect_timeout_seconds: float = 5.0
        gemini_write_timeout_seconds: float = 10.0
        gemini_pool_timeout_seconds: float = 5.0
        # Retries: Google's own guidance for 503 "model overloaded" is retry
        # with exponential backoff, no more than ~2 times (retries also
        # count against free-tier quota, so this must stay small/bounded).
        gemini_max_retries: int = 2
        gemini_retry_base_delay_seconds: float = 1.0

        class Config:
            env_file = ".env"
            case_sensitive = False

    settings = Settings()

else:
    # Minimal fallback so the rest of the codebase (and this sandbox, which
    # doesn't have pydantic-settings installed) can still import `settings`.
    class Settings:
        app_name = "CareerIQ ML Service"
        api_v1_prefix = "/api/v1"
        log_level = os.getenv("LOG_LEVEL", "INFO")
        cors_origins = os.getenv("CORS_ORIGINS", "*")

        model_dir = os.getenv("MODEL_DIR", str(BASE_DIR / "models"))
        taxonomy_dir = os.getenv("TAXONOMY_DIR", str(BASE_DIR / "app" / "taxonomy"))
        data_dir = os.getenv("DATA_DIR", str(BASE_DIR / "data"))

        max_file_size_mb = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
        allowed_extensions = os.getenv("ALLOWED_EXTENSIONS", ".pdf,.docx,.txt")

        embedding_model = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

        match_skill_weight = _env_float("MATCH_SKILL_WEIGHT", 0.50)
        match_experience_weight = _env_float("MATCH_EXPERIENCE_WEIGHT", 0.20)
        match_education_weight = _env_float("MATCH_EDUCATION_WEIGHT", 0.10)
        match_location_weight = _env_float("MATCH_LOCATION_WEIGHT", 0.10)
        match_preference_weight = _env_float("MATCH_PREFERENCE_WEIGHT", 0.10)

        hybrid_skill_weight = _env_float("HYBRID_SKILL_WEIGHT", 0.50)
        hybrid_semantic_weight = _env_float("HYBRID_SEMANTIC_WEIGHT", 0.30)
        hybrid_experience_weight = _env_float("HYBRID_EXPERIENCE_WEIGHT", 0.15)
        hybrid_education_weight = _env_float("HYBRID_EDUCATION_WEIGHT", 0.05)

        jwt_secret_key = os.getenv("JWT_SECRET_KEY", "insecure-dev-secret-key-change-me")
        jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        jwt_access_token_expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        debug = os.getenv("DEBUG", "true").lower() in ("1", "true", "yes")

        database_url = os.getenv(
            "DATABASE_URL", "postgresql+psycopg://careeriq:careeriq@localhost:5432/careeriq"
        )

        gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        gemini_base_url = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai")
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")
        gemini_read_timeout_seconds = _env_float("GEMINI_READ_TIMEOUT_SECONDS", 30.0)
        gemini_connect_timeout_seconds = _env_float("GEMINI_CONNECT_TIMEOUT_SECONDS", 5.0)
        gemini_write_timeout_seconds = _env_float("GEMINI_WRITE_TIMEOUT_SECONDS", 10.0)
        gemini_pool_timeout_seconds = _env_float("GEMINI_POOL_TIMEOUT_SECONDS", 5.0)
        gemini_max_retries = int(os.getenv("GEMINI_MAX_RETRIES", "2"))
        gemini_retry_base_delay_seconds = _env_float("GEMINI_RETRY_BASE_DELAY_SECONDS", 1.0)

    settings = Settings()
