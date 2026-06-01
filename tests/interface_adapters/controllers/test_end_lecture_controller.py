# 仕様: docs/spec/interface.md#end_lecture_controller
from application.dtos.end_lecture_response import EndLectureResponse
from application.errors import LectureNotFound
from application.result import Err, Ok
from interface_adapters.controllers.end_lecture_controller import EndLectureController
from interface_adapters.events.end_lecture_session_event import EndLectureSessionEvent
from tests.interface_adapters.conftest import StubUseCase


def test_end_lecture_controller_returns_ended_at_on_success():
    use_case = StubUseCase(
        result=Ok(EndLectureResponse(lecture_id="lecture-1", ended_at=99_000)),
    )
    controller = EndLectureController(_use_case=use_case.execute)

    outcome = controller.execute(EndLectureSessionEvent(lecture_id="lecture-1"))

    assert len(use_case.requests) == 1
    assert outcome.success is True
    assert outcome.lecture_id == "lecture-1"
    assert outcome.ended_at == 99_000


def test_end_lecture_controller_maps_not_found_error():
    use_case = StubUseCase(result=Err(LectureNotFound(lecture_id="missing")))
    controller = EndLectureController(_use_case=use_case.execute)

    outcome = controller.execute(EndLectureSessionEvent(lecture_id="missing"))

    assert outcome.success is False
    assert outcome.error_kind == "lecture_not_found"
