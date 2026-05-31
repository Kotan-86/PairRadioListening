# 仕様: docs/spec/application.md#generate_ai_replies_for_user_reaction
from dataclasses import dataclass

from application.dtos.generate_ai_replies_for_user_reaction_request import (
    GenerateAiRepliesForUserReactionRequest,
)
from application.dtos.generate_ai_replies_for_user_reaction_response import (
    GenerateAiRepliesForUserReactionResponse,
)
from application.errors import (
    AiAnalysisFailed,
    AiReactionBatchIncomplete,
    InvalidUserReaction,
    LectureClosed,
    LectureNotFound,
    ReactionNotFound,
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
from domain.entities.reaction import Reaction
from domain.services.user_reaction_analyzer import UserReactionAnalyzer
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
    _user_reaction_analyzer: UserReactionAnalyzer
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

        try:
            analysis = self._user_reaction_analyzer.analyze(user_reaction.reaction_text)
        except (ValueError, RuntimeError):
            return Err(
                AiAnalysisFailed(
                    lecture_id=request.lecture_id,
                    reaction_id=request.reaction_id,
                )
            )

        try:
            policies = self._user_reaction_responder.determine_policies(
                reaction=user_reaction,
                analysis_result=analysis,
                personas=lecture.persona_profiles,
            )
        except (ValueError, RuntimeError):
            return Err(
                to_ai_policy_generation_failed(
                    lecture_id=request.lecture_id,
                    trigger="user_reaction",
                    source_id=request.reaction_id,
                )
            )

        expected_count = len(lecture.persona_profiles)
        if len(policies) != expected_count:
            return Err(
                AiReactionBatchIncomplete(
                    lecture_id=request.lecture_id,
                    expected_count=expected_count,
                    succeeded_count=len(policies),
                )
            )

        reactions_to_save: list[Reaction] = []
        for persona, policy in zip(lecture.persona_profiles, policies, strict=True):
            text_result = self._reaction_text_generator.generate_for_user_reaction_reply(
                policy=policy,
                reaction=user_reaction,
                persona=persona,
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
                    created_at=user_reaction.created_at,
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
            reactions_to_save.append(reaction)

        saved_ids: list[str] = []
        for reaction in reactions_to_save:
            save_result = self._reaction_repository.save(reaction)
            if save_result.is_err():
                if saved_ids:
                    return Err(
                        AiReactionBatchIncomplete(
                            lecture_id=request.lecture_id,
                            expected_count=expected_count,
                            succeeded_count=len(saved_ids),
                        )
                    )
                return Err(to_persistence_failed(_USE_CASE, save_result.error))
            saved_ids.append(str(reaction.id))

        return Ok(
            GenerateAiRepliesForUserReactionResponse(
                lecture_id=request.lecture_id,
                user_reaction_id=request.reaction_id,
                reaction_ids=tuple(saved_ids),
            )
        )
