# 仕様: docs/spec/interface.md#record_utterance_controller
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RecordUtteranceOutcome:
    success: bool
    utterance_id: str = ""
    lecture_id: str = ""
    error_kind: str = ""
