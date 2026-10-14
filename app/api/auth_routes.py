"""Authentication endpoints: register, login, /me."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_authenticated
from app.auth.models import CurrentUser
from app.db.session import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth_service import authenticate_user, issue_token_for_user, register_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new CANDIDATE or RECRUITER account",
    description="Creates a new user. ADMIN accounts cannot be created through this endpoint. "
    "Passwords must be at least 8 characters and contain both letters and numbers.",
    responses={409: {"description": "An account with this email already exists"}},
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    user = register_user(db, payload.email, payload.password, payload.role)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Log in and receive a JWT access token",
    responses={401: {"description": "Invalid credentials or inactive account"}},
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.email, payload.password)
    return issue_token_for_user(user)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the currently authenticated user",
)
def me(current_user: CurrentUser = Depends(require_authenticated)):
    return current_user
