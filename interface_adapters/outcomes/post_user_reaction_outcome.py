# 仕様: docs/spec/interface.md#post_user_reaction_controller
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PostUserReactionOutcome:
    success: bool
    reaction_id: str = ""
    lecture_id: str = ""
    error_kind: str = ""
