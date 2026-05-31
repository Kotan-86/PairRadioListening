# 仕様: docs/spec/application.md#講義記録コンテキスト
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InvalidPersonaProfiles:
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class UtteranceNotFound:
    lecture_id: str
    utterance_id: str
