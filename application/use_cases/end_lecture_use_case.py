# 仕様: docs/spec/application.md#end_lecture
from dataclasses import dataclass

from application.dtos.end_lecture_request import EndLectureRequest
from application.dtos.end_lecture_response import EndLectureResponse
from application.errors import LectureAlreadyClosed, LectureNotFound
from application.errors.use_case_errors import EndLectureError
from application.ports.lecture_repository import LectureRepository
from application.ports.mappers import to_persistence_failed
from application.result import Err, Ok, Result

_USE_CASE = "end_lecture"


@dataclass(frozen=True, slots=True)
class EndLectureUseCase:
    _lecture_repository: LectureRepository

    def execute(
        self,
        request: EndLectureRequest,
    ) -> Result[EndLectureResponse, EndLectureError]:
        validation = request.validate()
        if validation.is_err():
            return Err(validation.error)

        load_result = self._lecture_repository.find_by_id(request.lecture_id)
        if load_result.is_err():
            return Err(to_persistence_failed(_USE_CASE, load_result.error))
        lecture = load_result.value
        if lecture is None:
            return Err(LectureNotFound(lecture_id=request.lecture_id))

        try:
            lecture.close()
        except ValueError:
            return Err(LectureAlreadyClosed(lecture_id=request.lecture_id))

        save_result = self._lecture_repository.save(lecture)
        if save_result.is_err():
            return Err(to_persistence_failed(_USE_CASE, save_result.error))

        return Ok(
            EndLectureResponse(
                lecture_id=request.lecture_id,
                ended_at=lecture.ended_at,
            )
        )
