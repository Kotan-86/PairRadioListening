# 仕様: docs/spec/framework_llm.md#6.1
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from domain.value_objects.lecture_llm_context import LectureLlmContext
from domain.value_objects.reply_target_focus import ReplyTargetFocus
from framework.llm.gemini_client import GeminiClient
from framework.llm.prompt_builder import build_user_reaction_policy_prompt


@dataclass(frozen=True, slots=True)
class GeminiLlmAnalyzerDriver:
    _client: GeminiClient

    def analyze_reaction(self, text: str) -> dict:
        _ = text
        return {"intent": "observation", "tone": "neutral"}

    def generate_reaction_policy(self, utterance_text: str, persona_prompt: str) -> dict:
        _ = utterance_text, persona_prompt
        return {"summary_angle": "要約", "personalization_angle": "例え"}

    def generate_response_policy(
        self,
        reaction_text: str,
        persona_prompt: str,
        reply_target_kind: str,
        lecture_llm_context: LectureLlmContext,
        reply_target_focus: ReplyTargetFocus,
    ) -> dict:
        _ = reply_target_kind
        prompt = build_user_reaction_policy_prompt(
            persona_prompt=persona_prompt,
            reaction_text=reaction_text,
            lecture_llm_context=lecture_llm_context,
            reply_target_focus=reply_target_focus,
        )
        raw = self._client.generate_text(prompt)
        return _parse_policy_json(raw)


def _parse_policy_json(raw: str) -> dict:
    cleaned = raw.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if fence:
        cleaned = fence.group(1)
    else:
        brace = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if brace:
            cleaned = brace.group(0)
    data = json.loads(cleaned)
    if not isinstance(data, dict):
        raise ValueError("policy JSON must be an object")
    return data
