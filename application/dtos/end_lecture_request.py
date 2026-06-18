# 仕様: docs/spec/application.md#end_lecture
from dataclasses import dataclass

from application.errors import InvalidRequest
from application.result import Err, Ok, Result

_USE_CASE = "end_lecture"


@dataclass(frozen=True, slots=True)
class EndLectureRequest:
    lecture_id: str

    def validate(self) -> Result[None, InvalidRequest]:
        if not self.lecture_id.strip():
            return Err(
                InvalidRequest(
                    use_case=_USE_CASE,
                    field="lecture_id",
                    reason="lecture_id is required",
                )
            )
        return Ok(None)
