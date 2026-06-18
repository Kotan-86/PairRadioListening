# 仕様: docs/spec/application.md#generate_ai_replies_for_user_reaction
from dataclasses import dataclass, field

from application.dtos.generate_ai_replies_for_user_reaction_request import (
    GenerateAiRepliesForUserReactionRequest,
)
from application.errors import (
    AiTextGenerationFailed,
    InvalidRequest,
    InvalidUserReaction,
    LectureNotFound,
    ReactionNotFound,
)
from application.ports.errors import PersistencePortError, ReactionTextPortError
from application.result import Err, Ok, Result
from application.use_cases.generate_ai_replies_for_user_reaction_use_case import (
    GenerateAiRepliesForUserReactionUseCase,
)
from domain.entities.lecture import Lecture
from domain.entities.reaction import Reaction
from domain.services.user_reaction_responder import UserReactionResponder
from domain.value_objects.ai_persona_profile import AiPersonaProfile
from domain.value_objects.audio_data import AudioData
from domain.value_objects.dialogue_speaker import DialogueSpeaker
from domain.value_objects.lecture_time_anchor import LectureTimeAnchor
from domain.value_objects.reaction_text import ReactionText
from domain.value_objects.reply_target import ReplyTarget
from domain.entities.utterance import Utterance
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
    by_id: dict[str, dict[str, Reaction]] = field(default_factory=dict)

    def save(self, reaction: Reaction) -> Result[None, PersistencePortError]:
        self.saved.append(reaction)
        lecture_key = str(reaction.lecture_id)
        if lecture_key not in self.by_id:
            self.by_id[lecture_key] = {}
        self.by_id[lecture_key][str(reaction.id)] = reaction
        return Ok(None)

    def find_by_id(
        self,
        lecture_id: str,
        reaction_id: str,
    ) -> Result[Reaction | None, PersistencePortError]:
        return Ok(self.by_id.get(str(lecture_id), {}).get(str(reaction_id)))

    def list_by_lecture_id(self, lecture_id: str) -> Result[list[Reaction], PersistencePortError]:
        return Ok(list(self.by_id.get(str(lecture_id), {}).values()))


@dataclass
class StubReactionTextGenerator:
    fail: bool = False

    def generate_for_lecturer_reaction(self, policy, utterance, persona) -> Result[str, ReactionTextPortError]:
        return Ok("text")

    def generate_for_user_reaction_reply(
        self, policy, reaction, persona, lecture_llm_context, reply_target_focus
    ) -> Result[str, ReactionTextPortError]:
        if self.fail:
            return Err(ReactionTextPortError(persona_id=str(persona.id), reason="failed"))
        return Ok(f"reply from {persona.display_name}")


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
        lecture_llm_context,
        reply_target_focus,
    ) -> dict:
        return {"tone": "neutral", "response_intent": "共感", "reference_facts": []}


def _lecture() -> Lecture:
    return Lecture(
        id="lecture-1",
        title="講義",
        persona_profiles=[
            AiPersonaProfile(id="p1", display_name="AI1", persona_prompt="prompt1"),
        ],
        started_at=0,
        utterances=[
            Utterance(
                id="u1",
                time_range=TimeRange(start_ms=0, end_ms=1000),
                speech_text=SpeechText(text="講義"),
                speaker=RecordingSpeaker(role="lecturer", display_name="講師"),
            ),
        ],
    )


def _user_reaction() -> Reaction:
    return Reaction(
        id="user-reaction-1",
        lecture_id="lecture-1",
        speaker=DialogueSpeaker(role="user", display_name="ユーザー"),
        reply_target=ReplyTarget(reply_target_kind="utterance", reply_target_id="u1"),
        lecture_time_anchor=LectureTimeAnchor.from_time_range(
            TimeRange(start_ms=0, end_ms=1000)
        ),
        reaction_text=ReactionText(text="なるほど"),
        audio_data=AudioData.empty(),
        dialogue_sequence=0,
    )


def _ai_reaction() -> Reaction:
    return Reaction(
        id="ai-reaction-1",
        lecture_id="lecture-1",
        speaker=DialogueSpeaker(role="ai", display_name="AI1", persona_id="p1"),
        reply_target=ReplyTarget(reply_target_kind="utterance", reply_target_id="u1"),
        lecture_time_anchor=LectureTimeAnchor.from_time_range(
            TimeRange(start_ms=0, end_ms=1000)
        ),
        reaction_text=ReactionText(text="AI"),
        audio_data=AudioData.empty(),
        dialogue_sequence=1,
    )


def _use_case(
    text_generator: StubReactionTextGenerator | None = None,
    lecture_repo: StubLectureRepository | None = None,
    reaction_repo: StubReactionRepository | None = None,
) -> GenerateAiRepliesForUserReactionUseCase:
    return GenerateAiRepliesForUserReactionUseCase(
        _lecture_repository=lecture_repo
        or StubLectureRepository(by_id={"lecture-1": _lecture()}),
        _reaction_repository=reaction_repo
        or StubReactionRepository(by_id={"lecture-1": {"user-reaction-1": _user_reaction()}}),
        _reaction_text_generator=text_generator or StubReactionTextGenerator(),
        _user_reaction_responder=UserReactionResponder(StubLlmAnalyzer()),
    )


def test_generate_ai_replies_succeeds():
    lecture_repo = StubLectureRepository(by_id={"lecture-1": _lecture()})
    reaction_repo = StubReactionRepository(
        by_id={"lecture-1": {"user-reaction-1": _user_reaction()}}
    )
    use_case = _use_case(lecture_repo=lecture_repo, reaction_repo=reaction_repo)

    result = use_case.execute(
        GenerateAiRepliesForUserReactionRequest(
            lecture_id="lecture-1",
            reaction_id="user-reaction-1",
        )
    )

    assert result.is_ok()
    assert result.value.reaction_id
    assert len(reaction_repo.saved) == 1
    assert reaction_repo.saved[0].dialogue_sequence == 0
    assert lecture_repo.by_id["lecture-1"].next_dialogue_sequence == 1


def test_generate_ai_replies_fails_when_reaction_not_found():
    use_case = GenerateAiRepliesForUserReactionUseCase(
        _lecture_repository=StubLectureRepository(by_id={"lecture-1": _lecture()}),
        _reaction_repository=StubReactionRepository(),
        _reaction_text_generator=StubReactionTextGenerator(),
        _user_reaction_responder=UserReactionResponder(StubLlmAnalyzer()),
    )

    result = use_case.execute(
        GenerateAiRepliesForUserReactionRequest(
            lecture_id="lecture-1",
            reaction_id="missing",
        )
    )

    assert result.is_err()
    assert isinstance(result.error, ReactionNotFound)


def test_generate_ai_replies_fails_when_not_user_reaction():
    use_case = GenerateAiRepliesForUserReactionUseCase(
        _lecture_repository=StubLectureRepository(by_id={"lecture-1": _lecture()}),
        _reaction_repository=StubReactionRepository(
            by_id={"lecture-1": {"ai-reaction-1": _ai_reaction()}}
        ),
        _reaction_text_generator=StubReactionTextGenerator(),
        _user_reaction_responder=UserReactionResponder(StubLlmAnalyzer()),
    )

    result = use_case.execute(
        GenerateAiRepliesForUserReactionRequest(
            lecture_id="lecture-1",
            reaction_id="ai-reaction-1",
        )
    )

    assert result.is_err()
    assert isinstance(result.error, InvalidUserReaction)


def test_generate_ai_replies_fails_when_text_generation_fails():
    use_case = _use_case(text_generator=StubReactionTextGenerator(fail=True))

    result = use_case.execute(
        GenerateAiRepliesForUserReactionRequest(
            lecture_id="lecture-1",
            reaction_id="user-reaction-1",
        )
    )

    assert result.is_err()
    assert isinstance(result.error, AiTextGenerationFailed)


def test_generate_ai_replies_fails_when_invalid_request():
    use_case = _use_case()

    result = use_case.execute(
        GenerateAiRepliesForUserReactionRequest(lecture_id="", reaction_id="r1")
    )

    assert result.is_err()
    assert isinstance(result.error, InvalidRequest)


def test_generate_ai_replies_fails_when_lecture_not_found():
    use_case = GenerateAiRepliesForUserReactionUseCase(
        _lecture_repository=StubLectureRepository(),
        _reaction_repository=StubReactionRepository(
            by_id={"lecture-1": {"user-reaction-1": _user_reaction()}}
        ),
        _reaction_text_generator=StubReactionTextGenerator(),
        _user_reaction_responder=UserReactionResponder(StubLlmAnalyzer()),
    )

    result = use_case.execute(
        GenerateAiRepliesForUserReactionRequest(
            lecture_id="lecture-1",
            reaction_id="user-reaction-1",
        )
    )

    assert result.is_err()
    assert isinstance(result.error, LectureNotFound)
