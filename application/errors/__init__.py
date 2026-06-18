# 仕様: docs/spec/application.md#4-アプリケーションエラー
from application.errors.ai import (
    AiAnalysisFailed,
    AiPolicyGenerationFailed,
    AiReactionBatchIncomplete,
    AiTextGenerationFailed,
    AiTrigger,
)
from application.errors.common import (
    InvalidRequest,
    LectureAlreadyClosed,
    LectureClosed,
    LectureNotFound,
    PersistenceFailed,
    PersistenceOperation,
)
from application.errors.lecture import InvalidPersonaProfiles, UtteranceNotFound
from application.errors.timeline import (
    InvalidUserReaction,
    ReactionNotFound,
    ReplyTargetKind,
    ReplyTargetNotFound,
    TimelineNotEstablished,
)
from application.errors.use_case_errors import (
    EndLectureError,
    GenerateAiReactionsForUtteranceError,
    GenerateAiRepliesForUserReactionError,
    GetDialogueError,
    GetTranscriptError,
    PostUserReactionError,
    RecordUtteranceError,
    StartLectureError,
)

__all__ = [
    "AiAnalysisFailed",
    "AiPolicyGenerationFailed",
    "AiReactionBatchIncomplete",
    "AiTextGenerationFailed",
    "AiTrigger",
    "EndLectureError",
    "GenerateAiReactionsForUtteranceError",
    "GenerateAiRepliesForUserReactionError",
    "GetDialogueError",
    "GetTranscriptError",
    "InvalidPersonaProfiles",
    "InvalidRequest",
    "InvalidUserReaction",
    "LectureAlreadyClosed",
    "LectureClosed",
    "LectureNotFound",
    "PersistenceFailed",
    "PersistenceOperation",
    "PostUserReactionError",
    "ReactionNotFound",
    "RecordUtteranceError",
    "ReplyTargetKind",
    "ReplyTargetNotFound",
    "StartLectureError",
    "TimelineNotEstablished",
    "UtteranceNotFound",
]
