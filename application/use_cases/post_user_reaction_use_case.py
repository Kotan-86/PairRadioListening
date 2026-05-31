# 仕様: docs/spec/application.md#post_user_reaction
from dataclasses import dataclass

from application.dtos.post_user_reaction_request import PostUserReactionRequest
from application.dtos.post_user_reaction_response import PostUserReactionResponse
from application.errors import (
    InvalidRequest,
    LectureClosed,
    LectureNotFound,
    ReplyTargetNotFound,
    TimelineNotEstablished,
)
from application.errors.use_case_errors import PostUserReactionError
from application.ports.lecture_repository import LectureRepository
from application.ports.mappers import to_persistence_failed
from application.ports.reaction_repository import ReactionRepository
from application.result import Err, Ok, Result
from domain.entities.reaction import Reaction
from domain.value_objects.audio_data import AudioData
from domain.value_objects.dialogue_speaker import DialogueSpeaker

_USE_CASE = "post_user_reaction"


@dataclass(frozen=True, slots=True)
class PostUserReactionUseCase:
    _lecture_repository: LectureRepository
    _reaction_repository: ReactionRepository

    def execute(
        self,
        request: PostUserReactionRequest,
    ) -> Result[PostUserReactionResponse, PostUserReactionError]:
        validation = request.validate()
        if validation.is_err():
            return Err(validation.error)

        load_result = self._lecture_repository.find_by_id(request.lecture_id)
        if load_result.is_err():
            return Err(to_persistence_failed(_USE_CASE, load_result.error))
        lecture = load_result.value
        if lecture is None:
            return Err(LectureNotFound(lecture_id=request.lecture_id))
        if lecture.status == "closed":
            return Err(LectureClosed(lecture_id=request.lecture_id))
        if lecture.started_at is None or not lecture.utterances:
            return Err(TimelineNotEstablished(lecture_id=request.lecture_id))

        target_check = self._verify_reply_target(request)
        if target_check.is_err():
            return Err(target_check.error)

        try:
            reaction = Reaction(
                lecture_id=request.lecture_id,
                speaker=DialogueSpeaker(
                    role="user",
                    display_name=request.speaker_display_name,
                ),
                reply_target=request.reply_target,
                lecture_time_anchor=request.lecture_time_anchor,
                reaction_text=request.reaction_text,
                audio_data=AudioData.empty(),
                created_at=request.lecture_time_anchor.time_range.start_ms,
            )
        except ValueError as exc:
            return Err(
                InvalidRequest(
                    use_case=_USE_CASE,
                    reason=str(exc),
                )
            )

        save_result = self._reaction_repository.save(reaction)
        if save_result.is_err():
            return Err(to_persistence_failed(_USE_CASE, save_result.error))

        return Ok(
            PostUserReactionResponse(
                reaction_id=str(reaction.id),
                lecture_id=request.lecture_id,
            )
        )

    def _verify_reply_target(
        self,
        request: PostUserReactionRequest,
    ) -> Result[None, ReplyTargetNotFound]:
        if request.reply_target.reply_target_kind == "utterance":
            load_result = self._lecture_repository.find_by_id(request.lecture_id)
            if load_result.is_err() or load_result.value is None:
                return Err(
                    ReplyTargetNotFound(
                        lecture_id=request.lecture_id,
                        reply_target_kind="utterance",
                        reply_target_id=str(request.reply_target.reply_target_id),
                    )
                )
            lecture = load_result.value
            if lecture.find_utterance_by_id(request.reply_target.reply_target_id) is None:
                return Err(
                    ReplyTargetNotFound(
                        lecture_id=request.lecture_id,
                        reply_target_kind="utterance",
                        reply_target_id=str(request.reply_target.reply_target_id),
                    )
                )
            return Ok(None)

        find_result = self._reaction_repository.find_by_id(
            request.lecture_id,
            request.reply_target.reply_target_id,
        )
        if find_result.is_err():
            return Err(
                ReplyTargetNotFound(
                    lecture_id=request.lecture_id,
                    reply_target_kind="reaction",
                    reply_target_id=str(request.reply_target.reply_target_id),
                )
            )
        if find_result.value is None:
            return Err(
                ReplyTargetNotFound(
                    lecture_id=request.lecture_id,
                    reply_target_kind="reaction",
                    reply_target_id=str(request.reply_target.reply_target_id),
                )
            )
        return Ok(None)
