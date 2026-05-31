# 仕様: docs/spec/application.md#record_utterance
from dataclasses import dataclass, field

from application.dtos.record_utterance_request import RecordUtteranceRequest
from application.errors import InvalidRequest, LectureClosed, LectureNotFound, PersistenceFailed
from application.ports.errors import PersistencePortError
from application.result import Err, Ok, Result
from application.use_cases.record_utterance_use_case import RecordUtteranceUseCase
from domain.entities.lecture import Lecture
from domain.value_objects.ai_persona_profile import AiPersonaProfile
from domain.value_objects.recording_speaker import RecordingSpeaker
from domain.value_objects.speech_text import SpeechText
from domain.value_objects.time_range import TimeRange


@dataclass
class StubLectureRepository:
    saved: list[Lecture] = field(default_factory=list)
    fail_on_save: bool = False
    fail_on_load: bool = False
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
        if self.fail_on_load:
            return Err(
                PersistencePortError(
                    operation="load",
                    resource="lecture",
                    reason="load failed",
                )
            )
        return Ok(self.by_id.get(str(lecture_id)))


def _lecture(lecture_id: str = "lecture-1") -> Lecture:
    return Lecture(
        id=lecture_id,
        title="講義",
        persona_profiles=[
            AiPersonaProfile(
                id="persona-1",
                display_name="AI",
                persona_prompt="prompt",
            )
        ],
    )


def _request(
    lecture_id: str = "lecture-1",
    utterance_id: str = "utterance-1",
    time_range: TimeRange | None = None,
) -> RecordUtteranceRequest:
    return RecordUtteranceRequest(
        lecture_id=lecture_id,
        utterance_id=utterance_id,
        time_range=time_range or TimeRange(start_ms=1000, end_ms=2000),
        speech_text=SpeechText(text="こんにちは"),
        speaker=RecordingSpeaker(display_name="講師"),
    )


def test_record_utterance_succeeds_and_establishes_timeline():
    repository = StubLectureRepository()
    repository.by_id["lecture-1"] = _lecture()
    use_case = RecordUtteranceUseCase(_lecture_repository=repository)

    result = use_case.execute(_request())

    assert result.is_ok()
    lecture = repository.by_id["lecture-1"]
    assert lecture.started_at == 0
    assert len(lecture.utterances) == 1
    assert lecture.utterances[0].time_range.start_ms == 0
    assert lecture.utterances[0].time_range.end_ms == 1000
    assert result.value.utterance_id == "utterance-1"


def test_record_utterance_upserts_same_id():
    repository = StubLectureRepository()
    lecture = _lecture()
    repository.by_id["lecture-1"] = lecture
    use_case = RecordUtteranceUseCase(_lecture_repository=repository)
    use_case.execute(_request(time_range=TimeRange(start_ms=0, end_ms=500)))

    result = use_case.execute(
        RecordUtteranceRequest(
            lecture_id="lecture-1",
            utterance_id="utterance-1",
            time_range=TimeRange(start_ms=0, end_ms=900),
            speech_text=SpeechText(text="更新"),
            speaker=RecordingSpeaker(display_name="講師"),
        )
    )

    assert result.is_ok()
    assert len(repository.by_id["lecture-1"].utterances) == 1
    assert repository.by_id["lecture-1"].utterances[0].speech_text.text == "更新"


def test_record_utterance_fails_when_invalid_request():
    repository = StubLectureRepository()
    use_case = RecordUtteranceUseCase(_lecture_repository=repository)

    result = use_case.execute(_request(lecture_id=""))

    assert result.is_err()
    assert isinstance(result.error, InvalidRequest)


def test_record_utterance_fails_when_lecture_not_found():
    repository = StubLectureRepository()
    use_case = RecordUtteranceUseCase(_lecture_repository=repository)

    result = use_case.execute(_request())

    assert result.is_err()
    assert isinstance(result.error, LectureNotFound)


def test_record_utterance_fails_when_lecture_closed():
    repository = StubLectureRepository()
    lecture = _lecture()
    lecture.close()
    repository.by_id["lecture-1"] = lecture
    use_case = RecordUtteranceUseCase(_lecture_repository=repository)

    result = use_case.execute(_request(time_range=TimeRange(start_ms=0, end_ms=500)))

    assert result.is_err()
    assert isinstance(result.error, LectureClosed)


def test_record_utterance_fails_when_persistence_fails():
    repository = StubLectureRepository(fail_on_save=True)
    repository.by_id["lecture-1"] = _lecture()
    use_case = RecordUtteranceUseCase(_lecture_repository=repository)

    result = use_case.execute(_request(time_range=TimeRange(start_ms=0, end_ms=500)))

    assert result.is_err()
    assert isinstance(result.error, PersistenceFailed)
