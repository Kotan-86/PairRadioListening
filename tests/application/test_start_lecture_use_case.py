# 仕様: docs/spec/application.md#start_lecture
from dataclasses import dataclass, field

from application.dtos.start_lecture_request import StartLectureRequest
from application.errors import InvalidPersonaProfiles, PersistenceFailed
from application.ports.errors import PersistencePortError
from application.result import Err, Ok, Result
from application.use_cases.start_lecture_use_case import StartLectureUseCase
from domain.entities.lecture import Lecture
from domain.value_objects.ai_persona_profile import AiPersonaProfile


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


def _persona() -> AiPersonaProfile:
    return AiPersonaProfile(
        id="persona-1",
        display_name="AI 太郎",
        persona_prompt="好奇心旺盛な聞き手",
    )


def test_start_lecture_succeeds_and_persists_lecture():
    repository = StubLectureRepository()
    use_case = StartLectureUseCase(_lecture_repository=repository)
    persona = _persona()
    request = StartLectureRequest.from_fields(
        persona_profiles=[persona],
        title="テスト講義",
    )

    result = use_case.execute(request)

    assert result.is_ok()
    assert isinstance(result.value.lecture_id, str)
    assert result.value.lecture_id not in ("", "None")
    assert len(repository.saved) == 1
    lecture = repository.saved[0]
    assert lecture.id is not None
    assert lecture.title == "テスト講義"
    assert lecture.status == "active"
    assert lecture.started_at is None
    assert lecture.ended_at == 0
    assert lecture.persona_profiles == [persona]
    assert result.value.lecture_id == str(lecture.id)


def test_start_lecture_fails_when_persona_profiles_more_than_one():
    repository = StubLectureRepository()
    use_case = StartLectureUseCase(_lecture_repository=repository)
    request = StartLectureRequest.from_fields(
        persona_profiles=[_persona(), _persona()],
    )

    result = use_case.execute(request)

    assert result.is_err()
    assert isinstance(result.error, InvalidPersonaProfiles)
    assert repository.saved == []


def test_start_lecture_fails_when_persona_profiles_empty():
    repository = StubLectureRepository()
    use_case = StartLectureUseCase(_lecture_repository=repository)
    request = StartLectureRequest.from_fields(persona_profiles=[])

    result = use_case.execute(request)

    assert result.is_err()
    assert isinstance(result.error, InvalidPersonaProfiles)
    assert repository.saved == []


def test_start_lecture_fails_when_persistence_fails():
    repository = StubLectureRepository(fail_on_save=True)
    use_case = StartLectureUseCase(_lecture_repository=repository)
    request = StartLectureRequest.from_fields(persona_profiles=[_persona()])

    result = use_case.execute(request)

    assert result.is_err()
    assert isinstance(result.error, PersistenceFailed)
    assert result.error.use_case == "start_lecture"
    assert result.error.operation == "save"
    assert repository.saved == []
