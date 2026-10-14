"""
Password hashing and JWT handling.

Password hashing: prefers passlib's CryptContext with Argon2 (production
default per the spec). Falls back to a stdlib PBKDF2-HMAC-SHA256 hasher with
the *same* hash_password/verify_password interface when passlib/argon2
aren't installed (this sandbox has neither) -- this keeps the hashing logic
genuinely testable here rather than only "written but never run". Swap
happens transparently based on what's importable; nothing else in the
codebase needs to know which backend is active.

JWT: uses PyJWT (installed in this environment, so this part is exercised
for real, not just written to spec). All configuration (secret, algorithm,
expiry) comes from settings / environment -- never hardcoded.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt as pyjwt

from app.core.config import settings
from app.core.exceptions import InvalidTokenError, TokenExpiredError

# --------------------------------------------------------------------------
# Password hashing
# --------------------------------------------------------------------------

try:
    from passlib.context import CryptContext

    _pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

    def hash_password(plain_password: str) -> str:
        return _pwd_context.hash(plain_password)

    def verify_password(plain_password: str, password_hash: str) -> bool:
        try:
            return _pwd_context.verify(plain_password, password_hash)
        except Exception:
            return False

    PASSWORD_HASH_BACKEND = "passlib-argon2"

except ImportError:
    # --- Fallback: stdlib PBKDF2-HMAC-SHA256, salted, constant-time compare ---
    # Format: pbkdf2_sha256$<iterations>$<salt_b64>$<hash_b64>
    _PBKDF2_ITERATIONS = 260_000

    def hash_password(plain_password: str) -> str:
        salt = secrets.token_bytes(16)
        derived = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
        return "pbkdf2_sha256${}${}${}".format(
            _PBKDF2_ITERATIONS,
            base64.b64encode(salt).decode("ascii"),
            base64.b64encode(derived).decode("ascii"),
        )

    def verify_password(plain_password: str, password_hash: str) -> bool:
        try:
            scheme, iterations_s, salt_b64, hash_b64 = password_hash.split("$")
            if scheme != "pbkdf2_sha256":
                return False
            iterations = int(iterations_s)
            salt = base64.b64decode(salt_b64)
            expected = base64.b64decode(hash_b64)
        except (ValueError, TypeError):
            return False
        derived = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(derived, expected)

    PASSWORD_HASH_BACKEND = "stdlib-pbkdf2-sha256-fallback"


# --------------------------------------------------------------------------
# JWT
# --------------------------------------------------------------------------

def create_access_token(subject: str | uuid.UUID, role: str, expires_minutes: int | None = None) -> str:
    """
    Creates a signed JWT. Claims are intentionally minimal (sub, role, iat,
    exp, jti) -- no email, no PII beyond what's needed to identify and
    authorize the user, per the spec's "no sensitive information inside JWT
    claims" requirement.
    """
    now = datetime.now(timezone.utc)
    expires_minutes = expires_minutes or settings.jwt_access_token_expire_minutes
    payload = {
        "sub": str(subject),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
        "jti": uuid.uuid4().hex,
    }
    return pyjwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodes and validates a JWT, raising our own auth exceptions (never leaks the raw PyJWT error)."""
    try:
        return pyjwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except pyjwt.ExpiredSignatureError:
        raise TokenExpiredError()
    except pyjwt.InvalidTokenError:
        raise InvalidTokenError()


def require_configured_secret() -> None:
    """
    Fail safely (per spec) if JWT_SECRET_KEY is missing or looks like an
    insecure default -- call this at startup in non-debug environments.
    """
    secret = settings.jwt_secret_key
    if not secret or secret in {"changeme", "secret", "insecure-dev-secret-key-change-me"}:
        if not settings.debug:
            raise RuntimeError(
                "JWT_SECRET_KEY is missing or insecure. Set a strong, unique JWT_SECRET_KEY "
                "in the environment before running in a non-debug environment."
            )
