# 仕様: docs/spec/interface.md#end_lecture_controller
from collections.abc import Callable
from dataclasses import dataclass

from application.dtos.end_lecture_request import EndLectureRequest
from application.dtos.end_lecture_response import EndLectureResponse
from application.errors import InvalidRequest
from application.errors.use_case_errors import EndLectureError
from application.result import Result
from interface_adapters.events.end_lecture_session_event import EndLectureSessionEvent
from interface_adapters.outcomes.end_lecture_outcome import EndLectureOutcome
from interface_adapters.presentation.error_kind import error_kind_for

_USE_CASE = "end_lecture"


@dataclass(frozen=True, slots=True)
class EndLectureController:
    _use_case: Callable[[EndLectureRequest], Result[EndLectureResponse, EndLectureError]]

    def execute(self, event: EndLectureSessionEvent) -> EndLectureOutcome:
        if not event.lecture_id.strip():
            return EndLectureOutcome(
                success=False,
                error_kind=error_kind_for(
                    InvalidRequest(
                        use_case=_USE_CASE,
                        field="lecture_id",
                        reason="lecture_id is required",
                    )
                ),
            )

        result = self._use_case(EndLectureRequest(lecture_id=event.lecture_id))
        if result.is_err():
            return EndLectureOutcome(
                success=False,
                error_kind=error_kind_for(result.error),
            )
        response = result.value
        return EndLectureOutcome(
            success=True,
            lecture_id=response.lecture_id,
            ended_at=response.ended_at,
        )
