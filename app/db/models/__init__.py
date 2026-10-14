"""
Import every ORM model here so `Base.metadata` is fully populated -- Alembic's
autogenerate and `Base.metadata.create_all()` both rely on every model having
been imported at least once before they run.
"""
from app.db.session import Base  # noqa: F401
from app.db.models.user import User  # noqa: F401
from app.db.models.candidate import (  # noqa: F401
    Candidate,
    CandidateSkill,
    CandidateEducation,
    CandidateExperience,
    CandidateProject,
    CandidateCertification,
)
from app.db.models.resume import Resume  # noqa: F401
from app.db.models.job import Job, JobSkill  # noqa: F401
from app.db.models.application import Application  # noqa: F401
from app.db.models.matching import MatchingResult, SkillGapRecord  # noqa: F401
from app.db.models.recommendation import Recommendation  # noqa: F401
from app.db.models.model_version import ModelVersion  # noqa: F401
from app.db.models.learning_plan import LearningPlan, LearningPlanItem  # noqa: F401
from app.db.models.assistant import AssistantConversation, AssistantMessage  # noqa: F401
from app.db.models.knowledge import KnowledgeDocument, KnowledgeChunk  # noqa: F401
from app.db.models.background_task import BackgroundTask  # noqa: F401

__all__ = [
    "Base",
    "User",
    "Candidate",
    "CandidateSkill",
    "CandidateEducation",
    "CandidateExperience",
    "CandidateProject",
    "CandidateCertification",
    "Resume",
    "Job",
    "JobSkill",
    "Application",
    "MatchingResult",
    "SkillGapRecord",
    "Recommendation",
    "ModelVersion",
    "LearningPlan",
    "LearningPlanItem",
    "AssistantConversation",
    "AssistantMessage",
    "KnowledgeDocument",
    "KnowledgeChunk",
    "BackgroundTask",
]
