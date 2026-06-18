# 仕様: docs/spec/framework_llm.md#5.2, docs/spec/framework_llm.md#8.3
import pytest
from unittest.mock import MagicMock, patch

from framework.llm.gemini_client import GeminiClient
from framework.llm.llm_rate_limiter import LlmRateLimitExceeded, LlmRateLimiter


@pytest.mark.phase3
def test_rate_limiter_rejects_when_rpm_exceeded():
    limiter = LlmRateLimiter(rpm_limit=2, rpd_limit=100)

    limiter.acquire()
    limiter.acquire()

    with pytest.raises(LlmRateLimitExceeded):
        limiter.acquire()


@pytest.mark.phase3
def test_rate_limiter_rejects_when_rpd_exceeded():
    limiter = LlmRateLimiter(rpm_limit=100, rpd_limit=1)

    limiter.acquire()

    with pytest.raises(LlmRateLimitExceeded):
        limiter.acquire()


@pytest.mark.phase3
def test_gemini_client_checks_rate_limiter_before_call():
    limiter = MagicMock()
    limiter.acquire.side_effect = LlmRateLimitExceeded("RPM limit exceeded")
    client = GeminiClient(api_key="test-key", model="gemini-test", rate_limiter=limiter)
    mock_models = MagicMock()
    client._client = MagicMock(models=mock_models)

    with pytest.raises(RuntimeError, match="RPM limit exceeded"):
        client.generate_text("hello")

    mock_models.generate_content.assert_not_called()


@pytest.mark.phase3
@patch("framework.llm.gemini_client.time.sleep", return_value=None)
def test_gemini_client_retries_once_on_429(mock_sleep):
    from google.genai import errors as genai_errors

    limiter = LlmRateLimiter(rpm_limit=10, rpd_limit=100)
    client = GeminiClient(api_key="test-key", model="gemini-test", rate_limiter=limiter)

    response = MagicMock()
    response.text = "ok"
    error_429 = genai_errors.ClientError(429, {"error": "rate limit"})
    client._client.models.generate_content = MagicMock(
        side_effect=[error_429, response]
    )

    assert client.generate_text("prompt") == "ok"
    assert client._client.models.generate_content.call_count == 2
    mock_sleep.assert_called_once()
