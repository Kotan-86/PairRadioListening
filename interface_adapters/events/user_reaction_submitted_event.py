# 仕様: docs/spec/interface.md#post_user_reaction_controller
from dataclasses import dataclass

from domain.value_objects.reply_target import ReplyTarget


@dataclass(frozen=True, slots=True)
class UserReactionSubmittedEvent:
    lecture_id: str
    reaction_text: str
    lecture_time_anchor_ms: int
    speaker_display_name: str
    reply_target: ReplyTarget | None = None
