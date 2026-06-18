# 仕様: docs/spec/application.md#end_lecture
from dataclasses import dataclass, field

from application.dtos.end_lecture_request import EndLectureRequest
from application.errors import (
    InvalidRequest,
    LectureAlreadyClosed,
    LectureNotFound,
    PersistenceFailed,
)
from application.ports.errors import PersistencePortError
from application.result import Err, Ok, Result
from application.use_cases.end_lecture_use_case import EndLectureUseCase
from domain.entities.lecture import Lecture
from domain.entities.utterance import Utterance
from domain.value_objects.ai_persona_profile import AiPersonaProfile
from domain.value_objects.recording_speaker import RecordingSpeaker
from domain.value_objects.speech_text import SpeechText
from domain.value_objects.time_range import TimeRange


@dataclass
class StubLectureRepository:
    saved: list[Lecture] = field(default_factory=list)
    fail_on_save: bool = False
    by_id: dict[str, Lecture] = field(default_factory=dict)

    def save(self, lecture: Lecture) -> Result[None, PersistencePortError]:
        if self.fail_on_save:
            return Err(
                PersistencePortError(
                    operation="save",
                    resource="lecture",
                    reason="save failed",
                )
            )
        self.saved.append(lecture)
        self.by_id[str(lecture.id)] = lecture
        return Ok(None)

    def find_by_id(self, lecture_id: str) -> Result[Lecture | None, PersistencePortError]:
        return Ok(self.by_id.get(str(lecture_id)))


def _active_lecture() -> Lecture:
    lecture = Lecture(
        id="lecture-1",
        title="講義",
        persona_profiles=[
            AiPersonaProfile(id="p1", display_name="AI", persona_prompt="prompt")
        ],
        started_at=0,
    )
    lecture.add_utterance(
        Utterance(
            id="u1",
            time_range=TimeRange(start_ms=0, end_ms=3000),
            speech_text=SpeechText(text="本日は"),
            speaker=RecordingSpeaker(display_name="講師"),
        )
    )
    return lecture


def test_end_lecture_succeeds():
    repository = StubLectureRepository()
    repository.by_id["lecture-1"] = _active_lecture()
    use_case = EndLectureUseCase(_lecture_repository=repository)

    result = use_case.execute(EndLectureRequest(lecture_id="lecture-1"))

    assert result.is_ok()
    assert result.value.ended_at == 3000
    assert repository.by_id["lecture-1"].status == "closed"


def test_end_lecture_fails_when_invalid_request():
    repository = StubLectureRepository()
    use_case = EndLectureUseCase(_lecture_repository=repository)

    result = use_case.execute(EndLectureRequest(lecture_id=""))

    assert result.is_err()
    assert isinstance(result.error, InvalidRequest)


def test_end_lecture_fails_when_lecture_not_found():
    repository = StubLectureRepository()
    use_case = EndLectureUseCase(_lecture_repository=repository)

    result = use_case.execute(EndLectureRequest(lecture_id="missing"))

    assert result.is_err()
    assert isinstance(result.error, LectureNotFound)


def test_end_lecture_fails_when_already_closed():
    repository = StubLectureRepository()
    lecture = _active_lecture()
    lecture.close()
    repository.by_id["lecture-1"] = lecture
    use_case = EndLectureUseCase(_lecture_repository=repository)

    result = use_case.execute(EndLectureRequest(lecture_id="lecture-1"))

    assert result.is_err()
    assert isinstance(result.error, LectureAlreadyClosed)


def test_end_lecture_fails_when_persistence_fails():
    repository = StubLectureRepository(fail_on_save=True)
    repository.by_id["lecture-1"] = _active_lecture()
    use_case = EndLectureUseCase(_lecture_repository=repository)

    result = use_case.execute(EndLectureRequest(lecture_id="lecture-1"))

    assert result.is_err()
    assert isinstance(result.error, PersistenceFailed)
