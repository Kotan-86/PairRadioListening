# 仕様: docs/spec/framework_llm.md#5.1 — Phase3 統合テスト用
from __future__ import annotations

from dataclasses import dataclass, field

from application.ports.errors import ReactionTextPortError
from application.result import Err, Ok, Result
from domain.entities.reaction import Reaction
from domain.entities.utterance import Utterance
from domain.value_objects.ai_persona_profile import AiPersonaProfile
from domain.value_objects.dialogue_policies import (
    LecturerReactionPolicy,
    UserReactionResponsePolicy,
)
from domain.value_objects.lecture_llm_context import LectureLlmContext
from domain.value_objects.reply_target_focus import ReplyTargetFocus


@dataclass
class FakeReactionTextGenerator:
    text_delay_s: float = 0.0
    reply_text: str = "これは Fake AI の壁打ち返信です。"
    calls: list[dict] = field(default_factory=list)

    def generate_for_lecturer_reaction(
        self,
        policy: LecturerReactionPolicy,
        utterance: Utterance,
        persona: AiPersonaProfile,
    ) -> Result[str, ReactionTextPortError]:
        _ = policy, utterance
        return Ok(f"lecturer fake for {persona.display_name}")

    def generate_for_user_reaction_reply(
        self,
        policy: UserReactionResponsePolicy,
        reaction: Reaction,
        persona: AiPersonaProfile,
        lecture_llm_context: LectureLlmContext,
        reply_target_focus: ReplyTargetFocus,
    ) -> Result[str, ReactionTextPortError]:
        if self.text_delay_s:
            import time

            time.sleep(self.text_delay_s)
        self.calls.append(
            {
                "policy": policy,
                "reaction": reaction,
                "persona": persona,
                "lecture_llm_context": lecture_llm_context,
                "reply_target_focus": reply_target_focus,
            }
        )
        return Ok(self.reply_text)
