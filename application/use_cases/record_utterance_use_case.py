# 仕様: docs/spec/application.md#record_utterance
from dataclasses import dataclass

from application.dtos.record_utterance_request import RecordUtteranceRequest
from application.dtos.record_utterance_response import RecordUtteranceResponse
from application.errors import InvalidRequest, LectureClosed, LectureNotFound
from application.errors.use_case_errors import RecordUtteranceError
from application.ports.lecture_repository import LectureRepository
from application.ports.mappers import to_persistence_failed
from application.result import Err, Ok, Result
from domain.entities.lecture import Lecture
from domain.entities.utterance import Utterance

_USE_CASE = "record_utterance"


@dataclass(frozen=True, slots=True)
class RecordUtteranceUseCase:
    _lecture_repository: LectureRepository

    def execute(
        self,
        request: RecordUtteranceRequest,
    ) -> Result[RecordUtteranceResponse, RecordUtteranceError]:
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

        time_range = request.time_range
        if lecture.started_at is None and not lecture.utterances:
            time_range = Lecture.normalize_time_range_for_first_utterance(time_range)

        try:
            utterance = Utterance(
                id=request.utterance_id,
                time_range=time_range,
                speech_text=request.speech_text,
                speaker=request.speaker,
            )
        except ValueError as exc:
            return Err(
                InvalidRequest(
                    use_case=_USE_CASE,
                    reason=str(exc),
                )
            )

        try:
            lecture.upsert_utterance(utterance)
        except ValueError as exc:
            return Err(LectureClosed(lecture_id=request.lecture_id))

        save_result = self._lecture_repository.save(lecture)
        if save_result.is_err():
            return Err(to_persistence_failed(_USE_CASE, save_result.error))

        return Ok(
            RecordUtteranceResponse(
                utterance_id=str(utterance.id),
                lecture_id=request.lecture_id,
            )
        )
