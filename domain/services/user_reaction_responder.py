# 仕様: docs/spec/domain.md#user_reaction_responder
from domain.entities.reaction import Reaction
from domain.value_objects.ai_persona_profile import AiPersonaProfile
from domain.services.llm_analyzer_protocol import LlmAnalyzerProtocol
from domain.value_objects.dialogue_policies import UserReactionResponsePolicy


class UserReactionResponder:

    def __init__(self, analyzer_client: LlmAnalyzerProtocol):
        self._analyzer_client = analyzer_client

    def determine_policy(
        self,
        reaction: Reaction,
        persona: AiPersonaProfile,
    ) -> UserReactionResponsePolicy:
        raw_policy = self._analyzer_client.generate_response_policy(
            reaction_text=reaction.reaction_text.text,
            persona_prompt=persona.persona_prompt,
            reply_target_kind=reaction.reply_target.reply_target_kind,
        )

        return UserReactionResponsePolicy(
            persona_id=persona.id,
            tone=raw_policy.get("tone", "ニュートラル"),
            response_intent=raw_policy.get("response_intent", "相槌を打つ"),
            reference_facts=raw_policy.get("reference_facts", []),
        )
