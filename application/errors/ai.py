# 仕様: docs/spec/application.md#AI-生成・外部サービス
from dataclasses import dataclass
from typing import Literal

AiTrigger = Literal["utterance", "user_reaction"]


@dataclass(frozen=True, slots=True)
class AiPolicyGenerationFailed:
    lecture_id: str
    trigger: AiTrigger
    source_id: str
    persona_id: str | None = None


@dataclass(frozen=True, slots=True)
class AiTextGenerationFailed:
    lecture_id: str
    trigger: AiTrigger
    source_id: str
    persona_id: str | None = None


@dataclass(frozen=True, slots=True)
class AiAnalysisFailed:
    lecture_id: str
    reaction_id: str


@dataclass(frozen=True, slots=True)
class AiReactionBatchIncomplete:
    lecture_id: str
    expected_count: int
    succeeded_count: int
