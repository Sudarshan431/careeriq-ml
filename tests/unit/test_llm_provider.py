import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import types
import unittest
from unittest.mock import patch

from app.ai.llm_provider import GeminiProvider, ChatMessage
from app.core.exceptions import LLMAuthenticationError, LLMRateLimitError, ModelNotAvailableError


class TestGeminiProviderUnavailable(unittest.TestCase):
    def test_unavailable_without_api_key(self):
        provider = GeminiProvider()
        provider.api_key = ""
        self.assertFalse(provider.is_available())

    def test_chat_raises_authentication_error_without_api_key(self):
        # Missing key must NOT be reported as the generic "model unavailable" --
        # it's a distinct, non-transient configuration problem.
        provider = GeminiProvider()
        provider.api_key = ""
        with self.assertRaises(LLMAuthenticationError) as ctx:
            provider.chat([ChatMessage(role="user", content="hi")])
        self.assertEqual(ctx.exception.code, "LLM_AUTHENTICATION_ERROR")

    def test_error_message_mentions_gemini_not_generic_llm(self):
        provider = GeminiProvider()
        provider.api_key = ""
        with self.assertRaises(LLMAuthenticationError) as ctx:
            provider.chat([ChatMessage(role="user", content="hi")])
        self.assertIn("Gemini", ctx.exception.message)

    def test_available_with_api_key_configured(self):
        provider = GeminiProvider()
        provider.api_key = "fake-key-for-test"
        self.assertTrue(provider.is_available())

    def test_default_base_url_points_at_gemini(self):
        provider = GeminiProvider()
        self.assertIn("generativelanguage.googleapis.com", provider.base_url)

    def test_no_openai_dependency_referenced(self):
        import app.ai.llm_provider as module
        source = Path(module.__file__).read_text()
        self.assertNotIn("import openai", source)
        self.assertNotIn("from openai", source)

    def test_default_read_timeout_raised_above_20s(self):
        # The original bug report included plain timeouts at the old 20s
        # ceiling; the fix raises the default read timeout.
        provider = GeminiProvider()
        self.assertGreater(provider.read_timeout, 20.0)

    def test_retries_are_small_and_bounded(self):
        provider = GeminiProvider()
        self.assertGreaterEqual(provider.max_retries, 1)
        self.assertLessEqual(provider.max_retries, 5)  # "small bounded number", never unbounded


def _install_fake_httpx():
    """
    Installs a minimal fake `httpx` module into sys.modules so GeminiProvider.chat()'s
    lazy `import httpx` picks it up -- lets us exercise the full request/response/error
    handling matrix (including multi-call retry sequences) without the real httpx
    package (not installed in this environment) and without a real network call.
    """

    class FakeHTTPError(Exception):
        pass

    class FakeTimeoutException(FakeHTTPError):
        pass

    class FakeHTTPStatusError(FakeHTTPError):
        response = None

    class FakeResponse:
        def __init__(self, status_code=200, json_body=None):
            self.status_code = status_code
            self._json_body = json_body if json_body is not None else {}

        def raise_for_status(self):
            if self.status_code >= 400:
                error = FakeHTTPStatusError(f"HTTP {self.status_code}")
                error.response = self
                raise error

        def json(self):
            return self._json_body

    class FakeClient:
        _next_responses = []  # class-level queue consumed in order across successive .post() calls

        def __init__(self, timeout=None):
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, json=None, headers=None):
            behavior = FakeClient._next_responses.pop(0)
            if isinstance(behavior, Exception):
                raise behavior
            return behavior

    fake_httpx = types.ModuleType("httpx")
    fake_httpx.Client = FakeClient
    fake_httpx.HTTPError = FakeHTTPError
    fake_httpx.TimeoutException = FakeTimeoutException
    fake_httpx.HTTPStatusError = FakeHTTPStatusError
    fake_httpx.Timeout = lambda **kwargs: kwargs
    sys.modules["httpx"] = fake_httpx
    return fake_httpx, FakeResponse, FakeTimeoutException


class TestGeminiProviderMockedHTTP(unittest.TestCase):
    """Covers the 7 scenarios required for the retry/backoff/error-differentiation fix."""

    def setUp(self):
        self._real_httpx = sys.modules.get("httpx")
        self.fake_httpx, self.FakeResponse, self.FakeTimeoutException = _install_fake_httpx()
        # Patch _sleep so retry-backoff tests run instantly instead of actually waiting.
        self._sleep_patcher = patch("app.ai.llm_provider._sleep")
        self.mock_sleep = self._sleep_patcher.start()

    def tearDown(self):
        self._sleep_patcher.stop()
        if self._real_httpx is not None:
            sys.modules["httpx"] = self._real_httpx
        else:
            sys.modules.pop("httpx", None)

    def _provider(self):
        provider = GeminiProvider()
        provider.api_key = "fake-key-for-test"
        return provider

    def _queue(self, *behaviors):
        self.fake_httpx.Client._next_responses = list(behaviors)

    # 1. successful Gemini response
    def test_successful_response(self):
        self._queue(self.FakeResponse(200, {"choices": [{"message": {"content": "Here is your answer."}}]}))
        result = self._provider().chat([ChatMessage(role="user", content="hi")])
        self.assertEqual(result, "Here is your answer.")
        self.mock_sleep.assert_not_called()

    # 2. 503 followed by successful retry
    def test_503_then_success_retries_and_succeeds(self):
        self._queue(
            self.FakeResponse(503, {}),
            self.FakeResponse(200, {"choices": [{"message": {"content": "Recovered."}}]}),
        )
        result = self._provider().chat([ChatMessage(role="user", content="hi")])
        self.assertEqual(result, "Recovered.")
        self.mock_sleep.assert_called_once()  # exactly one backoff wait before the successful retry

    # 3. repeated 503 (exhausts retries)
    def test_repeated_503_exhausts_retries_and_raises_model_unavailable(self):
        provider = self._provider()
        max_attempts = provider.max_retries + 1
        self._queue(*[self.FakeResponse(503, {}) for _ in range(max_attempts)])
        with self.assertRaises(ModelNotAvailableError):
            provider.chat([ChatMessage(role="user", content="hi")])
        self.assertEqual(self.mock_sleep.call_count, max_attempts - 1)  # backoff between attempts, not after the last one

    # 4. timeout
    def test_timeout_retries_then_raises_model_unavailable(self):
        provider = self._provider()
        max_attempts = provider.max_retries + 1
        self._queue(*[self.FakeTimeoutException("timed out") for _ in range(max_attempts)])
        with self.assertRaises(ModelNotAvailableError) as ctx:
            provider.chat([ChatMessage(role="user", content="hi")])
        self.assertIn("timed out", ctx.exception.message.lower())

    # 5. 429 rate limit
    def test_repeated_429_raises_distinct_rate_limit_error(self):
        provider = self._provider()
        max_attempts = provider.max_retries + 1
        self._queue(*[self.FakeResponse(429, {}) for _ in range(max_attempts)])
        with self.assertRaises(LLMRateLimitError) as ctx:
            provider.chat([ChatMessage(role="user", content="hi")])
        self.assertEqual(ctx.exception.code, "LLM_RATE_LIMITED")
        self.assertEqual(ctx.exception.status_code, 429)

    # 6. invalid API key / 401 or 403 -- must NOT retry and must NOT be the generic error
    def test_401_raises_authentication_error_without_retrying(self):
        self._queue(self.FakeResponse(401, {}))  # only one queued -- a retry would raise IndexError and fail the test
        provider = self._provider()
        with self.assertRaises(LLMAuthenticationError) as ctx:
            provider.chat([ChatMessage(role="user", content="hi")])
        self.assertEqual(ctx.exception.code, "LLM_AUTHENTICATION_ERROR")
        self.mock_sleep.assert_not_called()

    def test_403_raises_authentication_error_without_retrying(self):
        self._queue(self.FakeResponse(403, {}))
        provider = self._provider()
        with self.assertRaises(LLMAuthenticationError):
            provider.chat([ChatMessage(role="user", content="hi")])
        self.mock_sleep.assert_not_called()

    # 7. malformed provider response -- must NOT retry
    def test_malformed_response_raises_model_unavailable_without_retrying(self):
        self._queue(self.FakeResponse(200, {"unexpected": "shape"}))  # missing "choices"
        provider = self._provider()
        with self.assertRaises(ModelNotAvailableError):
            provider.chat([ChatMessage(role="user", content="hi")])
        self.mock_sleep.assert_not_called()

    # Extra: security -- API key never appears in any raised error message
    def test_api_key_never_appears_in_raised_error_message(self):
        self._queue(self.FakeResponse(401, {}))
        provider = self._provider()
        with self.assertRaises(LLMAuthenticationError) as ctx:
            provider.chat([ChatMessage(role="user", content="hi")])
        self.assertNotIn("fake-key-for-test", ctx.exception.message)

    # Extra: a non-retryable 4xx (e.g. 400) fails immediately, not retried
    def test_400_bad_request_not_retried(self):
        self._queue(self.FakeResponse(400, {}))
        provider = self._provider()
        with self.assertRaises(ModelNotAvailableError):
            provider.chat([ChatMessage(role="user", content="hi")])
        self.mock_sleep.assert_not_called()

    # Extra: backoff delay grows between attempts (exponential, capped)
    def test_backoff_delay_is_exponential(self):
        provider = self._provider()
        first = provider._backoff_delay(1)
        second = provider._backoff_delay(2)
        third = provider._backoff_delay(3)
        self.assertLess(first, second)
        self.assertLessEqual(second, third)  # capped, so may plateau but never decrease


class TestPromptBuilder(unittest.TestCase):
    def test_context_is_embedded_as_data_not_instructions(self):
        from app.ai.prompt_builder import build_messages

        context = {"candidate_skills": ["Java"], "match_score": 80}
        messages = build_messages("What am I missing?", context)
        system_message = messages[0]
        self.assertEqual(system_message.role, "system")
        self.assertIn("Java", system_message.content)
        self.assertIn("80", system_message.content)
        self.assertIn("Only use the facts", system_message.content)

    def test_user_question_is_last_message(self):
        from app.ai.prompt_builder import build_messages

        messages = build_messages("test question", {})
        self.assertEqual(messages[-1].role, "user")
        self.assertEqual(messages[-1].content, "test question")

    def test_conversation_history_included_in_order(self):
        from app.ai.prompt_builder import build_messages

        history = [{"role": "user", "content": "first"}, {"role": "assistant", "content": "reply"}]
        messages = build_messages("second question", {}, conversation_history=history)
        roles_content = [(m.role, m.content) for m in messages]
        self.assertIn(("user", "first"), roles_content)
        self.assertIn(("assistant", "reply"), roles_content)
        self.assertEqual(roles_content[-1], ("user", "second question"))


if __name__ == "__main__":
    unittest.main()
