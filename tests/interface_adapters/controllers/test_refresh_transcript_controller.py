# 仕様: docs/spec/interface.md#refresh_transcript_controller / §7.2
from dataclasses import dataclass

from application.dtos.transcript_item import GetTranscriptRequest
from application.errors import LectureNotFound
from application.result import Err, Ok
from interface_adapters.controllers.refresh_transcript_controller import (
    RefreshTranscriptController,
)
from interface_adapters.events.transcript_refresh_request import TranscriptRefreshRequest
from interface_adapters.mappers.transcript_view_model_mapper import TranscriptViewModelMapper
from interface_adapters.presenters.transcript_presenter import TranscriptPresenter
from interface_adapters.view_models.transcript_view_model import (
    TranscriptLineView,
    TranscriptViewModel,
)
from tests.interface_adapters.conftest import (
    SpyViewModelStore,
    StubUseCase,
    make_get_transcript_response,
)


@dataclass
class SpyTranscriptPresenter:
    present_count: int = 0
    present_error_count: int = 0
    last_response: object | None = None
    last_error: object | None = None

    def present(self, response):
        self.present_count += 1
        self.last_response = response

    def present_error(self, lecture_id, error):
        self.present_error_count += 1
        self.last_error = error


def test_refresh_transcript_controller_presents_on_success():
    response = make_get_transcript_response()
    use_case = StubUseCase(result=Ok(response))
    presenter = SpyTranscriptPresenter()
    controller = RefreshTranscriptController(
        _use_case=use_case.execute,
        _presenter=presenter,
    )

    outcome = controller.execute(TranscriptRefreshRequest(lecture_id="lecture-1"))

    assert len(use_case.requests) == 1
    assert isinstance(use_case.requests[0], GetTranscriptRequest)
    assert presenter.present_count == 1
    assert presenter.present_error_count == 0
    assert outcome.success is True
    assert outcome.item_count == len(response.items)


def test_refresh_transcript_controller_present_error_on_failure():
    use_case = StubUseCase(result=Err(LectureNotFound(lecture_id="missing")))
    presenter = SpyTranscriptPresenter()
    controller = RefreshTranscriptController(
        _use_case=use_case.execute,
        _presenter=presenter,
    )

    outcome = controller.execute(TranscriptRefreshRequest(lecture_id="missing"))

    assert presenter.present_count == 0
    assert presenter.present_error_count == 1
    assert outcome.success is False


def test_refresh_transcript_present_error_clears_previous_lines():
    response = make_get_transcript_response()
    store = SpyViewModelStore()
    store.present(
        TranscriptViewModel(
            lecture_id="lecture-1",
            lines=(
                TranscriptLineView(
                    utterance_id="old",
                    time_label="00:00",
                    speaker_label="講師",
                    body="古い",
                ),
            ),
            error_message="",
        )
    )
    use_case = StubUseCase(result=Err(LectureNotFound(lecture_id="lecture-1")))
    presenter = TranscriptPresenter(
        _mapper=TranscriptViewModelMapper(),
        _store=store,
    )
    controller = RefreshTranscriptController(
        _use_case=use_case.execute,
        _presenter=presenter,
    )

    controller.execute(TranscriptRefreshRequest(lecture_id="lecture-1"))

    assert store.view_model is not None
    assert store.view_model.lines == ()
    assert store.view_model.error_message != ""
