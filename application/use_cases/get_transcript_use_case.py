# 仕様: docs/spec/application.md#get_transcript
from dataclasses import dataclass

from application.dtos.transcript_item import (
    GetTranscriptRequest,
    GetTranscriptResponse,
    TranscriptItem,
)
from application.errors import LectureNotFound
from application.errors.use_case_errors import GetTranscriptError
from application.ports.lecture_repository import LectureRepository
from application.ports.mappers import to_persistence_failed
from application.result import Err, Ok, Result

_USE_CASE = "get_transcript"


@dataclass(frozen=True, slots=True)
class GetTranscriptUseCase:
    _lecture_repository: LectureRepository

    def execute(
        self,
        request: GetTranscriptRequest,
    ) -> Result[GetTranscriptResponse, GetTranscriptError]:
        validation = request.validate()
        if validation.is_err():
            return Err(validation.error)

        load_result = self._lecture_repository.find_by_id(request.lecture_id)
        if load_result.is_err():
            return Err(to_persistence_failed(_USE_CASE, load_result.error))
        lecture = load_result.value
        if lecture is None:
            return Err(LectureNotFound(lecture_id=request.lecture_id))

        sorted_utterances = sorted(
            lecture.utterances,
            key=lambda utterance: utterance.time_range.start_ms,
        )
        items = tuple(
            TranscriptItem(
                utterance_id=str(utterance.id),
                time_range=utterance.time_range,
                speech_text=utterance.speech_text,
                speaker=utterance.speaker,
            )
            for utterance in sorted_utterances
        )

        return Ok(
            GetTranscriptResponse(
                lecture_id=request.lecture_id,
                items=items,
            )
        )
