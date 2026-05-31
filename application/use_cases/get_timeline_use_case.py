# 仕様: docs/spec/application.md#get_timeline
from dataclasses import dataclass

from application.dtos.timeline_item import (
    GetTimelineRequest,
    GetTimelineResponse,
    ReactionTimelineItem,
    TimelineItem,
    UtteranceTimelineItem,
)
from application.errors import LectureNotFound
from application.errors.use_case_errors import GetTimelineError
from application.ports.lecture_repository import LectureRepository
from application.ports.mappers import to_persistence_failed
from application.ports.reaction_repository import ReactionRepository
from application.result import Err, Ok, Result

_USE_CASE = "get_timeline"


@dataclass(frozen=True, slots=True)
class GetTimelineUseCase:
    _lecture_repository: LectureRepository
    _reaction_repository: ReactionRepository

    def execute(
        self,
        request: GetTimelineRequest,
    ) -> Result[GetTimelineResponse, GetTimelineError]:
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

        items = self._build_items(lecture.utterances, reactions_result.value)
        sorted_items = tuple(
            sorted(
                items,
                key=lambda item: (
                    item.time_range.start_ms,
                    item.created_at if isinstance(item, ReactionTimelineItem) else 0,
                ),
            )
        )

        return Ok(
            GetTimelineResponse(
                lecture_id=request.lecture_id,
                items=sorted_items,
            )
        )

    @staticmethod
    def _build_items(utterances, reactions) -> list[TimelineItem]:
        items: list[TimelineItem] = []
        for utterance in utterances:
            items.append(
                UtteranceTimelineItem(
                    kind="utterance",
                    time_range=utterance.time_range,
                    utterance_id=str(utterance.id),
                    speech_text=utterance.speech_text,
                    speaker=utterance.speaker,
                )
            )
        for reaction in reactions:
            items.append(
                ReactionTimelineItem(
                    kind="reaction",
                    time_range=reaction.lecture_time_anchor.time_range,
                    reaction_id=str(reaction.id),
                    reaction_text=reaction.reaction_text,
                    speaker=reaction.speaker,
                    reply_target=reaction.reply_target,
                    lecture_time_anchor=reaction.lecture_time_anchor,
                    created_at=reaction.created_at,
                )
            )
        return items
