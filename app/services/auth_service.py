"""
Auth service: registration and login business logic. Routes call this, not
the repository directly, so validation/hashing/token-issuing logic lives in
one place.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.auth.models import Role
from app.auth.security import create_access_token, hash_password, verify_password
from app.core.exceptions import DuplicateUserError, InactiveUserError, InvalidCredentialsError
from app.db.repositories.candidate_repository import CandidateRepository
from app.db.repositories.user_repository import UserRepository


def register_user(db: Session, email: str, password: str, role: Role) -> "User":
    from app.db.models.user import User  # local import avoids a circular import with app.db.models.__init__

    repo = UserRepository(db)
    if repo.get_by_email(email) is not None:
        raise DuplicateUserError()

    # ADMIN cannot be self-assigned through public registration; only
    # CANDIDATE/RECRUITER are reachable here, per spec ("assign safe default role").
    safe_role = role if role in (Role.CANDIDATE, Role.RECRUITER) else Role.CANDIDATE

    user = repo.create(email=email, password_hash=hash_password(password), role=safe_role.value)

    # Every CANDIDATE gets an (initially empty) candidate profile row at
    # registration time so downstream resume/matching flows always have
    # somewhere to attach data.
    if safe_role == Role.CANDIDATE:
        CandidateRepository(db).create_for_user(user.id)

    return user


def authenticate_user(db: Session, email: str, password: str) -> "User":
    from app.db.models.user import User

    repo = UserRepository(db)
    user = repo.get_by_email(email)
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError()
    if not user.is_active:
        raise InactiveUserError()
    return user


def issue_token_for_user(user) -> dict:
    role_value = user.role.value if hasattr(user.role, "value") else user.role
    token = create_access_token(subject=user.id, role=role_value)
    from app.core.config import settings

    return {"access_token": token, "token_type": "bearer", "expires_in_minutes": settings.jwt_access_token_expire_minutes}
