# 仕様: docs/spec/application.md#実装方針（ポート Outbound）
from application.errors import (
    AiPolicyGenerationFailed,
    AiTextGenerationFailed,
    PersistenceFailed,
)
from application.errors.ai import AiTrigger
from application.ports.errors import PersistencePortError, ReactionTextPortError


def to_persistence_failed(use_case: str, port_error: PersistencePortError) -> PersistenceFailed:
    """ポート層の永続化失敗をアプリケーションエラーに変換する。"""
    return PersistenceFailed(
        use_case=use_case,
        operation=port_error.operation,
        resource=port_error.resource,
    )


def to_ai_policy_generation_failed(
    lecture_id: str,
    trigger: AiTrigger,
    source_id: str,
    persona_id: str | None = None,
) -> AiPolicyGenerationFailed:
    return AiPolicyGenerationFailed(
        lecture_id=lecture_id,
        trigger=trigger,
        source_id=source_id,
        persona_id=persona_id,
    )


def to_ai_text_generation_failed(
    lecture_id: str,
    trigger: AiTrigger,
    source_id: str,
    port_error: ReactionTextPortError,
) -> AiTextGenerationFailed:
    return AiTextGenerationFailed(
        lecture_id=lecture_id,
        trigger=trigger,
        source_id=source_id,
        persona_id=port_error.persona_id,
    )
