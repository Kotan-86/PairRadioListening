# 仕様: docs/spec/framework_llm.md#5.1 — Phase3 統合テスト用
from __future__ import annotations

from dataclasses import dataclass, field

from domain.value_objects.lecture_llm_context import LectureLlmContext
from domain.value_objects.reply_target_focus import ReplyTargetFocus


@dataclass
class FakeLlmAnalyzer:
    policy_delay_s: float = 0.0
    calls: list[dict] = field(default_factory=list)

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
        if self.policy_delay_s:
            import time

            time.sleep(self.policy_delay_s)
        self.calls.append(
            {
                "reaction_text": reaction_text,
                "persona_prompt": persona_prompt,
                "reply_target_kind": reply_target_kind,
                "lecture_llm_context": lecture_llm_context,
                "reply_target_focus": reply_target_focus,
            }
        )
        return {
            "tone": "共感的",
            "response_intent": "壁打ち",
            "reference_facts": ["fake"],
        }
