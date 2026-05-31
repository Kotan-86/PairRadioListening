# 仕様: docs/spec/application.md#共通エラー
from dataclasses import dataclass
from typing import Literal

PersistenceOperation = Literal["save", "load"]


@dataclass(frozen=True, slots=True)
class InvalidRequest:
    use_case: str
    field: str | None = None
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class PersistenceFailed:
    use_case: str
    operation: PersistenceOperation
    resource: str


@dataclass(frozen=True, slots=True)
class LectureNotFound:
    lecture_id: str


@dataclass(frozen=True, slots=True)
class LectureClosed:
    lecture_id: str


@dataclass(frozen=True, slots=True)
class LectureAlreadyClosed:
    lecture_id: str
