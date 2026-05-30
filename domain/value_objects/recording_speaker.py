# 仕様: docs/spec/domain.md#speaker（講義記録側）
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class RecordingSpeaker:
    display_name: str
    role: Literal["lecturer"] = "lecturer"

    def __post_init__(self) -> None:
        if self.role != "lecturer":
            raise ValueError("recording_speaker の role は lecturer のみです")
        if not self.display_name.strip():
            raise ValueError("recording_speaker の display_name は空にできません")
