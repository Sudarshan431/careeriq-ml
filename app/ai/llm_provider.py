"""
LLM provider abstraction for the AI Career Assistant.

No provider-specific logic is scattered elsewhere in the codebase --
app.services.assistant_service only ever calls `get_llm_provider().chat(...)`.

Provider: Google Gemini, called via `httpx` (already a project dependency,
see requirements.txt) against Gemini's official OpenAI-compatible chat
completions endpoint (https://ai.google.dev/gemini-api/docs/openai) rather
than adding a new provider SDK dependency. This is why migrating from a
generic OpenAI-compatible setup to Gemini required no new dependency and
almost no code change: the request/response wire format
(`POST {base_url}/chat/completions` with `model`/`messages`, response at
`choices[0].message.content`) is identical -- only the configured
base_url/api_key/model default changed. Swapping to a different
OpenAI-compatible provider later is a config change, not a code change,
via GEMINI_BASE_URL/GEMINI_API_KEY/GEMINI_MODEL.

Why not the native `google-genai` SDK? It isn't currently an installed
project dependency, and the symptom this module was hardened for --
Gemini returning HTTP 503 "model overloaded", sometimes with client-side
timeouts -- is a well-documented, expected *transient* condition across
BOTH the native SDK and the OpenAI-compatible endpoint alike (Google's own
guidance for it is simply "retry with exponential backoff, no more than a
couple of times"). Switching wire formats would not have fixed that; the
actual bug was that this module made exactly one attempt per request with
no retry logic at all, so any transient overload was surfaced straight to
the user. That is what this version fixes. If a future need for
native-SDK-only features (e.g. streaming, function calling with Gemini's
native schema) arises, `google-genai` can be added as a dependency and
substituted here without changing `LLMProvider`, `ChatMessage`, or
`get_llm_provider()` -- i.e. without touching any other module in the app.

All configuration is environment-driven (see app.core.config.settings) --
no API key is ever hard-coded. If no key is configured, or the provider
call fails/times out after retries, `is_available()`/`chat()` report that
clearly so the assistant endpoint can return the project's normal
structured error instead of crashing -- every non-AI feature in the app is
completely unaffected by the LLM being unavailable.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from app.core.config import settings
from app.core.exceptions import LLMAuthenticationError, LLMRateLimitError, ModelNotAvailableError
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Retryable per Google's own guidance (429 quota, 5xx transient/overload).
# 401/403 (auth) and any other 4xx are NOT retried -- retrying the same
# request with the same bad credential/payload cannot succeed.
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_AUTH_FAILURE_STATUS_CODES = {401, 403}
_MAX_BACKOFF_SECONDS = 8.0


def _sleep(seconds: float) -> None:
    """Isolated as its own function so tests can patch it out and run instantly
    instead of actually sleeping through the retry backoff."""
    time.sleep(seconds)


@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


class LLMProvider:
    """Base interface. A future second provider (e.g. a different vendor) only needs to implement `chat`."""

    def is_available(self) -> bool:
        raise NotImplementedError

    def chat(self, messages: list[ChatMessage]) -> str:
        raise NotImplementedError


class GeminiProvider(LLMProvider):
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.base_url = settings.gemini_base_url.rstrip("/")
        self.model = settings.gemini_model
        self.connect_timeout = settings.gemini_connect_timeout_seconds
        self.read_timeout = settings.gemini_read_timeout_seconds
        self.write_timeout = settings.gemini_write_timeout_seconds
        self.pool_timeout = settings.gemini_pool_timeout_seconds
        self.max_retries = settings.gemini_max_retries
        self.retry_base_delay_seconds = settings.gemini_retry_base_delay_seconds

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _backoff_delay(self, attempt_number: int) -> float:
        """attempt_number is 1-based (delay before the 2nd, 3rd, ... attempt)."""
        return min(self.retry_base_delay_seconds * (2 ** (attempt_number - 1)), _MAX_BACKOFF_SECONDS)

    def chat(self, messages: list[ChatMessage]) -> str:
        if not self.is_available():
            # Fails fast, before any network call -- a missing key is a
            # configuration problem, never a transient one, so there is
            # nothing to retry.
            raise LLMAuthenticationError(
                "The AI Career Assistant is not configured in this environment (no Gemini API key set)."
            )

        try:
            import httpx
        except ImportError as e:
            logger.error("httpx unavailable for LLM provider call: %s", e)
            raise ModelNotAvailableError("The AI Career Assistant's HTTP client could not be loaded in this environment.") from e

        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": 0.2,  # low temperature -- this assistant explains grounded data, not creative writing
        }
        # Never log this dict -- it carries the API key. Every log line
        # below logs only provider/model/status/latency/attempt/sanitized
        # error type, never headers or the key itself.
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        timeout = httpx.Timeout(connect=self.connect_timeout, read=self.read_timeout, write=self.write_timeout, pool=self.pool_timeout)

        max_attempts = self.max_retries + 1
        last_error_summary = "unknown error"

        for attempt in range(1, max_attempts + 1):
            start = time.perf_counter()
            try:
                with httpx.Client(timeout=timeout) as client:
                    response = client.post(f"{self.base_url}/chat/completions", json=payload, headers=headers)
                latency_ms = (time.perf_counter() - start) * 1000

                if response.status_code in _AUTH_FAILURE_STATUS_CODES:
                    logger.error(
                        "provider=gemini model=%s attempt=%d/%d status=%d latency_ms=%.1f "
                        "auth_failure -- check GEMINI_API_KEY (not retrying)",
                        self.model, attempt, max_attempts, response.status_code, latency_ms,
                    )
                    raise LLMAuthenticationError(
                        "The AI Career Assistant could not authenticate with Gemini. Check GEMINI_API_KEY."
                    )

                if response.status_code in _RETRYABLE_STATUS_CODES:
                    last_error_summary = f"HTTP {response.status_code}"
                    is_last_attempt = attempt == max_attempts
                    logger.warning(
                        "provider=gemini model=%s attempt=%d/%d status=%d latency_ms=%.1f retrying=%s",
                        self.model, attempt, max_attempts, response.status_code, latency_ms, not is_last_attempt,
                    )
                    if not is_last_attempt:
                        _sleep(self._backoff_delay(attempt))
                        continue
                    logger.error(
                        "provider=gemini model=%s exhausted %d attempts, last status=%d",
                        self.model, max_attempts, response.status_code,
                    )
                    if response.status_code == 429:
                        raise LLMRateLimitError()
                    raise ModelNotAvailableError("The AI Career Assistant is currently unavailable. Please try again shortly.")

                if response.status_code >= 400:
                    # Any other 4xx (e.g. 400 bad request) -- not one of our
                    # own retryable/auth cases, and retrying an identical
                    # malformed request cannot succeed. Fail immediately.
                    logger.error(
                        "provider=gemini model=%s attempt=%d/%d status=%d (not retrying)",
                        self.model, attempt, max_attempts, response.status_code,
                    )
                    raise ModelNotAvailableError("The AI Career Assistant is currently unavailable.")

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                logger.info(
                    "provider=gemini model=%s attempt=%d/%d status=%d latency_ms=%.1f retries=%d",
                    self.model, attempt, max_attempts, response.status_code, latency_ms, attempt - 1,
                )
                return content

            except httpx.TimeoutException as e:
                latency_ms = (time.perf_counter() - start) * 1000
                last_error_summary = "timeout"
                is_last_attempt = attempt == max_attempts
                logger.warning(
                    "provider=gemini model=%s attempt=%d/%d status=timeout latency_ms=%.1f retrying=%s",
                    self.model, attempt, max_attempts, latency_ms, not is_last_attempt,
                )
                if not is_last_attempt:
                    _sleep(self._backoff_delay(attempt))
                    continue
                logger.error("provider=gemini model=%s exhausted %d attempts, last error=timeout", self.model, max_attempts)
                raise ModelNotAvailableError("The AI Career Assistant timed out. Please try again.") from e

            except (LLMAuthenticationError, LLMRateLimitError, ModelNotAvailableError):
                raise  # already the correct, final, structured exception -- don't reclassify it below

            except (KeyError, IndexError, ValueError) as e:
                # Malformed/unexpected response body (missing choices/message/content,
                # or invalid JSON). Not retried -- a malformed response from a
                # successful HTTP round-trip is not the transient-overload case
                # retries are meant for, and retrying an already-odd response
                # doesn't reliably help.
                logger.error(
                    "provider=gemini model=%s attempt=%d/%d malformed_response error=%s (not retrying)",
                    self.model, attempt, max_attempts, type(e).__name__,
                )
                raise ModelNotAvailableError("The AI Career Assistant is currently unavailable.") from e

            except httpx.HTTPError as e:
                # Network/connection-level failures (DNS, connection refused, etc.)
                # -- transient by nature, so retried the same as 5xx/429.
                latency_ms = (time.perf_counter() - start) * 1000
                last_error_summary = type(e).__name__
                is_last_attempt = attempt == max_attempts
                logger.warning(
                    "provider=gemini model=%s attempt=%d/%d network_error=%s latency_ms=%.1f retrying=%s",
                    self.model, attempt, max_attempts, type(e).__name__, latency_ms, not is_last_attempt,
                )
                if not is_last_attempt:
                    _sleep(self._backoff_delay(attempt))
                    continue
                logger.error(
                    "provider=gemini model=%s exhausted %d attempts, last error=%s",
                    self.model, max_attempts, type(e).__name__,
                )
                raise ModelNotAvailableError("The AI Career Assistant is currently unavailable.") from e

        # Defensive only -- the loop above always returns or raises.
        raise ModelNotAvailableError(f"The AI Career Assistant is currently unavailable ({last_error_summary}).")


_provider: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    """Singleton accessor -- avoids re-reading config/constructing a client per request."""
    global _provider
    if _provider is None:
        _provider = GeminiProvider()
    return _provider
