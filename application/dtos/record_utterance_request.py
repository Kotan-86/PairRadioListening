# 仕様: docs/spec/application.md#record_utterance
from dataclasses import dataclass

from application.errors import InvalidRequest
from application.result import Err, Ok, Result
from domain.value_objects.recording_speaker import RecordingSpeaker
from domain.value_objects.speech_text import SpeechText
from domain.value_objects.time_range import TimeRange

_USE_CASE = "record_utterance"


@dataclass(frozen=True, slots=True)
class RecordUtteranceRequest:
    lecture_id: str
    utterance_id: str
    time_range: TimeRange
    speech_text: SpeechText
    speaker: RecordingSpeaker

    def validate(self) -> Result[None, InvalidRequest]:
        if not self.lecture_id.strip():
            return Err(
                InvalidRequest(
                    use_case=_USE_CASE,
                    field="lecture_id",
                    reason="lecture_id is required",
                )
            )
        if not self.utterance_id.strip():
            return Err(
                InvalidRequest(
                    use_case=_USE_CASE,
                    field="utterance_id",
                    reason="utterance_id is required",
                )
            )
        if self.speaker.role != "lecturer":
            return Err(
                InvalidRequest(
                    use_case=_USE_CASE,
                    field="speaker",
                    reason="speaker.role must be lecturer",
                )
            )
        return Ok(None)
