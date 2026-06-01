# 仕様: docs/spec/application.md#get_transcript
from dataclasses import dataclass, field

from application.dtos.transcript_item import GetTranscriptRequest
from application.errors import InvalidRequest, LectureNotFound, PersistenceFailed
from application.ports.errors import PersistencePortError
from application.result import Err, Ok, Result
from application.use_cases.get_transcript_use_case import GetTranscriptUseCase
from domain.entities.lecture import Lecture
from domain.entities.utterance import Utterance
from domain.value_objects.ai_persona_profile import AiPersonaProfile
from domain.value_objects.recording_speaker import RecordingSpeaker
from domain.value_objects.speech_text import SpeechText
from domain.value_objects.time_range import TimeRange


@dataclass
class StubLectureRepository:
    by_id: dict[str, Lecture] = field(default_factory=dict)
    fail_on_load: bool = False

    def save(self, lecture: Lecture) -> Result[None, PersistencePortError]:
        return Ok(None)

    def find_by_id(self, lecture_id: str) -> Result[Lecture | None, PersistencePortError]:
        if self.fail_on_load:
            return Err(
                PersistencePortError(operation="load", resource="lecture", reason="load failed")
            )
        return Ok(self.by_id.get(str(lecture_id)))


def _lecture_with_utterances() -> Lecture:
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
            id="u2",
            time_range=TimeRange(start_ms=2000, end_ms=3000),
            speech_text=SpeechText(text="後"),
            speaker=RecordingSpeaker(display_name="講師"),
        )
    )
    lecture.add_utterance(
        Utterance(
            id="u1",
            time_range=TimeRange(start_ms=0, end_ms=1000),
            speech_text=SpeechText(text="先"),
            speaker=RecordingSpeaker(display_name="講師"),
        )
    )
    return lecture


def test_get_transcript_returns_utterances_sorted_by_start_ms():
    use_case = GetTranscriptUseCase(
        _lecture_repository=StubLectureRepository(by_id={"lecture-1": _lecture_with_utterances()}),
    )

    result = use_case.execute(GetTranscriptRequest(lecture_id="lecture-1"))

    assert result.is_ok()
    assert len(result.value.items) == 2
    assert result.value.items[0].utterance_id == "u1"
    assert result.value.items[1].utterance_id == "u2"


def test_get_transcript_fails_when_invalid_request():
    use_case = GetTranscriptUseCase(_lecture_repository=StubLectureRepository())

    result = use_case.execute(GetTranscriptRequest(lecture_id=""))

    assert result.is_err()
    assert isinstance(result.error, InvalidRequest)


def test_get_transcript_fails_when_lecture_not_found():
    use_case = GetTranscriptUseCase(_lecture_repository=StubLectureRepository())

    result = use_case.execute(GetTranscriptRequest(lecture_id="missing"))

    assert result.is_err()
    assert isinstance(result.error, LectureNotFound)


def test_get_transcript_fails_when_load_fails():
    use_case = GetTranscriptUseCase(
        _lecture_repository=StubLectureRepository(
            by_id={"lecture-1": _lecture_with_utterances()},
            fail_on_load=True,
        ),
    )

    result = use_case.execute(GetTranscriptRequest(lecture_id="lecture-1"))

    assert result.is_err()
    assert isinstance(result.error, PersistenceFailed)
