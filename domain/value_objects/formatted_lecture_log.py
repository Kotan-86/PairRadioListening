from dataclasses import dataclass
from enum import Enum, auto

class LogFormat(Enum):
    """出力するログのフォーマット形式"""
    MARKDOWN = auto()
    JSON = auto()

@dataclass(frozen=True)
class FormattedLectureLog:
    format_type: LogFormat
    content: str

    def to_string(self) -> str:
        return self.content
