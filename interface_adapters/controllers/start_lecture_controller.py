# 仕様: docs/spec/interface.md#start_lecture_controller
from collections.abc import Callable
from dataclasses import dataclass

from application.dtos.start_lecture_request import StartLectureRequest
from application.dtos.start_lecture_response import StartLectureResponse
from application.errors import InvalidPersonaProfiles
from application.errors.use_case_errors import StartLectureError
from application.result import Result
from interface_adapters.events.start_lecture_form_event import StartLectureFormEvent
from interface_adapters.outcomes.start_lecture_outcome import StartLectureOutcome
from interface_adapters.presentation.error_kind import error_kind_for


@dataclass(frozen=True, slots=True)
class StartLectureController:
    _use_case: Callable[[StartLectureRequest], Result[StartLectureResponse, StartLectureError]]

    def execute(self, event: StartLectureFormEvent) -> StartLectureOutcome:
        validation = self._validate_event(event)
        if validation is not None:
            return validation

        request = StartLectureRequest.from_fields(
            persona_profiles=event.persona_profiles,
            title=event.title,
        )
        result = self._use_case(request)
        if result.is_err():
            return StartLectureOutcome(
                success=False,
                error_kind=error_kind_for(result.error),
            )
        return StartLectureOutcome(
            success=True,
            lecture_id=result.value.lecture_id,
        )

    def _validate_event(self, event: StartLectureFormEvent) -> StartLectureOutcome | None:
        if len(event.persona_profiles) != 1:
            return StartLectureOutcome(
                success=False,
                error_kind=error_kind_for(
                    InvalidPersonaProfiles(
                        reason="persona_profiles must contain exactly one item",
                    )
                ),
            )
        persona = event.persona_profiles[0]
        if not str(persona.id).strip() or not persona.display_name.strip():
            return StartLectureOutcome(
                success=False,
                error_kind=error_kind_for(
                    InvalidPersonaProfiles(reason="persona profile is incomplete"),
                ),
            )
        return None
