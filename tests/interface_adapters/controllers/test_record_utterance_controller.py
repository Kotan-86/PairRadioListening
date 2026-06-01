# 仕様: docs/spec/interface.md#record_utterance_controller / §5.2
from application.dtos.record_utterance_request import RecordUtteranceRequest
from application.dtos.record_utterance_response import RecordUtteranceResponse
from application.errors import LectureNotFound
from application.result import Err, Ok
from interface_adapters.controllers.record_utterance_controller import (
    RecordUtteranceController,
)
from interface_adapters.events.speech_recognition_utterance_event import (
    SpeechRecognitionUtteranceEvent,
)
from tests.interface_adapters.conftest import SpyOrchestrator, StubUseCase


def _event(**kwargs) -> SpeechRecognitionUtteranceEvent:
    defaults = {
        "lecture_id": "lecture-1",
        "utterance_id": "utt-1",
        "start_ms": 0,
        "end_ms": 1000,
        "transcript": "こんにちは",
        "speaker_display_name": "講師",
    }
    defaults.update(kwargs)
    return SpeechRecognitionUtteranceEvent(**defaults)


def test_record_utterance_controller_calls_use_case_and_orchestrator_on_success():
    use_case = StubUseCase(
        result=Ok(
            RecordUtteranceResponse(utterance_id="utt-1", lecture_id="lecture-1")
        ),
    )
    orchestrator = SpyOrchestrator()
    controller = RecordUtteranceController(
        _use_case=use_case.execute,
        _orchestrator=orchestrator,
    )

    outcome = controller.execute(_event())

    assert len(use_case.requests) == 1
    request = use_case.requests[0]
    assert isinstance(request, RecordUtteranceRequest)
    assert request.speech_text.text == "こんにちは"
    assert request.speaker.role == "lecturer"
    assert outcome.success is True
    assert len(orchestrator.utterance_recorded) == 1


def test_record_utterance_controller_rejects_invalid_time_range():
    use_case = StubUseCase(
        result=Ok(
            RecordUtteranceResponse(utterance_id="utt-1", lecture_id="lecture-1")
        ),
    )
    orchestrator = SpyOrchestrator()
    controller = RecordUtteranceController(
        _use_case=use_case.execute,
        _orchestrator=orchestrator,
    )

    outcome = controller.execute(_event(start_ms=2000, end_ms=1000))

    assert use_case.requests == []
    assert orchestrator.utterance_recorded == []
    assert outcome.success is False
    assert outcome.error_kind == "invalid_request"


def test_record_utterance_controller_does_not_call_orchestrator_on_failure():
    use_case = StubUseCase(result=Err(LectureNotFound(lecture_id="missing")))
    orchestrator = SpyOrchestrator()
    controller = RecordUtteranceController(
        _use_case=use_case.execute,
        _orchestrator=orchestrator,
    )

    outcome = controller.execute(_event(lecture_id="missing"))

    assert outcome.success is False
    assert orchestrator.utterance_recorded == []
