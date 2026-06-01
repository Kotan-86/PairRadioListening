# 仕様: docs/spec/interface.md#start_lecture_controller
from application.dtos.start_lecture_request import StartLectureRequest
from application.dtos.start_lecture_response import StartLectureResponse
from application.errors import InvalidPersonaProfiles, PersistenceFailed
from application.result import Err, Ok
from domain.value_objects.ai_persona_profile import AiPersonaProfile
from interface_adapters.controllers.start_lecture_controller import StartLectureController
from interface_adapters.events.start_lecture_form_event import StartLectureFormEvent
from tests.interface_adapters.conftest import StubUseCase


def _persona() -> AiPersonaProfile:
    return AiPersonaProfile(
        id="persona-1",
        display_name="AI",
        persona_prompt="prompt",
    )


def test_start_lecture_controller_calls_use_case_once_with_one_persona():
    use_case = StubUseCase(
        result=Ok(StartLectureResponse(lecture_id="lecture-new")),
    )
    controller = StartLectureController(_use_case=use_case.execute)
    event = StartLectureFormEvent(persona_profiles=(_persona(),), title="講義")

    outcome = controller.execute(event)

    assert len(use_case.requests) == 1
    request = use_case.requests[0]
    assert isinstance(request, StartLectureRequest)
    assert len(request.persona_profiles) == 1
    assert outcome.success is True
    assert outcome.lecture_id == "lecture-new"


def test_start_lecture_controller_rejects_multiple_personas_without_calling_use_case():
    use_case = StubUseCase(
        result=Ok(StartLectureResponse(lecture_id="lecture-new")),
    )
    controller = StartLectureController(_use_case=use_case.execute)
    event = StartLectureFormEvent(
        persona_profiles=(_persona(), _persona()),
    )

    outcome = controller.execute(event)

    assert use_case.requests == []
    assert outcome.success is False
    assert outcome.error_kind == "invalid_persona_profiles"


def test_start_lecture_controller_maps_use_case_error():
    use_case = StubUseCase(
        result=Err(
            PersistenceFailed(
                use_case="start_lecture",
                operation="save",
                resource="lecture",
            )
        ),
    )
    controller = StartLectureController(_use_case=use_case.execute)

    outcome = controller.execute(StartLectureFormEvent(persona_profiles=(_persona(),)))

    assert outcome.success is False
    assert outcome.error_kind == "persistence_failed"
