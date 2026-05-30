# 仕様: docs/spec/domain.md#utterance（エンティティ）
from dataclasses import dataclass

from domain.entities.entity import Entity
from domain.value_objects.recording_speaker import RecordingSpeaker
from domain.value_objects.speech_text import SpeechText
from domain.value_objects.time_range import TimeRange


@dataclass(kw_only=True)
class Utterance(Entity):
    time_range: TimeRange
    speech_text: SpeechText
    speaker: RecordingSpeaker
