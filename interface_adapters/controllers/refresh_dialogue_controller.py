# 仕様: docs/spec/interface.md#refresh_dialogue_controller
from collections.abc import Callable
from dataclasses import dataclass

from application.dtos.dialogue_item import GetDialogueRequest, GetDialogueResponse
from application.dtos.transcript_item import GetTranscriptRequest, GetTranscriptResponse
from application.errors.use_case_errors import GetDialogueError, GetTranscriptError
from application.result import Result
from interface_adapters.events.dialogue_refresh_request import DialogueRefreshRequest
from interface_adapters.mappers.dialogue_presentation_context_builder import (
    build_dialogue_presentation_context,
)
from interface_adapters.outcomes.dialogue_refresh_outcome import DialogueRefreshOutcome
from interface_adapters.presentation.error_kind import error_kind_for
from interface_adapters.presenters.dialogue_presenter import DialoguePresenter


@dataclass(frozen=True, slots=True)
class RefreshDialogueController:
    _dialogue_use_case: Callable[
        [GetDialogueRequest], Result[GetDialogueResponse, GetDialogueError]
    ]
    _transcript_use_case: Callable[
        [GetTranscriptRequest], Result[GetTranscriptResponse, GetTranscriptError]
    ]
    _presenter: DialoguePresenter

    def execute(self, request: DialogueRefreshRequest) -> DialogueRefreshOutcome:
        dialogue_result = self._dialogue_use_case(
            GetDialogueRequest(lecture_id=request.lecture_id)
        )
        if dialogue_result.is_err():
            self._presenter.present_error(request.lecture_id, dialogue_result.error)
            return DialogueRefreshOutcome(
                success=False,
                error_kind=error_kind_for(dialogue_result.error),
            )

        transcript_result = self._transcript_use_case(
            GetTranscriptRequest(lecture_id=request.lecture_id)
        )
        if transcript_result.is_err():
            self._presenter.present_error(request.lecture_id, transcript_result.error)
            return DialogueRefreshOutcome(
                success=False,
                error_kind=error_kind_for(transcript_result.error),
            )

        dialogue_response = dialogue_result.value
        context = build_dialogue_presentation_context(
            dialogue_response,
            transcript_result.value,
        )
        self._presenter.present(dialogue_response, context)
        return DialogueRefreshOutcome(
            success=True,
            item_count=len(dialogue_response.items),
        )
