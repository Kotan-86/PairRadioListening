# 仕様: docs/spec/application.md#post_user_reaction
from dataclasses import dataclass, field

from application.dtos.post_user_reaction_request import PostUserReactionRequest
from application.errors import (
    InvalidRequest,
    LectureClosed,
    LectureNotFound,
    PersistenceFailed,
    ReplyTargetNotFound,
    TimelineNotEstablished,
)
from application.ports.errors import PersistencePortError
from application.result import Err, Ok, Result
from application.use_cases.post_user_reaction_use_case import PostUserReactionUseCase
from domain.entities.lecture import Lecture
from domain.entities.reaction import Reaction
from domain.entities.utterance import Utterance
from domain.value_objects.ai_persona_profile import AiPersonaProfile
from domain.value_objects.audio_data import AudioData
from domain.value_objects.dialogue_speaker import DialogueSpeaker
from domain.value_objects.lecture_time_anchor import LectureTimeAnchor
from domain.value_objects.reaction_text import ReactionText
from domain.value_objects.recording_speaker import RecordingSpeaker
from domain.value_objects.reply_target import ReplyTarget
from domain.value_objects.speech_text import SpeechText
from domain.value_objects.time_range import TimeRange


@dataclass
class StubLectureRepository:
    by_id: dict[str, Lecture] = field(default_factory=dict)
    fail_on_load: bool = False

    def save(self, lecture: Lecture) -> Result[None, PersistencePortError]:
        self.by_id[str(lecture.id)] = lecture
        return Ok(None)

    def find_by_id(self, lecture_id: str) -> Result[Lecture | None, PersistencePortError]:
        if self.fail_on_load:
            return Err(
                PersistencePortError(operation="load", resource="lecture", reason="load failed")
            )
        return Ok(self.by_id.get(str(lecture_id)))


@dataclass
class StubReactionRepository:
    saved: list[Reaction] = field(default_factory=list)
    fail_on_save: bool = False
    by_id: dict[str, dict[str, Reaction]] = field(default_factory=dict)

    def save(self, reaction: Reaction) -> Result[None, PersistencePortError]:
        if self.fail_on_save:
            return Err(
                PersistencePortError(operation="save", resource="reaction", reason="save failed")
            )
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


def _lecture_with_utterance() -> Lecture:
    lecture = Lecture(
        id="lecture-1",
        title="講義",
        persona_profiles=[
            AiPersonaProfile(id="p1", display_name="AI", persona_prompt="prompt")
        ],
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


def _request(
    reply_target: ReplyTarget | None = None,
) -> PostUserReactionRequest:
    return PostUserReactionRequest(
        lecture_id="lecture-1",
        reaction_text=ReactionText(text="なるほど"),
        reply_target=reply_target
        or ReplyTarget(reply_target_kind="utterance", reply_target_id="utterance-1"),
        lecture_time_anchor=LectureTimeAnchor.from_time_range(
            TimeRange(start_ms=500, end_ms=1000)
        ),
        speaker_display_name="ユーザーA",
    )


def test_post_user_reaction_succeeds():
    lecture_repo = StubLectureRepository(by_id={"lecture-1": _lecture_with_utterance()})
    reaction_repo = StubReactionRepository()
    use_case = PostUserReactionUseCase(
        _lecture_repository=lecture_repo,
        _reaction_repository=reaction_repo,
    )

    result = use_case.execute(_request())

    assert result.is_ok()
    assert len(reaction_repo.saved) == 1
    assert reaction_repo.saved[0].speaker.role == "user"


def test_post_user_reaction_fails_when_invalid_request():
    use_case = PostUserReactionUseCase(
        _lecture_repository=StubLectureRepository(),
        _reaction_repository=StubReactionRepository(),
    )

    request = PostUserReactionRequest(
        lecture_id="",
        reaction_text=ReactionText(text="x"),
        reply_target=ReplyTarget(reply_target_kind="utterance", reply_target_id="u1"),
        lecture_time_anchor=LectureTimeAnchor.from_time_range(
            TimeRange(start_ms=0, end_ms=100)
        ),
        speaker_display_name="ユーザー",
    )

    result = use_case.execute(request)

    assert result.is_err()
    assert isinstance(result.error, InvalidRequest)


def test_post_user_reaction_fails_when_lecture_not_found():
    use_case = PostUserReactionUseCase(
        _lecture_repository=StubLectureRepository(),
        _reaction_repository=StubReactionRepository(),
    )

    result = use_case.execute(_request())

    assert result.is_err()
    assert isinstance(result.error, LectureNotFound)


def test_post_user_reaction_fails_when_lecture_closed():
    lecture = _lecture_with_utterance()
    lecture.close()
    use_case = PostUserReactionUseCase(
        _lecture_repository=StubLectureRepository(by_id={"lecture-1": lecture}),
        _reaction_repository=StubReactionRepository(),
    )

    result = use_case.execute(_request())

    assert result.is_err()
    assert isinstance(result.error, LectureClosed)


def test_post_user_reaction_fails_when_timeline_not_established():
    lecture = Lecture(
        id="lecture-1",
        title="講義",
        persona_profiles=[
            AiPersonaProfile(id="p1", display_name="AI", persona_prompt="prompt")
        ],
    )
    use_case = PostUserReactionUseCase(
        _lecture_repository=StubLectureRepository(by_id={"lecture-1": lecture}),
        _reaction_repository=StubReactionRepository(),
    )

    result = use_case.execute(_request())

    assert result.is_err()
    assert isinstance(result.error, TimelineNotEstablished)


def test_post_user_reaction_fails_when_reply_target_not_found():
    use_case = PostUserReactionUseCase(
        _lecture_repository=StubLectureRepository(by_id={"lecture-1": _lecture_with_utterance()}),
        _reaction_repository=StubReactionRepository(),
    )

    result = use_case.execute(
        _request(
            ReplyTarget(reply_target_kind="utterance", reply_target_id="missing")
        )
    )

    assert result.is_err()
    assert isinstance(result.error, ReplyTargetNotFound)


def test_post_user_reaction_fails_when_persistence_fails():
    use_case = PostUserReactionUseCase(
        _lecture_repository=StubLectureRepository(by_id={"lecture-1": _lecture_with_utterance()}),
        _reaction_repository=StubReactionRepository(fail_on_save=True),
    )

    result = use_case.execute(_request())

    assert result.is_err()
    assert isinstance(result.error, PersistenceFailed)
