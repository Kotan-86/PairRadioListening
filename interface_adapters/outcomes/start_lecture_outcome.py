# 仕様: docs/spec/interface.md#start_lecture_controller
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StartLectureOutcome:
    success: bool
    lecture_id: str = ""
    error_kind: str = ""
