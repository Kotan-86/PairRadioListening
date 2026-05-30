# 仕様: docs/spec/domain.md#reply_target
from dataclasses import dataclass
from typing import Literal

from domain.entities.entity import EntityId

ReplyTargetKind = Literal["utterance", "reaction"]


@dataclass(frozen=True)
class ReplyTarget:
    reply_target_kind: ReplyTargetKind
    reply_target_id: EntityId

    def __post_init__(self) -> None:
        if self.reply_target_kind not in ("utterance", "reaction"):
            raise ValueError("reply_target の reply_target_kind は utterance または reaction のみです")
        if isinstance(self.reply_target_id, str) and not self.reply_target_id.strip():
            raise ValueError("reply_target の reply_target_id は空にできません")
