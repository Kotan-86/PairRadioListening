# 仕様: docs/spec/interface.md#7.3
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TranscriptLineView:
    utterance_id: str
    time_label: str
    speaker_label: str
    body: str


@dataclass(frozen=True, slots=True)
class TranscriptViewModel:
    lecture_id: str
    lines: tuple[TranscriptLineView, ...]
    error_message: str
