# 仕様: docs/spec/domain.md#lecture（集約ルート）
from dataclasses import dataclass, field

from domain.entities.entity import Entity
from domain.entities.utterance import Utterance
from domain.value_objects.ai_persona_profile import AiPersonaProfile


@dataclass(kw_only=True)
class Lecture(Entity):
    title: str
    started_at: int
    ended_at: int
    persona_profiles: list[AiPersonaProfile]
    utterances: list[Utterance] = field(default_factory=list)

    def add_utterance(self, utterance: Utterance) -> None:
        self.utterances.append(utterance)
        if utterance.time_range.end_ms > self.ended_at:
            self.ended_at = utterance.time_range.end_ms
