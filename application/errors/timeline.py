# 仕様: docs/spec/application.md#タイムライン対話コンテキスト
from dataclasses import dataclass
from typing import Literal

ReplyTargetKind = Literal["utterance", "reaction"]


@dataclass(frozen=True, slots=True)
class TimelineNotEstablished:
    lecture_id: str


@dataclass(frozen=True, slots=True)
class ReplyTargetNotFound:
    lecture_id: str
    reply_target_kind: ReplyTargetKind
    reply_target_id: str


@dataclass(frozen=True, slots=True)
class ReactionNotFound:
    lecture_id: str
    reaction_id: str


@dataclass(frozen=True, slots=True)
class InvalidUserReaction:
    lecture_id: str
    reaction_id: str
