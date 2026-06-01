# 仕様: docs/spec/interface.md#record_utterance_controller
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SpeechRecognitionUtteranceEvent:
    lecture_id: str
    utterance_id: str
    start_ms: int
    end_ms: int
    transcript: str
    speaker_display_name: str
