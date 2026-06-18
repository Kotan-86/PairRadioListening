# 仕様: docs/spec/application.md#start_lecture
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StartLectureResponse:
    lecture_id: str
