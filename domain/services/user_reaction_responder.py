# 仕様: docs/spec/domain.md#user_reaction_responder
from domain.entities.reaction import Reaction
from domain.value_objects.ai_persona_profile import AiPersonaProfile
from domain.services.llm_analyzer_protocol import LlmAnalyzerProtocol
from domain.value_objects.dialogue_policies import UserReactionResponsePolicy
from domain.value_objects.lecture_llm_context import LectureLlmContext
from domain.value_objects.reply_target_focus import ReplyTargetFocus


class UserReactionResponder:

    def __init__(self, analyzer_client: LlmAnalyzerProtocol):
        self._analyzer_client = analyzer_client

    def determine_policy(
        self,
        reaction: Reaction,
        persona: AiPersonaProfile,
        lecture_llm_context: LectureLlmContext,
        reply_target_focus: ReplyTargetFocus,
    ) -> UserReactionResponsePolicy:
        raw_policy = self._analyzer_client.generate_response_policy(
            reaction_text=reaction.reaction_text.text,
            persona_prompt=persona.persona_prompt,
            reply_target_kind=reaction.reply_target.reply_target_kind,
            lecture_llm_context=lecture_llm_context,
            reply_target_focus=reply_target_focus,
        )

        return UserReactionResponsePolicy(
            persona_id=persona.id,
            tone=raw_policy.get("tone", "ニュートラル"),
            response_intent=raw_policy.get("response_intent", "相槌を打つ"),
            reference_facts=raw_policy.get("reference_facts", []),
        )
