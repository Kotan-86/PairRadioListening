from typing import Protocol

class LlmAnalyzerProtocol(Protocol):
    
    def analyze_reaction(self, text: str) -> dict:
        ...

    def generate_reaction_policy(self, utterance_text: str, persona_prompt: str) -> dict:
        ...

    def generate_response_policy(self, reaction_text: str, persona_prompt: str, analysis: dict) -> dict:
        ...
