from typing import Optional
from domain.entities.utterance import Utterance
from domain.value_objects.ai_persona_profile import AiPersonaProfile
from domain.services.llm_analyzer_protocol import LlmAnalyzerProtocol
from domain.value_objects.dialogue_policies import (
    AtmosphereLevel,
    LecturerReactionPolicy
)

class LecturerReactionGenerator:

    def __init__(self, analyzer_client: LlmAnalyzerProtocol):
        self._analyzer_client = analyzer_client

    def generate_policies(
        self,
        utterance: Utterance,
        personas: list[AiPersonaProfile],
        atmosphere: Optional[AtmosphereLevel] = None
    ) -> list[LecturerReactionPolicy]:
        policies = []
        
        for persona in personas:
            policy = self._generate_policy_for_persona(utterance, persona, atmosphere)
            policies.append(policy)
            
        return policies

    def _generate_policy_for_persona(
        self, 
        utterance: Utterance, 
        persona: AiPersonaProfile, 
        atmosphere: Optional[AtmosphereLevel]
    ) -> LecturerReactionPolicy:
        raw_policy = self._analyzer_client.generate_reaction_policy(
            utterance_text=utterance.speech_text.text,
            persona_prompt=persona.persona_prompt
        )
        
        return LecturerReactionPolicy(
            persona_id=persona.id,
            summary_angle=raw_policy.get("summary_angle", "事実の単純要約"),
            personalization_angle=raw_policy.get("personalization_angle", "一般的な例え")
        )
