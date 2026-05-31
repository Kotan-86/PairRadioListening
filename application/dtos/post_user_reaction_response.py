# 仕様: docs/spec/application.md#post_user_reaction
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PostUserReactionResponse:
    reaction_id: str
    lecture_id: str
