# 仕様: docs/spec/domain.md#speech_text
from dataclasses import dataclass


@dataclass(frozen=True)
class SpeechText:
    text: str
