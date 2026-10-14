"""
Custom exception hierarchy for the CareerIQ ML service.

API routes catch these and translate them into clean HTTP responses without
leaking stack traces or internal details to the client (the real exception
is logged server-side instead).
"""
from __future__ import annotations


class CareerIQError(Exception):
    """Base class for all application-raised errors."""

    status_code: int = 500
    code: str = "INTERNAL_ERROR"
    default_message: str = "An internal error occurred."

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class UnsupportedFileTypeError(CareerIQError):
    status_code = 415
    code = "UNSUPPORTED_FILE_TYPE"
    default_message = "Unsupported file type. Allowed: .pdf, .docx, .txt"


class FileTooLargeError(CareerIQError):
    status_code = 413
    code = "FILE_TOO_LARGE"
    default_message = "Uploaded file exceeds the maximum allowed size."


class CorruptedDocumentError(CareerIQError):
    status_code = 422
    code = "CORRUPTED_DOCUMENT"
    default_message = "The document could not be read; it may be corrupted."


class EmptyDocumentError(CareerIQError):
    status_code = 422
    code = "EMPTY_DOCUMENT"
    default_message = "The document contains no extractable text."


class InvalidRequestError(CareerIQError):
    status_code = 400
    code = "VALIDATION_ERROR"
    default_message = "The request payload is invalid."


class ModelNotAvailableError(CareerIQError):
    status_code = 503
    code = "MODEL_NOT_AVAILABLE"
    default_message = "A required ML model is not currently available."


class InferenceError(CareerIQError):
    status_code = 500
    code = "INFERENCE_ERROR"
    default_message = "Model inference failed."


# --- Auth / RBAC (Phase 4) --------------------------------------------------

class AuthError(CareerIQError):
    status_code = 401
    code = "AUTH_ERROR"
    default_message = "Authentication failed."


class InvalidCredentialsError(AuthError):
    code = "INVALID_CREDENTIALS"
    default_message = "Invalid email or password."


class TokenExpiredError(AuthError):
    code = "TOKEN_EXPIRED"
    default_message = "Authentication token has expired."


class InvalidTokenError(AuthError):
    code = "INVALID_TOKEN"
    default_message = "Authentication token is invalid."


class InactiveUserError(AuthError):
    code = "INACTIVE_USER"
    default_message = "This account is inactive."


class DuplicateUserError(CareerIQError):
    status_code = 409
    code = "DUPLICATE_USER"
    default_message = "An account with this email already exists."


class ForbiddenError(CareerIQError):
    status_code = 403
    code = "FORBIDDEN"
    default_message = "You do not have permission to perform this action."


class NotFoundError(CareerIQError):
    status_code = 404
    code = "NOT_FOUND"
    default_message = "The requested resource was not found."


# --- Applications (Phase 8) --------------------------------------------------

class DuplicateApplicationError(CareerIQError):
    status_code = 409
    code = "DUPLICATE_APPLICATION"
    default_message = "You have already applied to this job."


# --- AI Career Assistant / LLM provider --------------------------------------
# Kept distinct from ModelNotAvailableError (which now means "we tried,
# retried a bounded number of times, and the provider is still not
# responding usefully") -- an auth failure or a rate limit are not the same
# situation operationally, and conflating them was flagged as a real bug:
# a misconfigured GEMINI_API_KEY looked identical in logs/responses to a
# transient Gemini outage, making the actual problem hard to diagnose.

class LLMAuthenticationError(CareerIQError):
    status_code = 503  # client-facing contract unchanged (still "assistant unavailable"); the `code` below is what's new and distinct
    code = "LLM_AUTHENTICATION_ERROR"
    default_message = "The AI Career Assistant is not configured correctly. Please contact support."


class LLMRateLimitError(CareerIQError):
    status_code = 429
    code = "LLM_RATE_LIMITED"
    default_message = "The AI Career Assistant is temporarily rate-limited. Please try again in a moment."
