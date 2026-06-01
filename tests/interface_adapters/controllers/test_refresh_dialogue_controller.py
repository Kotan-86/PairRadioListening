# 仕様: docs/spec/interface.md#refresh_dialogue_controller / §7.2
from dataclasses import dataclass

from application.dtos.dialogue_item import GetDialogueRequest
from application.dtos.transcript_item import GetTranscriptRequest
from application.errors import LectureNotFound, PersistenceFailed
from application.result import Err, Ok
from interface_adapters.controllers.refresh_dialogue_controller import (
    RefreshDialogueController,
)
from interface_adapters.events.dialogue_refresh_request import DialogueRefreshRequest
from interface_adapters.mappers.dialogue_view_model_mapper import DialogueViewModelMapper
from interface_adapters.presenters.dialogue_presenter import DialoguePresenter
from interface_adapters.view_models.dialogue_presentation_context import (
    DialoguePresentationContext,
)
from interface_adapters.view_models.dialogue_view_model import (
    DialogueLineView,
    DialogueViewModel,
)
from tests.interface_adapters.conftest import (
    SpyViewModelStore,
    make_get_dialogue_response,
    make_get_transcript_response,
)


@dataclass
class SpyDialoguePresenter:
    present_count: int = 0
    present_error_count: int = 0
    last_context: DialoguePresentationContext | None = None

    def present(self, response, context):
        self.present_count += 1
        self.last_context = context

    def present_error(self, lecture_id, error):
        self.present_error_count += 1


@dataclass
class DualStubUseCase:
    dialogue_result: object
    transcript_result: object
    dialogue_requests: list = None
    transcript_requests: list = None

    def __post_init__(self):
        if self.dialogue_requests is None:
            self.dialogue_requests = []
        if self.transcript_requests is None:
            self.transcript_requests = []

    def execute_dialogue(self, request):
        self.dialogue_requests.append(request)
        return self.dialogue_result

    def execute_transcript(self, request):
        self.transcript_requests.append(request)
        return self.transcript_result


def test_refresh_dialogue_controller_builds_context_and_presents():
    dialogue_response = make_get_dialogue_response()
    transcript_response = make_get_transcript_response()
    stubs = DualStubUseCase(
        dialogue_result=Ok(dialogue_response),
        transcript_result=Ok(transcript_response),
    )
    presenter = SpyDialoguePresenter()
    controller = RefreshDialogueController(
        _dialogue_use_case=stubs.execute_dialogue,
        _transcript_use_case=stubs.execute_transcript,
        _presenter=presenter,
    )

    outcome = controller.execute(DialogueRefreshRequest(lecture_id="lecture-1"))

    assert len(stubs.dialogue_requests) == 1
    assert isinstance(stubs.dialogue_requests[0], GetDialogueRequest)
    assert len(stubs.transcript_requests) == 1
    assert isinstance(stubs.transcript_requests[0], GetTranscriptRequest)
    assert presenter.present_count == 1
    assert presenter.present_error_count == 0
    assert presenter.last_context is not None
    assert outcome.success is True
    assert outcome.item_count == len(dialogue_response.items)


def test_refresh_dialogue_controller_present_error_when_dialogue_fails():
    stubs = DualStubUseCase(
        dialogue_result=Err(LectureNotFound(lecture_id="missing")),
        transcript_result=Ok(make_get_transcript_response()),
    )
    presenter = SpyDialoguePresenter()
    controller = RefreshDialogueController(
        _dialogue_use_case=stubs.execute_dialogue,
        _transcript_use_case=stubs.execute_transcript,
        _presenter=presenter,
    )

    outcome = controller.execute(DialogueRefreshRequest(lecture_id="missing"))

    assert stubs.transcript_requests == []
    assert presenter.present_count == 0
    assert presenter.present_error_count == 1
    assert outcome.success is False


def test_refresh_dialogue_controller_present_error_when_transcript_fails():
    stubs = DualStubUseCase(
        dialogue_result=Ok(make_get_dialogue_response()),
        transcript_result=Err(
            PersistenceFailed(
                use_case="get_transcript",
                operation="load",
                resource="lecture",
            )
        ),
    )
    presenter = SpyDialoguePresenter()
    controller = RefreshDialogueController(
        _dialogue_use_case=stubs.execute_dialogue,
        _transcript_use_case=stubs.execute_transcript,
        _presenter=presenter,
    )

    outcome = controller.execute(DialogueRefreshRequest(lecture_id="lecture-1"))

    assert len(stubs.dialogue_requests) == 1
    assert presenter.present_count == 0
    assert presenter.present_error_count == 1
    assert outcome.success is False


def test_refresh_dialogue_present_error_clears_previous_lines():
    store = SpyViewModelStore()
    store.present(
        DialogueViewModel(
            lecture_id="lecture-1",
            lines=(
                DialogueLineView(
                    reaction_id="old",
                    speaker_label="ユーザー",
                    body="古い",
                    reference_time_label="",
                    reference_quote_label="",
                ),
            ),
            error_message="",
        )
    )
    stubs = DualStubUseCase(
        dialogue_result=Err(LectureNotFound(lecture_id="lecture-1")),
        transcript_result=Ok(make_get_transcript_response()),
    )
    presenter = DialoguePresenter(
        _mapper=DialogueViewModelMapper(),
        _store=store,
    )
    controller = RefreshDialogueController(
        _dialogue_use_case=stubs.execute_dialogue,
        _transcript_use_case=stubs.execute_transcript,
        _presenter=presenter,
    )

    controller.execute(DialogueRefreshRequest(lecture_id="lecture-1"))

    assert store.view_model is not None
    assert store.view_model.lines == ()
    assert store.view_model.error_message != ""
