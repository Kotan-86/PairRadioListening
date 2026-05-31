# 仕様: docs/spec/application.md#generate_ai_replies_for_user_reaction
from dataclasses import dataclass

from application.errors import InvalidRequest
from application.result import Err, Ok, Result

_USE_CASE = "generate_ai_replies_for_user_reaction"


@dataclass(frozen=True, slots=True)
class GenerateAiRepliesForUserReactionRequest:
    lecture_id: str
    reaction_id: str

    def validate(self) -> Result[None, InvalidRequest]:
        if not self.lecture_id.strip():
            return Err(
                InvalidRequest(
                    use_case=_USE_CASE,
                    field="lecture_id",
                    reason="lecture_id is required",
                )
            )
        if not self.reaction_id.strip():
            return Err(
                InvalidRequest(
                    use_case=_USE_CASE,
                    field="reaction_id",
                    reason="reaction_id is required",
                )
            )
        return Ok(None)
