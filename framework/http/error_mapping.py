# 仕様: docs/spec/framework.md#3.1
from __future__ import annotations

from typing import Final

_ERROR_KIND_TO_STATUS: Final[dict[str, int]] = {
    "invalid_request": 400,
    "invalid_persona_profiles": 400,
    "invalid_user_reaction": 400,
    "lecture_not_found": 404,
    "utterance_not_found": 404,
    "reaction_not_found": 404,
    "lecture_closed": 409,
    "lecture_already_closed": 409,
    "timeline_not_established": 409,
    "reply_target_not_found": 409,
    "persistence_failed": 503,
    "ai_policy_generation_failed": 503,
    "ai_text_generation_failed": 503,
    "ai_analysis_failed": 503,
    "ai_reaction_batch_incomplete": 503,
    "unknown_error": 500,
}


def http_status_for_command(*, success: bool, error_kind: str) -> int:
    if success:
        return 200
    return _ERROR_KIND_TO_STATUS.get(error_kind, 500)


def http_status_for_start(*, success: bool, error_kind: str) -> int:
    if success:
        return 201
    return _ERROR_KIND_TO_STATUS.get(error_kind, 500)
