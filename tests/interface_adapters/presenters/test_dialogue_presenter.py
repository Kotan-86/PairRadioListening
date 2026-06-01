# 仕様: docs/spec/interface.md#6.5
from dataclasses import dataclass

from application.errors import LectureNotFound
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
)


@dataclass
class FakeDialogueMapper:
    success_view_model: DialogueViewModel | None = None
    last_response: object | None = None
    last_context: DialoguePresentationContext | None = None

    def to_view_model(self, response, context):
        self.last_response = response
        self.last_context = context
        return self.success_view_model or DialogueViewModel(
            lecture_id=response.lecture_id,
            lines=(),
            error_message="",
        )

    def to_error_view_model(self, lecture_id, error):
        return DialogueViewModel(
            lecture_id=lecture_id,
            lines=(),
            error_message="error",
        )


def test_dialogue_presenter_passes_context_to_mapper():
    response = make_get_dialogue_response()
    context = DialoguePresentationContext(utterance_times={}, reaction_snippets={})
    store = SpyViewModelStore()
    mapper = FakeDialogueMapper()
    presenter = DialoguePresenter(_mapper=mapper, _store=store)

    presenter.present(response, context)

    assert mapper.last_response == response
    assert mapper.last_context == context
    assert store.present_count == 1


def test_dialogue_presenter_present_error_clears_lines_and_sets_error_message():
    store = SpyViewModelStore()
    store.present(
        DialogueViewModel(
            lecture_id="lecture-1",
            lines=(
                DialogueLineView(
                    reaction_id="r1",
                    speaker_label="ユーザー",
                    body="古い",
                    reference_time_label="",
                    reference_quote_label="",
                ),
            ),
            error_message="",
        )
    )
    mapper = DialogueViewModelMapper()
    presenter = DialoguePresenter(_mapper=mapper, _store=store)

    presenter.present_error("missing", LectureNotFound(lecture_id="missing"))

    assert store.view_model is not None
    assert store.view_model.lines == ()
    assert store.view_model.error_message != ""
