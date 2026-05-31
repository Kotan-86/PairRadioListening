# 仕様: docs/spec/application.md#generate_ai_reactions_for_utterance
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GenerateAiReactionsForUtteranceResponse:
    lecture_id: str
    utterance_id: str
    reaction_ids: tuple[str, ...]
