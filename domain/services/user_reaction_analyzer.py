from domain.value_objects.reaction_text import ReactionText
from domain.services.llm_analyzer_protocol import LlmAnalyzerProtocol
from domain.value_objects.dialogue_policies import (
    UserReactionAnalysisResult,
    UserReactionIntent,
    EmotionTone
)

class UserReactionAnalyzer:
    """ユーザーが投稿した reaction_text を解析し、意図と感情トーンを分類する"""
    
    def __init__(self, analyzer_client: LlmAnalyzerProtocol):
        self._analyzer_client = analyzer_client

    def analyze(self, reaction_text: ReactionText) -> UserReactionAnalysisResult:
        raw_result = self._analyzer_client.analyze_reaction(reaction_text.text)
        
        intent = self._map_to_intent(raw_result.get("intent", ""))
        tone = self._map_to_tone(raw_result.get("tone", ""))
        
        return UserReactionAnalysisResult(intent=intent, tone=tone)

    def _map_to_intent(self, raw_intent: str) -> UserReactionIntent:
        mapping = {
            "technical_question": UserReactionIntent.TECHNICAL_QUESTION,
            "empathy": UserReactionIntent.EMPATHY,
            "concern": UserReactionIntent.CONCERN,
            "observation": UserReactionIntent.OBSERVATION,
        }
        return mapping.get(raw_intent.lower(), UserReactionIntent.OTHER)

    def _map_to_tone(self, raw_tone: str) -> EmotionTone:
        mapping = {
            "positive": EmotionTone.POSITIVE,
            "negative": EmotionTone.NEGATIVE,
            "confused": EmotionTone.CONFUSED,
        }
        return mapping.get(raw_tone.lower(), EmotionTone.NEUTRAL)
