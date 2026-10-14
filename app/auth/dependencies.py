"""
FastAPI dependencies for authentication and RBAC.

`get_current_user` decodes the JWT and cross-checks against the DB (so a
deactivated user's existing token stops working immediately, not just after
expiry). Role guards (`require_candidate`, `require_recruiter`,
`require_admin`) build on top of it. Ownership checks are separate,
explicit dependencies -- a role alone never proves ownership of a specific
resource (spec: "authorization must be enforced by the backend").
"""
from __future__ import annotations

import uuid

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.models import CurrentUser, Role
from app.auth.security import decode_access_token
from app.core.exceptions import ForbiddenError, InactiveUserError, InvalidTokenError, NotFoundError
from app.db.session import get_db
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.candidate_repository import CandidateRepository

# auto_error=False so we raise our own structured AuthError instead of FastAPI's default 401.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> CurrentUser:
    if not token:
        raise InvalidTokenError("Missing authentication token.")

    claims = decode_access_token(token)
    try:
        user_id = uuid.UUID(claims["sub"])
    except (KeyError, ValueError):
        raise InvalidTokenError("Malformed token payload.")

    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise InvalidTokenError("User no longer exists.")
    if not user.is_active:
        raise InactiveUserError()

    return CurrentUser(id=user.id, email=user.email, role=Role(user.role.value if hasattr(user.role, "value") else user.role), is_active=user.is_active)


def require_authenticated(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    return current_user


def require_role(*allowed_roles: Role):
    def _dependency(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise ForbiddenError(f"This action requires one of: {', '.join(r.value for r in allowed_roles)}.")
        return current_user

    return _dependency


# ADMIN is implicitly allowed everywhere a specific role is required, per spec
# ("ADMIN can manage system-level resources") -- but ADMIN is never granted
# automatically to a RECRUITER or vice versa.
require_candidate = require_role(Role.CANDIDATE, Role.ADMIN)
require_recruiter = require_role(Role.RECRUITER, Role.ADMIN)
require_admin = require_role(Role.ADMIN)


def require_own_candidate_profile(candidate_id: uuid.UUID, current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)) -> CurrentUser:
    """
    Ownership check for candidate-scoped resources (profile, resumes,
    matching history). ADMIN bypasses the ownership check; every other role
    (including a *different* CANDIDATE) is rejected with 403 -- this is what
    stops candidate A from reading candidate B's data even though both hold
    valid CANDIDATE-role tokens.
    """
    if current_user.role == Role.ADMIN:
        return current_user

    candidate = CandidateRepository(db).get_by_id(candidate_id)
    if candidate is None:
        raise NotFoundError("Candidate not found.")
    if candidate.user_id != current_user.id:
        raise ForbiddenError("You may only access your own candidate profile.")
    return current_user
