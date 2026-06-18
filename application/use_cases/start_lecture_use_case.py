# 仕様: docs/spec/application.md#start_lecture
from dataclasses import dataclass

from application.dtos.start_lecture_request import StartLectureRequest
from application.dtos.start_lecture_response import StartLectureResponse
from application.errors import InvalidPersonaProfiles
from application.errors.use_case_errors import StartLectureError
from application.ports.lecture_repository import LectureRepository
from application.ports.mappers import to_persistence_failed
from application.result import Err, Ok, Result
from domain.entities.lecture import Lecture

_USE_CASE = "start_lecture"


@dataclass(frozen=True, slots=True)
class StartLectureUseCase:
    _lecture_repository: LectureRepository

    def execute(
        self,
        request: StartLectureRequest,
    ) -> Result[StartLectureResponse, StartLectureError]:
        validation = request.validate()
        if validation.is_err():
            return Err(validation.error)

        try:
            lecture = Lecture(
                title=request.title,
                persona_profiles=list(request.persona_profiles),
            )
        except ValueError as exc:
            return Err(InvalidPersonaProfiles(reason=str(exc)))

        save_result = self._lecture_repository.save(lecture)
        if save_result.is_err():
            return Err(to_persistence_failed(_USE_CASE, save_result.error))

        return Ok(StartLectureResponse(lecture_id=str(lecture.id)))
