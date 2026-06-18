# 仕様: docs/spec/framework_llm.md#6.2
from __future__ import annotations

from dataclasses import dataclass

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
from framework.llm.gemini_client import GeminiClient
from framework.llm.prompt_builder import build_user_reaction_text_prompt


@dataclass(frozen=True, slots=True)
class GeminiReactionTextGenerator:
    _client: GeminiClient

    def generate_for_lecturer_reaction(
        self,
        policy: LecturerReactionPolicy,
        utterance: Utterance,
        persona: AiPersonaProfile,
    ) -> Result[str, ReactionTextPortError]:
        _ = policy, utterance
        return Err(
            ReactionTextPortError(
                persona_id=str(persona.id),
                reason="lecturer reaction generation is out of MVP scope",
            )
        )

    def generate_for_user_reaction_reply(
        self,
        policy: UserReactionResponsePolicy,
        reaction: Reaction,
        persona: AiPersonaProfile,
        lecture_llm_context: LectureLlmContext,
        reply_target_focus: ReplyTargetFocus,
    ) -> Result[str, ReactionTextPortError]:
        try:
            prompt = build_user_reaction_text_prompt(
                persona=persona,
                policy=policy,
                reaction=reaction,
                lecture_llm_context=lecture_llm_context,
                reply_target_focus=reply_target_focus,
            )
            text = self._client.generate_text(prompt)
            return Ok(text)
        except Exception as exc:
            return Err(
                ReactionTextPortError(
                    persona_id=str(persona.id),
                    reason=str(exc),
                )
            )
