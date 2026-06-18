# 仕様: docs/spec/application.md#generate_ai_replies_for_user_reaction
from dataclasses import dataclass

from application.dtos.generate_ai_replies_for_user_reaction_request import (
    GenerateAiRepliesForUserReactionRequest,
)
from application.dtos.generate_ai_replies_for_user_reaction_response import (
    GenerateAiRepliesForUserReactionResponse,
)
from application.errors import (
    InvalidUserReaction,
    LectureClosed,
    LectureNotFound,
    ReactionNotFound,
    ReplyTargetNotFound,
)
from application.errors.use_case_errors import GenerateAiRepliesForUserReactionError
from application.ports.lecture_repository import LectureRepository
from application.ports.mappers import (
    to_ai_policy_generation_failed,
    to_ai_text_generation_failed,
    to_persistence_failed,
)
from application.ports.reaction_repository import ReactionRepository
from application.ports.reaction_text_generator import ReactionTextGeneratorPort
from application.result import Err, Ok, Result
from application.services.build_lecture_llm_context import build_lecture_llm_context
from application.services.build_reply_target_focus import build_reply_target_focus
from domain.entities.reaction import Reaction
from domain.services.user_reaction_responder import UserReactionResponder
from domain.value_objects.audio_data import AudioData
from domain.value_objects.dialogue_speaker import DialogueSpeaker
from domain.value_objects.reaction_text import ReactionText
from domain.value_objects.reply_target import ReplyTarget

_USE_CASE = "generate_ai_replies_for_user_reaction"


@dataclass(frozen=True, slots=True)
class GenerateAiRepliesForUserReactionUseCase:
    _lecture_repository: LectureRepository
    _reaction_repository: ReactionRepository
    _reaction_text_generator: ReactionTextGeneratorPort
    _user_reaction_responder: UserReactionResponder

    def execute(
        self,
        request: GenerateAiRepliesForUserReactionRequest,
    ) -> Result[GenerateAiRepliesForUserReactionResponse, GenerateAiRepliesForUserReactionError]:
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

        reaction_result = self._reaction_repository.find_by_id(
            request.lecture_id,
            request.reaction_id,
        )
        if reaction_result.is_err():
            return Err(to_persistence_failed(_USE_CASE, reaction_result.error))
        user_reaction = reaction_result.value
        if user_reaction is None:
            return Err(
                ReactionNotFound(
                    lecture_id=request.lecture_id,
                    reaction_id=request.reaction_id,
                )
            )
        if user_reaction.speaker.role != "user":
            return Err(
                InvalidUserReaction(
                    lecture_id=request.lecture_id,
                    reaction_id=request.reaction_id,
                )
            )

        persona = lecture.persona_profiles[0]

        lecture_llm_context = build_lecture_llm_context(lecture, user_reaction)

        target_reaction: Reaction | None = None
        if user_reaction.reply_target.reply_target_kind == "reaction":
            target_result = self._reaction_repository.find_by_id(
                request.lecture_id,
                user_reaction.reply_target.reply_target_id,
            )
            if target_result.is_err():
                return Err(to_persistence_failed(_USE_CASE, target_result.error))
            target_reaction = target_result.value

        reply_target_focus = build_reply_target_focus(
            lecture,
            user_reaction,
            target_reaction=target_reaction,
        )
        if reply_target_focus is None:
            return Err(
                ReplyTargetNotFound(
                    lecture_id=request.lecture_id,
                    reply_target_kind=user_reaction.reply_target.reply_target_kind,
                    reply_target_id=user_reaction.reply_target.reply_target_id,
                )
            )

        try:
            policy = self._user_reaction_responder.determine_policy(
                reaction=user_reaction,
                persona=persona,
                lecture_llm_context=lecture_llm_context,
                reply_target_focus=reply_target_focus,
            )
        except (ValueError, RuntimeError):
            return Err(
                to_ai_policy_generation_failed(
                    lecture_id=request.lecture_id,
                    trigger="user_reaction",
                    source_id=request.reaction_id,
                )
            )

        text_result = self._reaction_text_generator.generate_for_user_reaction_reply(
            policy=policy,
            reaction=user_reaction,
            persona=persona,
            lecture_llm_context=lecture_llm_context,
            reply_target_focus=reply_target_focus,
        )
        if text_result.is_err():
            return Err(
                to_ai_text_generation_failed(
                    lecture_id=request.lecture_id,
                    trigger="user_reaction",
                    source_id=request.reaction_id,
                    port_error=text_result.error,
                )
            )

        try:
            dialogue_sequence = lecture.allocate_dialogue_sequence()
            reaction = Reaction(
                lecture_id=request.lecture_id,
                speaker=DialogueSpeaker(
                    role="ai",
                    display_name=persona.display_name,
                    persona_id=persona.id,
                ),
                reply_target=ReplyTarget(
                    reply_target_kind="reaction",
                    reply_target_id=str(user_reaction.id),
                ),
                lecture_time_anchor=user_reaction.lecture_time_anchor,
                reaction_text=ReactionText(text=text_result.value),
                audio_data=AudioData.empty(),
                dialogue_sequence=dialogue_sequence,
            )
        except ValueError:
            return Err(
                to_ai_policy_generation_failed(
                    lecture_id=request.lecture_id,
                    trigger="user_reaction",
                    source_id=request.reaction_id,
                    persona_id=str(persona.id),
                )
            )

        save_result = self._reaction_repository.save(reaction)
        if save_result.is_err():
            return Err(to_persistence_failed(_USE_CASE, save_result.error))

        lecture_save_result = self._lecture_repository.save(lecture)
        if lecture_save_result.is_err():
            return Err(to_persistence_failed(_USE_CASE, lecture_save_result.error))

        return Ok(
            GenerateAiRepliesForUserReactionResponse(
                lecture_id=request.lecture_id,
                user_reaction_id=request.reaction_id,
                reaction_id=str(reaction.id),
            )
        )
