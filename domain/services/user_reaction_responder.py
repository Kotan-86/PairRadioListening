from typing import Optional
from domain.entities.reaction import Reaction
from domain.value_objects.ai_persona_profile import AiPersonaProfile
from domain.services.llm_analyzer_protocol import LlmAnalyzerProtocol
from domain.value_objects.dialogue_policies import (
    UserReactionAnalysisResult,
    AtmosphereLevel,
    UserReactionResponsePolicy
)

class UserReactionResponder:

    def __init__(self, analyzer_client: LlmAnalyzerProtocol):
        self._analyzer_client = analyzer_client

    def determine_policies(
        self,
        reaction: Reaction,
        analysis_result: UserReactionAnalysisResult,
        personas: list[AiPersonaProfile],
        atmosphere: Optional[AtmosphereLevel] = None
    ) -> list[UserReactionResponsePolicy]:
        policies = []
        
        analysis_data = self._prepare_analysis_data(analysis_result)
        
        for persona in personas:
            policy = self._determine_policy_for_persona(reaction, persona, analysis_data)
            policies.append(policy)
            
        return policies

    def _prepare_analysis_data(self, analysis_result: UserReactionAnalysisResult) -> dict:
        return {
            "intent": analysis_result.intent.name,
            "tone": analysis_result.tone.name
        }

    def _determine_policy_for_persona(
        self, 
        reaction: Reaction, 
        persona: AiPersonaProfile, 
        analysis_data: dict
    ) -> UserReactionResponsePolicy:
        
        raw_policy = self._analyzer_client.generate_response_policy(
            reaction_text=reaction.reaction_text.text,
            persona_prompt=persona.persona_prompt,
            analysis=analysis_data
        )
        
        return UserReactionResponsePolicy(
            persona_id=persona.id,
            tone=raw_policy.get("tone", "ニュートラル"),
            response_intent=raw_policy.get("response_intent", "相槌を打つ"),
            reference_facts=raw_policy.get("reference_facts", [])
        )
