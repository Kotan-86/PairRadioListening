# 仕様: docs/spec/interface.md#end_lecture_controller
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EndLectureSessionEvent:
    lecture_id: str
