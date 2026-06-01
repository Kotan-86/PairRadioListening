# 仕様: docs/spec/interface.md#3.4
from application.errors import (
    InvalidPersonaProfiles,
    InvalidRequest,
    InvalidUserReaction,
    LectureAlreadyClosed,
    LectureClosed,
    LectureNotFound,
    PersistenceFailed,
    ReactionNotFound,
    ReplyTargetNotFound,
    TimelineNotEstablished,
    UtteranceNotFound,
)
from application.errors.ai import (
    AiAnalysisFailed,
    AiPolicyGenerationFailed,
    AiReactionBatchIncomplete,
    AiTextGenerationFailed,
)

_ERROR_KINDS: dict[type[object], str] = {
    InvalidRequest: "invalid_request",
    InvalidPersonaProfiles: "invalid_persona_profiles",
    PersistenceFailed: "persistence_failed",
    LectureNotFound: "lecture_not_found",
    LectureClosed: "lecture_closed",
    LectureAlreadyClosed: "lecture_already_closed",
    TimelineNotEstablished: "timeline_not_established",
    ReplyTargetNotFound: "reply_target_not_found",
    ReactionNotFound: "reaction_not_found",
    InvalidUserReaction: "invalid_user_reaction",
    UtteranceNotFound: "utterance_not_found",
    AiPolicyGenerationFailed: "ai_policy_generation_failed",
    AiTextGenerationFailed: "ai_text_generation_failed",
    AiAnalysisFailed: "ai_analysis_failed",
    AiReactionBatchIncomplete: "ai_reaction_batch_incomplete",
}


def error_kind_for(error: object) -> str:
    for error_type, kind in _ERROR_KINDS.items():
        if isinstance(error, error_type):
            return kind
    return "unknown_error"
