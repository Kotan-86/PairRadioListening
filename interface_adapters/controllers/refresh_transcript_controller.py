# 仕様: docs/spec/interface.md#refresh_transcript_controller
from collections.abc import Callable
from dataclasses import dataclass

from application.dtos.transcript_item import GetTranscriptRequest, GetTranscriptResponse
from application.errors.use_case_errors import GetTranscriptError
from application.result import Result
from interface_adapters.events.transcript_refresh_request import TranscriptRefreshRequest
from interface_adapters.outcomes.transcript_refresh_outcome import TranscriptRefreshOutcome
from interface_adapters.presentation.error_kind import error_kind_for
from interface_adapters.presenters.transcript_presenter import TranscriptPresenter


@dataclass(frozen=True, slots=True)
class RefreshTranscriptController:
    _use_case: Callable[
        [GetTranscriptRequest], Result[GetTranscriptResponse, GetTranscriptError]
    ]
    _presenter: TranscriptPresenter

    def execute(self, request: TranscriptRefreshRequest) -> TranscriptRefreshOutcome:
        result = self._use_case(GetTranscriptRequest(lecture_id=request.lecture_id))
        if result.is_err():
            self._presenter.present_error(request.lecture_id, result.error)
            return TranscriptRefreshOutcome(
                success=False,
                error_kind=error_kind_for(result.error),
            )

        response = result.value
        self._presenter.present(response)
        return TranscriptRefreshOutcome(
            success=True,
            item_count=len(response.items),
        )
