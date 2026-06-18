# 仕様: docs/spec/interface.md#7.2 / §6.7
from application.errors import InvalidRequest, LectureNotFound, PersistenceFailed
from interface_adapters.mappers.error_view_model_mapper import ErrorViewModelMapper
from interface_adapters.presentation.error_messages import error_message_for


def test_invalid_request_maps_to_non_empty_error_message_for_transcript():
    error = InvalidRequest(use_case="get_transcript", field="lecture_id")
    mapper = ErrorViewModelMapper()

    view_model = mapper.to_transcript_error_view_model("lecture-1", error)

    assert view_model.lines == ()
    assert view_model.error_message == error_message_for(error)
    assert view_model.error_message != ""


def test_lecture_not_found_maps_to_non_empty_error_message_for_dialogue():
    error = LectureNotFound(lecture_id="missing")
    mapper = ErrorViewModelMapper()

    view_model = mapper.to_dialogue_error_view_model("missing", error)

    assert view_model.lines == ()
    assert view_model.error_message == error_message_for(error)
    assert view_model.error_message != ""


def test_persistence_failed_maps_to_formatted_message():
    error = PersistenceFailed(
        use_case="get_transcript",
        operation="load",
        resource="lecture",
    )
    mapper = ErrorViewModelMapper()

    view_model = mapper.to_transcript_error_view_model("lecture-1", error)

    assert view_model.lines == ()
    assert view_model.error_message == error_message_for(error)
