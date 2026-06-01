# 仕様: docs/spec/application.md#generate_ai_reactions_for_utterance
from dataclasses import dataclass, field

from application.dtos.generate_ai_reactions_for_utterance_request import (
    GenerateAiReactionsForUtteranceRequest,
)
from application.errors import (
    AiTextGenerationFailed,
    InvalidRequest,
    LectureClosed,
    LectureNotFound,
    PersistenceFailed,
    UtteranceNotFound,
)
from application.ports.errors import PersistencePortError, ReactionTextPortError
from application.result import Err, Ok, Result
from application.use_cases.generate_ai_reactions_for_utterance_use_case import (
    GenerateAiReactionsForUtteranceUseCase,
)
from domain.entities.lecture import Lecture
from domain.entities.reaction import Reaction
from domain.entities.utterance import Utterance
from domain.services.lecturer_reaction_generator import LecturerReactionGenerator
from domain.value_objects.ai_persona_profile import AiPersonaProfile
from domain.value_objects.recording_speaker import RecordingSpeaker
from domain.value_objects.speech_text import SpeechText
from domain.value_objects.time_range import TimeRange


@dataclass
class StubLectureRepository:
    by_id: dict[str, Lecture] = field(default_factory=dict)

    def save(self, lecture: Lecture) -> Result[None, PersistencePortError]:
        self.by_id[str(lecture.id)] = lecture
        return Ok(None)

    def find_by_id(self, lecture_id: str) -> Result[Lecture | None, PersistencePortError]:
        return Ok(self.by_id.get(str(lecture_id)))


@dataclass
class StubReactionRepository:
    saved: list[Reaction] = field(default_factory=list)
    fail_on_save: bool = False

    def save(self, reaction: Reaction) -> Result[None, PersistencePortError]:
        if self.fail_on_save:
            return Err(
                PersistencePortError(operation="save", resource="reaction", reason="save failed")
            )
        self.saved.append(reaction)
        return Ok(None)

    def find_by_id(
        self,
        lecture_id: str,
        reaction_id: str,
    ) -> Result[Reaction | None, PersistencePortError]:
        return Ok(None)

    def list_by_lecture_id(self, lecture_id: str) -> Result[list[Reaction], PersistencePortError]:
        return Ok([])


@dataclass
class StubReactionTextGenerator:
    fail: bool = False

    def generate_for_lecturer_reaction(self, policy, utterance, persona) -> Result[str, ReactionTextPortError]:
        if self.fail:
            return Err(ReactionTextPortError(persona_id=str(persona.id), reason="failed"))
        return Ok(f"AI reaction for {persona.display_name}")

    def generate_for_user_reaction_reply(self, policy, reaction, persona) -> Result[str, ReactionTextPortError]:
        return Ok("reply")


class StubLlmAnalyzer:
    def analyze_reaction(self, text: str) -> dict:
        return {"intent": "observation", "tone": "positive"}

    def generate_reaction_policy(self, utterance_text: str, persona_prompt: str) -> dict:
        return {"summary_angle": "要約", "personalization_angle": "例え"}

    def generate_response_policy(
        self,
        reaction_text: str,
        persona_prompt: str,
        reply_target_kind: str,
    ) -> dict:
        return {"tone": "neutral", "response_intent": "共感", "reference_facts": []}


def _lecture_with_utterance() -> Lecture:
    lecture = Lecture(
        id="lecture-1",
        title="講義",
        persona_profiles=[
            AiPersonaProfile(id="p1", display_name="AI1", persona_prompt="prompt1"),
        ],
        started_at=0,
    )
    lecture.add_utterance(
        Utterance(
            id="utterance-1",
            time_range=TimeRange(start_ms=0, end_ms=1000),
            speech_text=SpeechText(text="本日は"),
            speaker=RecordingSpeaker(display_name="講師"),
        )
    )
    return lecture


def _use_case(
    lecture_repo: StubLectureRepository | None = None,
    reaction_repo: StubReactionRepository | None = None,
    text_generator: StubReactionTextGenerator | None = None,
) -> GenerateAiReactionsForUtteranceUseCase:
    return GenerateAiReactionsForUtteranceUseCase(
        _lecture_repository=lecture_repo or StubLectureRepository(),
        _reaction_repository=reaction_repo or StubReactionRepository(),
        _reaction_text_generator=text_generator or StubReactionTextGenerator(),
        _lecturer_reaction_generator=LecturerReactionGenerator(StubLlmAnalyzer()),
    )


def test_generate_ai_reactions_succeeds():
    lecture_repo = StubLectureRepository(by_id={"lecture-1": _lecture_with_utterance()})
    reaction_repo = StubReactionRepository()
    use_case = _use_case(lecture_repo=lecture_repo, reaction_repo=reaction_repo)

    result = use_case.execute(
        GenerateAiReactionsForUtteranceRequest(
            lecture_id="lecture-1",
            utterance_id="utterance-1",
        )
    )

    assert result.is_ok()
    assert result.value.reaction_id
    assert len(reaction_repo.saved) == 1
    assert reaction_repo.saved[0].dialogue_sequence == 0
    assert lecture_repo.by_id["lecture-1"].next_dialogue_sequence == 1


def test_generate_ai_reactions_fails_when_utterance_not_found():
    use_case = _use_case(
        lecture_repo=StubLectureRepository(by_id={"lecture-1": _lecture_with_utterance()}),
    )

    result = use_case.execute(
        GenerateAiReactionsForUtteranceRequest(
            lecture_id="lecture-1",
            utterance_id="missing",
        )
    )

    assert result.is_err()
    assert isinstance(result.error, UtteranceNotFound)


def test_generate_ai_reactions_fails_when_lecture_closed():
    lecture = _lecture_with_utterance()
    lecture.close()
    use_case = _use_case(
        lecture_repo=StubLectureRepository(by_id={"lecture-1": lecture}),
    )

    result = use_case.execute(
        GenerateAiReactionsForUtteranceRequest(
            lecture_id="lecture-1",
            utterance_id="utterance-1",
        )
    )

    assert result.is_err()
    assert isinstance(result.error, LectureClosed)


def test_generate_ai_reactions_fails_when_text_generation_fails():
    use_case = _use_case(
        lecture_repo=StubLectureRepository(by_id={"lecture-1": _lecture_with_utterance()}),
        text_generator=StubReactionTextGenerator(fail=True),
    )

    result = use_case.execute(
        GenerateAiReactionsForUtteranceRequest(
            lecture_id="lecture-1",
            utterance_id="utterance-1",
        )
    )

    assert result.is_err()
    assert isinstance(result.error, AiTextGenerationFailed)


def test_generate_ai_reactions_fails_when_persistence_fails():
    use_case = _use_case(
        lecture_repo=StubLectureRepository(by_id={"lecture-1": _lecture_with_utterance()}),
        reaction_repo=StubReactionRepository(fail_on_save=True),
    )

    result = use_case.execute(
        GenerateAiReactionsForUtteranceRequest(
            lecture_id="lecture-1",
            utterance_id="utterance-1",
        )
    )

    assert result.is_err()
    assert isinstance(result.error, PersistenceFailed)


def test_generate_ai_reactions_fails_when_invalid_request():
    use_case = _use_case()

    result = use_case.execute(
        GenerateAiReactionsForUtteranceRequest(lecture_id="", utterance_id="u1")
    )

    assert result.is_err()
    assert isinstance(result.error, InvalidRequest)


def test_generate_ai_reactions_fails_when_lecture_not_found():
    use_case = _use_case()

    result = use_case.execute(
        GenerateAiReactionsForUtteranceRequest(
            lecture_id="lecture-1",
            utterance_id="utterance-1",
        )
    )

    assert result.is_err()
    assert isinstance(result.error, LectureNotFound)
