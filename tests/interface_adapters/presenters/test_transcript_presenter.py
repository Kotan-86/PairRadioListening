# 仕様: docs/spec/interface.md#6.4
from dataclasses import dataclass

from application.errors import LectureNotFound
from interface_adapters.mappers.transcript_view_model_mapper import TranscriptViewModelMapper
from interface_adapters.presenters.transcript_presenter import TranscriptPresenter
from interface_adapters.view_models.transcript_view_model import (
    TranscriptLineView,
    TranscriptViewModel,
)
from tests.interface_adapters.conftest import (
    SpyViewModelStore,
    make_get_transcript_response,
)


@dataclass
class FakeTranscriptMapper:
    success_view_model: TranscriptViewModel | None = None
    error_view_model: TranscriptViewModel | None = None
    last_response: object | None = None
    last_error_lecture_id: str | None = None
    last_error: object | None = None

    def to_view_model(self, response):
        self.last_response = response
        return self.success_view_model or TranscriptViewModel(
            lecture_id=response.lecture_id,
            lines=(),
            latest_anchor_ms=0,
            error_message="",
        )

    def to_error_view_model(self, lecture_id, error):
        self.last_error_lecture_id = lecture_id
        self.last_error = error
        return self.error_view_model or TranscriptViewModel(
            lecture_id=lecture_id,
            lines=(),
            latest_anchor_ms=0,
            error_message="error",
        )


def test_transcript_presenter_present_replaces_store_view_model():
    response = make_get_transcript_response()
    expected = TranscriptViewModel(
        lecture_id=response.lecture_id,
        lines=(
            TranscriptLineView(
                utterance_id="u1",
                time_label="00:00",
                speaker_label="講師",
                body="本文",
            ),
        ),
        latest_anchor_ms=0,
        error_message="",
    )
    store = SpyViewModelStore()
    mapper = FakeTranscriptMapper(success_view_model=expected)
    presenter = TranscriptPresenter(_mapper=mapper, _store=store)

    presenter.present(response)

    assert store.present_count == 1
    assert store.view_model == expected
    assert store.view_model.error_message == ""


def test_transcript_presenter_present_error_clears_lines_and_sets_error_message():
    store = SpyViewModelStore()
    store.present(
        TranscriptViewModel(
            lecture_id="lecture-1",
            lines=(
                TranscriptLineView(
                    utterance_id="old",
                    time_label="00:00",
                    speaker_label="講師",
                    body="古い内容",
                ),
            ),
            latest_anchor_ms=0,
            error_message="",
        )
    )
    mapper = TranscriptViewModelMapper()
    presenter = TranscriptPresenter(_mapper=mapper, _store=store)
    error = LectureNotFound(lecture_id="missing")

    presenter.present_error("missing", error)

    assert store.present_count == 2
    assert store.view_model is not None
    assert store.view_model.lines == ()
    assert store.view_model.error_message != ""
