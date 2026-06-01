# 仕様: docs/spec/application.md#get_transcript
from dataclasses import dataclass

from application.errors import InvalidRequest
from application.result import Err, Ok, Result
from domain.value_objects.recording_speaker import RecordingSpeaker
from domain.value_objects.speech_text import SpeechText
from domain.value_objects.time_range import TimeRange

_USE_CASE = "get_transcript"


@dataclass(frozen=True, slots=True)
class TranscriptItem:
    utterance_id: str
    time_range: TimeRange
    speech_text: SpeechText
    speaker: RecordingSpeaker


@dataclass(frozen=True, slots=True)
class GetTranscriptRequest:
    lecture_id: str

    def validate(self) -> Result[None, InvalidRequest]:
        if not self.lecture_id.strip():
            return Err(
                InvalidRequest(
                    use_case=_USE_CASE,
                    field="lecture_id",
                    reason="lecture_id is required",
                )
            )
        return Ok(None)


@dataclass(frozen=True, slots=True)
class GetTranscriptResponse:
    lecture_id: str
    items: tuple[TranscriptItem, ...]
