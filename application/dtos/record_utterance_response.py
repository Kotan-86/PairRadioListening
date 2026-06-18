# 仕様: docs/spec/application.md#record_utterance
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecordUtteranceResponse:
    utterance_id: str
    lecture_id: str
