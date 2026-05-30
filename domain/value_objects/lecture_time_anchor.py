# 仕様: docs/spec/domain.md#lecture_time_anchor
from dataclasses import dataclass

from domain.entities.entity import EntityId
from domain.value_objects.time_range import TimeRange


@dataclass(frozen=True)
class LectureTimeAnchor:
    time_range: TimeRange
    utterance_id: EntityId | None = None

    def __post_init__(self) -> None:
        if self.utterance_id is None:
            return
        if isinstance(self.utterance_id, str) and not self.utterance_id.strip():
            raise ValueError(
                "lecture_time_anchor の utterance_id を指定する場合は空にできません"
            )

    @classmethod
    def from_time_range(cls, time_range: TimeRange) -> "LectureTimeAnchor":
        return cls(time_range=time_range)

    @classmethod
    def from_utterance(
        cls, utterance_id: EntityId, time_range: TimeRange
    ) -> "LectureTimeAnchor":
        return cls(time_range=time_range, utterance_id=utterance_id)
