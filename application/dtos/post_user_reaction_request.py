# 仕様: docs/spec/application.md#post_user_reaction
from dataclasses import dataclass

from application.errors import InvalidRequest
from application.result import Err, Ok, Result
from domain.value_objects.lecture_time_anchor import LectureTimeAnchor
from domain.value_objects.reaction_text import ReactionText
from domain.value_objects.reply_target import ReplyTarget

_USE_CASE = "post_user_reaction"


@dataclass(frozen=True, slots=True)
class PostUserReactionRequest:
    lecture_id: str
    reaction_text: ReactionText
    lecture_time_anchor: LectureTimeAnchor
    speaker_display_name: str
    reply_target: ReplyTarget | None = None

    def validate(self) -> Result[None, InvalidRequest]:
        if not self.lecture_id.strip():
            return Err(
                InvalidRequest(
                    use_case=_USE_CASE,
                    field="lecture_id",
                    reason="lecture_id is required",
                )
            )
        if not self.speaker_display_name.strip():
            return Err(
                InvalidRequest(
                    use_case=_USE_CASE,
                    field="speaker_display_name",
                    reason="speaker_display_name is required",
                )
            )
        return Ok(None)
