# 仕様: docs/spec/application.md#get_dialogue
from dataclasses import dataclass

from application.dtos.dialogue_item import (
    DialogueItem,
    GetDialogueRequest,
    GetDialogueResponse,
)
from application.errors import LectureNotFound
from application.errors.use_case_errors import GetDialogueError
from application.ports.lecture_repository import LectureRepository
from application.ports.mappers import to_persistence_failed
from application.ports.reaction_repository import ReactionRepository
from application.result import Err, Ok, Result

_USE_CASE = "get_dialogue"


@dataclass(frozen=True, slots=True)
class GetDialogueUseCase:
    _lecture_repository: LectureRepository
    _reaction_repository: ReactionRepository

    def execute(
        self,
        request: GetDialogueRequest,
    ) -> Result[GetDialogueResponse, GetDialogueError]:
        validation = request.validate()
        if validation.is_err():
            return Err(validation.error)

        load_result = self._lecture_repository.find_by_id(request.lecture_id)
        if load_result.is_err():
            return Err(to_persistence_failed(_USE_CASE, load_result.error))
        lecture = load_result.value
        if lecture is None:
            return Err(LectureNotFound(lecture_id=request.lecture_id))

        reactions_result = self._reaction_repository.list_by_lecture_id(request.lecture_id)
        if reactions_result.is_err():
            return Err(to_persistence_failed(_USE_CASE, reactions_result.error))

        sorted_reactions = sorted(
            reactions_result.value,
            key=lambda reaction: reaction.dialogue_sequence,
        )
        items = tuple(
            DialogueItem(
                reaction_id=str(reaction.id),
                dialogue_sequence=reaction.dialogue_sequence,
                reaction_text=reaction.reaction_text,
                speaker=reaction.speaker,
                reply_target=reaction.reply_target,
                lecture_time_anchor=reaction.lecture_time_anchor,
            )
            for reaction in sorted_reactions
        )

        return Ok(
            GetDialogueResponse(
                lecture_id=request.lecture_id,
                items=items,
            )
        )
