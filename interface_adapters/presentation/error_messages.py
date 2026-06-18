# 仕様: docs/spec/interface.md#7.2
from application.errors import (
    InvalidRequest,
    LectureNotFound,
    PersistenceFailed,
)

QUOTE_EXCERPT_MAX_LENGTH = 20
QUOTE_LABEL_SEPARATOR = ": "

_ERROR_MESSAGES: dict[type[object], str] = {
    InvalidRequest: "入力内容を確認してください。",
    LectureNotFound: "講義が見つかりません。",
    PersistenceFailed: "データの読み込みに失敗しました。",
}


def error_message_for(error: object) -> str:
    for error_type, message in _ERROR_MESSAGES.items():
        if isinstance(error, error_type):
            return message
    return "表示の更新に失敗しました。"
