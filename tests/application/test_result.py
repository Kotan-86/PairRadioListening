# 仕様: docs/spec/application.md#実装方針
from application.errors import InvalidRequest, LectureNotFound
from application.result import Err, Ok


def test_ok_is_success():
    result = Ok(value="lecture-1")

    assert result.is_ok()
    assert not result.is_err()
    assert result.value == "lecture-1"


def test_err_is_failure():
    result = Err(error=LectureNotFound(lecture_id="missing"))

    assert result.is_err()
    assert not result.is_ok()
    assert isinstance(result.error, LectureNotFound)
    assert result.error.lecture_id == "missing"


def test_err_carries_application_error():
    result = Err(
        error=InvalidRequest(use_case="start_lecture", field="persona_profiles")
    )

    assert result.is_err()
    assert result.error.use_case == "start_lecture"
    assert result.error.field == "persona_profiles"
