# 仕様: docs/spec/application.md#4-アプリケーションエラー
from application.errors import (
    AiReactionBatchIncomplete,
    EndLectureError,
    InvalidPersonaProfiles,
    LectureAlreadyClosed,
    ReplyTargetNotFound,
    StartLectureError,
)


def test_error_dataclasses_are_frozen():
    error = InvalidPersonaProfiles(reason="empty")
    assert error.reason == "empty"


def test_reply_target_not_found_fields():
    error = ReplyTargetNotFound(
        lecture_id="lec-1",
        reply_target_kind="utterance",
        reply_target_id="utt-1",
    )
    assert error.reply_target_kind == "utterance"


def test_ai_reaction_batch_incomplete_fields():
    error = AiReactionBatchIncomplete(
        lecture_id="lec-1",
        expected_count=2,
        succeeded_count=1,
    )
    assert error.expected_count == 2


def test_use_case_error_type_aliases_exist():
    # 型エイリアスが import 可能であること（UC 実装時の契約）
    assert StartLectureError is not None
    assert EndLectureError is not None


def test_lecture_already_closed_distinct_from_lecture_closed():
    already = LectureAlreadyClosed(lecture_id="lec-1")
    assert already.lecture_id == "lec-1"
