# 仕様: docs/spec/application.md#get_dialogue
from dataclasses import dataclass

from application.errors import InvalidRequest
from application.result import Err, Ok, Result
from domain.value_objects.dialogue_speaker import DialogueSpeaker
from domain.value_objects.lecture_time_anchor import LectureTimeAnchor
from domain.value_objects.reaction_text import ReactionText
from domain.value_objects.reply_target import ReplyTarget

_USE_CASE = "get_dialogue"


@dataclass(frozen=True, slots=True)
class DialogueItem:
    reaction_id: str
    dialogue_sequence: int
    reaction_text: ReactionText
    speaker: DialogueSpeaker
    reply_target: ReplyTarget
    lecture_time_anchor: LectureTimeAnchor


@dataclass(frozen=True, slots=True)
class GetDialogueRequest:
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
class GetDialogueResponse:
    lecture_id: str
    items: tuple[DialogueItem, ...]
