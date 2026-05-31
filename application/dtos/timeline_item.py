# 仕様: docs/spec/application.md#get_timeline
from dataclasses import dataclass
from typing import Literal

from application.errors import InvalidRequest
from application.result import Err, Ok, Result
from domain.value_objects.dialogue_speaker import DialogueSpeaker
from domain.value_objects.lecture_time_anchor import LectureTimeAnchor
from domain.value_objects.reaction_text import ReactionText
from domain.value_objects.recording_speaker import RecordingSpeaker
from domain.value_objects.reply_target import ReplyTarget
from domain.value_objects.speech_text import SpeechText
from domain.value_objects.time_range import TimeRange

_USE_CASE = "get_timeline"


@dataclass(frozen=True, slots=True)
class UtteranceTimelineItem:
    kind: Literal["utterance"]
    time_range: TimeRange
    utterance_id: str
    speech_text: SpeechText
    speaker: RecordingSpeaker


@dataclass(frozen=True, slots=True)
class ReactionTimelineItem:
    kind: Literal["reaction"]
    time_range: TimeRange
    reaction_id: str
    reaction_text: ReactionText
    speaker: DialogueSpeaker
    reply_target: ReplyTarget
    lecture_time_anchor: LectureTimeAnchor
    created_at: int


TimelineItem = UtteranceTimelineItem | ReactionTimelineItem


@dataclass(frozen=True, slots=True)
class GetTimelineRequest:
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
class GetTimelineResponse:
    lecture_id: str
    items: tuple[TimelineItem, ...]
