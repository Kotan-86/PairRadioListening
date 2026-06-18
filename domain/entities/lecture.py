# 仕様: docs/spec/domain.md#lecture（集約ルート）
from dataclasses import dataclass, field
from typing import Literal

from domain.entities.entity import Entity, EntityId
from domain.entities.utterance import Utterance
from domain.value_objects.ai_persona_profile import AiPersonaProfile
from domain.value_objects.time_range import TimeRange

LectureStatus = Literal["active", "closed"]


@dataclass(kw_only=True)
class Lecture(Entity):
    title: str
    started_at: int | None = None
    ended_at: int = 0
    status: LectureStatus = "active"
    persona_profiles: list[AiPersonaProfile]
    next_dialogue_sequence: int = 0
    utterances: list[Utterance] = field(default_factory=list)

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.status not in ("active", "closed"):
            raise ValueError("lecture.status は active または closed のみです")
        if len(self.persona_profiles) != 1:
            raise ValueError(
                "lecture.persona_profiles は MVP ではちょうど 1 件である必要があります"
            )

    def add_utterance(self, utterance: Utterance) -> None:
        if self.status == "closed":
            raise ValueError("closed の lecture に utterance を追加できません")
        if self.started_at is None:
            self.started_at = 0
        self.utterances.append(utterance)
        self._refresh_ended_at()

    def upsert_utterance(self, utterance: Utterance) -> None:
        if self.status == "closed":
            raise ValueError("closed の lecture に utterance を追加できません")
        for index, existing in enumerate(self.utterances):
            if str(existing.id) == str(utterance.id):
                if self.started_at is None:
                    self.started_at = 0
                self.utterances[index] = utterance
                self._refresh_ended_at()
                return
        self.add_utterance(utterance)

    def allocate_dialogue_sequence(self) -> int:
        if self.status == "closed":
            raise ValueError("closed の lecture では dialogue_sequence を採番できません")
        current = self.next_dialogue_sequence
        self.next_dialogue_sequence += 1
        return current

    def latest_utterance(self) -> Utterance | None:
        if not self.utterances:
            return None
        return max(self.utterances, key=lambda u: u.time_range.start_ms)

    def find_utterance_by_id(self, utterance_id: EntityId) -> Utterance | None:
        for utterance in self.utterances:
            if str(utterance.id) == str(utterance_id):
                return utterance
        return None

    @staticmethod
    def normalize_time_range_for_first_utterance(time_range: TimeRange) -> TimeRange:
        offset = time_range.start_ms
        return TimeRange(start_ms=0, end_ms=time_range.end_ms - offset)

    def _refresh_ended_at(self) -> None:
        if self.utterances:
            self.ended_at = max(u.time_range.end_ms for u in self.utterances)
        else:
            self.ended_at = 0

    def close(self) -> None:
        if self.status == "closed":
            raise ValueError("lecture は既に closed です")
        self.status = "closed"
        if self.utterances:
            self.ended_at = max(u.time_range.end_ms for u in self.utterances)
        else:
            self.ended_at = 0
