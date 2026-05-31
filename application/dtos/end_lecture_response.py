# 仕様: docs/spec/application.md#end_lecture
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EndLectureResponse:
    lecture_id: str
    ended_at: int
