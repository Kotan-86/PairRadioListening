# 仕様: docs/spec/interface.md#record_utterance_controller
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from application.dtos.record_utterance_request import RecordUtteranceRequest
from application.dtos.record_utterance_response import RecordUtteranceResponse
from application.errors import InvalidRequest
from application.errors.use_case_errors import RecordUtteranceError
from application.result import Result
from domain.value_objects.recording_speaker import RecordingSpeaker
from domain.value_objects.speech_text import SpeechText
from domain.value_objects.time_range import TimeRange
from interface_adapters.events.speech_recognition_utterance_event import (
    SpeechRecognitionUtteranceEvent,
)
from interface_adapters.outcomes.record_utterance_outcome import RecordUtteranceOutcome
from interface_adapters.presentation.error_kind import error_kind_for

_USE_CASE = "record_utterance"


class AiReactionOrchestratorPort(Protocol):
    def on_utterance_recorded(self, response: RecordUtteranceResponse) -> None: ...


@dataclass(frozen=True, slots=True)
class RecordUtteranceController:
    _use_case: Callable[
        [RecordUtteranceRequest], Result[RecordUtteranceResponse, RecordUtteranceError]
    ]
    _orchestrator: AiReactionOrchestratorPort

    def execute(self, event: SpeechRecognitionUtteranceEvent) -> RecordUtteranceOutcome:
        validation = self._validate_event(event)
        if validation is not None:
            return validation

        request = RecordUtteranceRequest(
            lecture_id=event.lecture_id,
            utterance_id=event.utterance_id,
            time_range=TimeRange(start_ms=event.start_ms, end_ms=event.end_ms),
            speech_text=SpeechText(text=event.transcript),
            speaker=RecordingSpeaker(
                display_name=event.speaker_display_name,
                role="lecturer",
            ),
        )
        result = self._use_case(request)
        if result.is_err():
            return RecordUtteranceOutcome(
                success=False,
                error_kind=error_kind_for(result.error),
            )

        response = result.value
        self._orchestrator.on_utterance_recorded(response)
        return RecordUtteranceOutcome(
            success=True,
            utterance_id=response.utterance_id,
            lecture_id=response.lecture_id,
        )

    def _validate_event(
        self, event: SpeechRecognitionUtteranceEvent
    ) -> RecordUtteranceOutcome | None:
        if not event.lecture_id.strip():
            return RecordUtteranceOutcome(
                success=False,
                error_kind=error_kind_for(
                    InvalidRequest(
                        use_case=_USE_CASE,
                        field="lecture_id",
                        reason="lecture_id is required",
                    )
                ),
            )
        if not event.utterance_id.strip():
            return RecordUtteranceOutcome(
                success=False,
                error_kind=error_kind_for(
                    InvalidRequest(
                        use_case=_USE_CASE,
                        field="utterance_id",
                        reason="utterance_id is required",
                    )
                ),
            )
        if not event.transcript.strip():
            return RecordUtteranceOutcome(
                success=False,
                error_kind=error_kind_for(
                    InvalidRequest(
                        use_case=_USE_CASE,
                        field="transcript",
                        reason="transcript is required",
                    )
                ),
            )
        if not event.speaker_display_name.strip():
            return RecordUtteranceOutcome(
                success=False,
                error_kind=error_kind_for(
                    InvalidRequest(
                        use_case=_USE_CASE,
                        field="speaker_display_name",
                        reason="speaker_display_name is required",
                    )
                ),
            )
        if event.start_ms > event.end_ms:
            return RecordUtteranceOutcome(
                success=False,
                error_kind=error_kind_for(
                    InvalidRequest(
                        use_case=_USE_CASE,
                        field="time_range",
                        reason="start_ms must be less than or equal to end_ms",
                    )
                ),
            )
        return None
