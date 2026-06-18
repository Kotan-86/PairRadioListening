# 仕様: docs/spec/interface.md#6.7
from interface_adapters.mappers.transcript_view_model_mapper import TranscriptViewModelMapper
from interface_adapters.presentation.time_label_format import format_time_label
from tests.interface_adapters.conftest import make_get_transcript_response, make_transcript_item


def test_transcript_mapper_line_count_matches_items():
    response = make_get_transcript_response(
        items=(
            make_transcript_item(utterance_id="u1"),
            make_transcript_item(utterance_id="u2", start_ms=2000, end_ms=3000),
        )
    )
    mapper = TranscriptViewModelMapper()

    view_model = mapper.to_view_model(response)

    assert len(view_model.lines) == len(response.items)


def test_transcript_mapper_copies_fields_from_items():
    item = make_transcript_item(
        utterance_id="u42",
        speech_text="書き起こし",
        speaker_name="講師A",
        start_ms=5000,
        end_ms=6000,
    )
    response = make_get_transcript_response(items=(item,))
    mapper = TranscriptViewModelMapper()

    view_model = mapper.to_view_model(response)
    line = view_model.lines[0]

    assert line.utterance_id == item.utterance_id
    assert line.body == item.speech_text.text
    assert line.speaker_label == item.speaker.display_name


def test_transcript_mapper_generates_time_label_from_time_range():
    item = make_transcript_item(start_ms=0, end_ms=1000)
    mapper = TranscriptViewModelMapper()

    view_model = mapper.to_view_model(make_get_transcript_response(items=(item,)))

    assert view_model.lines[0].time_label == format_time_label(item.time_range)


def test_transcript_mapper_success_has_empty_error_message():
    mapper = TranscriptViewModelMapper()

    view_model = mapper.to_view_model(make_get_transcript_response())

    assert view_model.error_message == ""


def test_transcript_mapper_latest_anchor_ms_is_last_item_end_ms():
    response = make_get_transcript_response(
        items=(
            make_transcript_item(utterance_id="u1", start_ms=0, end_ms=1200),
            make_transcript_item(utterance_id="u2", start_ms=1300, end_ms=2500),
        )
    )
    mapper = TranscriptViewModelMapper()

    view_model = mapper.to_view_model(response)

    assert view_model.latest_anchor_ms == 2500


def test_transcript_mapper_latest_anchor_ms_is_zero_when_items_empty():
    mapper = TranscriptViewModelMapper()

    view_model = mapper.to_view_model(make_get_transcript_response(items=()))

    assert view_model.latest_anchor_ms == 0


def test_transcript_mapper_error_has_zero_latest_anchor_ms():
    from application.errors import LectureNotFound

    mapper = TranscriptViewModelMapper()

    view_model = mapper.to_error_view_model(
        "missing", LectureNotFound(lecture_id="missing")
    )

    assert view_model.latest_anchor_ms == 0
