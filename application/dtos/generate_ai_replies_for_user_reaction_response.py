# 仕様: docs/spec/application.md#generate_ai_replies_for_user_reaction
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GenerateAiRepliesForUserReactionResponse:
    lecture_id: str
    user_reaction_id: str
    reaction_id: str
