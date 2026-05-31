# 仕様: docs/spec/application.md#generate_ai_reactions_for_utterance
from dataclasses import dataclass

from application.errors import InvalidRequest
from application.result import Err, Ok, Result

_USE_CASE = "generate_ai_reactions_for_utterance"


@dataclass(frozen=True, slots=True)
class GenerateAiReactionsForUtteranceRequest:
    lecture_id: str
    utterance_id: str

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
        return Ok(None)
