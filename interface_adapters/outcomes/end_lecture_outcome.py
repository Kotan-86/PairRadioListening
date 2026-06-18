# 仕様: docs/spec/interface.md#end_lecture_controller
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EndLectureOutcome:
    success: bool
    lecture_id: str = ""
    ended_at: int = 0
    error_kind: str = ""
