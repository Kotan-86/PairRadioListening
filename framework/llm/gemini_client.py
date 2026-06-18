# 仕様: docs/spec/framework_llm.md#5.1, docs/spec/framework_llm.md#5.3
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from google import genai
from google.genai import errors as genai_errors

from framework.llm.llm_rate_limiter import LlmRateLimitExceeded, LlmRateLimiter

logger = logging.getLogger(__name__)


@dataclass
class GeminiClient:
    api_key: str
    model: str
    rate_limiter: LlmRateLimiter
    _client: genai.Client = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._client = genai.Client(api_key=self.api_key)

    def generate_text(self, prompt: str) -> str:
        try:
            self.rate_limiter.acquire()
        except LlmRateLimitExceeded as exc:
            raise RuntimeError(str(exc)) from exc

        last_error: Exception | None = None
        for attempt in range(2):
            try:
                response = self._client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                )
                return _extract_text(response)
            except genai_errors.ClientError as exc:
                last_error = exc
                if attempt == 0 and _is_rate_limited(exc):
                    logger.warning("Gemini 429 received; backing off once")
                    time.sleep(1.0)
                    continue
                raise RuntimeError(f"Gemini API error: {exc}") from exc
            except Exception as exc:
                raise RuntimeError(f"Gemini API error: {exc}") from exc

        raise RuntimeError(f"Gemini API error: {last_error}")


def _extract_text(response: Any) -> str:
    text = getattr(response, "text", None)
    if text:
        return str(text).strip()
    raise RuntimeError("Gemini response contained no text")


def _is_rate_limited(exc: genai_errors.ClientError) -> bool:
    return getattr(exc, "code", None) == 429
