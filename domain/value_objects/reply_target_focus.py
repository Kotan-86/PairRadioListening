# 仕様: docs/spec/application.md#reply_target_focus, docs/spec/framework_llm.md#3.2
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class UtteranceReplyTargetFocus:
    kind: Literal["utterance"]
    utterance_id: str
    speech_text: str
    start_ms: int
    end_ms: int


@dataclass(frozen=True, slots=True)
class ReactionReplyTargetFocus:
    kind: Literal["reaction"]
    reaction_id: str
    reaction_text: str
    speaker_display_name: str


ReplyTargetFocus = UtteranceReplyTargetFocus | ReactionReplyTargetFocus
