# 仕様: docs/spec/domain.md#lecturer_reaction_generator
from domain.entities.utterance import Utterance
from domain.value_objects.ai_persona_profile import AiPersonaProfile
from domain.services.llm_analyzer_protocol import LlmAnalyzerProtocol
from domain.value_objects.dialogue_policies import LecturerReactionPolicy


class LecturerReactionGenerator:

    def __init__(self, analyzer_client: LlmAnalyzerProtocol):
        self._analyzer_client = analyzer_client

    def generate_policy(
        self,
        utterance: Utterance,
        persona: AiPersonaProfile,
    ) -> LecturerReactionPolicy:
        raw_policy = self._analyzer_client.generate_reaction_policy(
            utterance_text=utterance.speech_text.text,
            persona_prompt=persona.persona_prompt,
        )

        return LecturerReactionPolicy(
            persona_id=persona.id,
            summary_angle=raw_policy.get("summary_angle", "事実の単純要約"),
            personalization_angle=raw_policy.get("personalization_angle", "一般的な例え"),
        )
