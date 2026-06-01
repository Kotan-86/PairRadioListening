# 仕様: docs/spec/application.md#generate_ai_reactions_for_utterance
from dataclasses import dataclass

from application.dtos.generate_ai_reactions_for_utterance_request import (
    GenerateAiReactionsForUtteranceRequest,
)
from application.dtos.generate_ai_reactions_for_utterance_response import (
    GenerateAiReactionsForUtteranceResponse,
)
from application.errors import (
    LectureClosed,
    LectureNotFound,
    UtteranceNotFound,
)
from application.errors.use_case_errors import GenerateAiReactionsForUtteranceError
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
from domain.services.lecturer_reaction_generator import LecturerReactionGenerator
from domain.value_objects.audio_data import AudioData
from domain.value_objects.dialogue_speaker import DialogueSpeaker
from domain.value_objects.lecture_time_anchor import LectureTimeAnchor
from domain.value_objects.reaction_text import ReactionText
from domain.value_objects.reply_target import ReplyTarget

_USE_CASE = "generate_ai_reactions_for_utterance"


@dataclass(frozen=True, slots=True)
class GenerateAiReactionsForUtteranceUseCase:
    _lecture_repository: LectureRepository
    _reaction_repository: ReactionRepository
    _reaction_text_generator: ReactionTextGeneratorPort
    _lecturer_reaction_generator: LecturerReactionGenerator

    def execute(
        self,
        request: GenerateAiReactionsForUtteranceRequest,
    ) -> Result[GenerateAiReactionsForUtteranceResponse, GenerateAiReactionsForUtteranceError]:
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

        utterance = lecture.find_utterance_by_id(request.utterance_id)
        if utterance is None:
            return Err(
                UtteranceNotFound(
                    lecture_id=request.lecture_id,
                    utterance_id=request.utterance_id,
                )
            )

        persona = lecture.persona_profiles[0]

        try:
            policy = self._lecturer_reaction_generator.generate_policy(
                utterance=utterance,
                persona=persona,
            )
        except (ValueError, RuntimeError):
            return Err(
                to_ai_policy_generation_failed(
                    lecture_id=request.lecture_id,
                    trigger="utterance",
                    source_id=request.utterance_id,
                )
            )

        text_result = self._reaction_text_generator.generate_for_lecturer_reaction(
            policy=policy,
            utterance=utterance,
            persona=persona,
        )
        if text_result.is_err():
            return Err(
                to_ai_text_generation_failed(
                    lecture_id=request.lecture_id,
                    trigger="utterance",
                    source_id=request.utterance_id,
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
                    reply_target_kind="utterance",
                    reply_target_id=str(utterance.id),
                ),
                lecture_time_anchor=LectureTimeAnchor.from_utterance(
                    utterance_id=str(utterance.id),
                    time_range=utterance.time_range,
                ),
                reaction_text=ReactionText(text=text_result.value),
                audio_data=AudioData.empty(),
                dialogue_sequence=dialogue_sequence,
            )
        except ValueError:
            return Err(
                to_ai_policy_generation_failed(
                    lecture_id=request.lecture_id,
                    trigger="utterance",
                    source_id=request.utterance_id,
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
            GenerateAiReactionsForUtteranceResponse(
                lecture_id=request.lecture_id,
                utterance_id=request.utterance_id,
                reaction_id=str(reaction.id),
            )
        )
