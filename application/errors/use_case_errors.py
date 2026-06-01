# 仕様: docs/spec/application.md#ユースケース別-Error-型
from application.errors.ai import (
    AiAnalysisFailed,
    AiPolicyGenerationFailed,
    AiReactionBatchIncomplete,
    AiTextGenerationFailed,
)
from application.errors.common import (
    InvalidRequest,
    LectureAlreadyClosed,
    LectureClosed,
    LectureNotFound,
    PersistenceFailed,
)
from application.errors.lecture import InvalidPersonaProfiles, UtteranceNotFound
from application.errors.timeline import (
    InvalidUserReaction,
    ReactionNotFound,
    ReplyTargetNotFound,
    TimelineNotEstablished,
)

StartLectureError = InvalidRequest | InvalidPersonaProfiles | PersistenceFailed

RecordUtteranceError = (
    InvalidRequest | LectureNotFound | LectureClosed | PersistenceFailed
)

PostUserReactionError = (
    InvalidRequest
    | LectureNotFound
    | LectureClosed
    | TimelineNotEstablished
    | ReplyTargetNotFound
    | PersistenceFailed
)

GenerateAiReactionsForUtteranceError = (
    InvalidRequest
    | LectureNotFound
    | LectureClosed
    | UtteranceNotFound
    | AiPolicyGenerationFailed
    | AiTextGenerationFailed
    | PersistenceFailed
)

GenerateAiRepliesForUserReactionError = (
    InvalidRequest
    | LectureNotFound
    | LectureClosed
    | ReactionNotFound
    | InvalidUserReaction
    | AiPolicyGenerationFailed
    | AiTextGenerationFailed
    | PersistenceFailed
)

GetTranscriptError = InvalidRequest | LectureNotFound | PersistenceFailed

GetDialogueError = InvalidRequest | LectureNotFound | PersistenceFailed

EndLectureError = (
    InvalidRequest | LectureNotFound | LectureAlreadyClosed | PersistenceFailed
)
