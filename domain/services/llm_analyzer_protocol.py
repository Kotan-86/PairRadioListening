from typing import Protocol

from domain.value_objects.lecture_llm_context import LectureLlmContext
from domain.value_objects.reply_target_focus import ReplyTargetFocus


class LlmAnalyzerProtocol(Protocol):

    def analyze_reaction(self, text: str) -> dict:
        ...

    def generate_reaction_policy(self, utterance_text: str, persona_prompt: str) -> dict:
        ...

    def generate_response_policy(
        self,
        reaction_text: str,
        persona_prompt: str,
        reply_target_kind: str,
        lecture_llm_context: LectureLlmContext,
        reply_target_focus: ReplyTargetFocus,
    ) -> dict:
        ...
