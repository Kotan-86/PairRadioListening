# 仕様: docs/spec/application.md#実装方針（ポート Outbound）
from dataclasses import dataclass
from typing import Literal

PersistenceOperation = Literal["save", "load"]


@dataclass(frozen=True, slots=True)
class PersistencePortError:
    """永続化ポートの失敗。アプリケーションエラー（PersistenceFailed）へはユースケースが変換する。"""

    operation: PersistenceOperation
    resource: str
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class ReactionTextPortError:
    """本文生成ポートの失敗。アプリケーションエラー（AiTextGenerationFailed）へは UC が変換する。"""

    persona_id: str | None = None
    reason: str | None = None
