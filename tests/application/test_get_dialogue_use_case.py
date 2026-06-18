# 仕様: docs/spec/application.md#get_dialogue
from dataclasses import dataclass, field

from application.dtos.dialogue_item import GetDialogueRequest
from application.errors import InvalidRequest, LectureNotFound, PersistenceFailed
from application.ports.errors import PersistencePortError
from application.result import Err, Ok, Result
from application.use_cases.get_dialogue_use_case import GetDialogueUseCase
from domain.entities.lecture import Lecture
from domain.entities.reaction import Reaction
from domain.value_objects.ai_persona_profile import AiPersonaProfile
from domain.value_objects.audio_data import AudioData
from domain.value_objects.dialogue_speaker import DialogueSpeaker
from domain.value_objects.lecture_time_anchor import LectureTimeAnchor
from domain.value_objects.reaction_text import ReactionText
from domain.value_objects.reply_target import ReplyTarget
from domain.value_objects.time_range import TimeRange


@dataclass
class StubLectureRepository:
    by_id: dict[str, Lecture] = field(default_factory=dict)

    def save(self, lecture: Lecture) -> Result[None, PersistencePortError]:
        return Ok(None)

    def find_by_id(self, lecture_id: str) -> Result[Lecture | None, PersistencePortError]:
        return Ok(self.by_id.get(str(lecture_id)))


@dataclass
class StubReactionRepository:
    by_id: dict[str, dict[str, Reaction]] = field(default_factory=dict)
    fail_on_list: bool = False

    def save(self, reaction: Reaction) -> Result[None, PersistencePortError]:
        return Ok(None)

    def find_by_id(
        self,
        lecture_id: str,
        reaction_id: str,
    ) -> Result[Reaction | None, PersistencePortError]:
        return Ok(self.by_id.get(str(lecture_id), {}).get(str(reaction_id)))

    def list_by_lecture_id(self, lecture_id: str) -> Result[list[Reaction], PersistencePortError]:
        if self.fail_on_list:
            return Err(
                PersistencePortError(operation="load", resource="reaction", reason="load failed")
            )
        return Ok(list(self.by_id.get(str(lecture_id), {}).values()))


def _lecture() -> Lecture:
    return Lecture(
        id="lecture-1",
        title="講義",
        persona_profiles=[
            AiPersonaProfile(id="p1", display_name="AI", persona_prompt="prompt")
        ],
        started_at=0,
    )


def _reactions() -> dict[str, Reaction]:
    return {
        "r2": Reaction(
            id="r2",
            lecture_id="lecture-1",
            speaker=DialogueSpeaker(role="ai", display_name="AI", persona_id="p1"),
            reply_target=ReplyTarget(reply_target_kind="utterance", reply_target_id="u1"),
            lecture_time_anchor=LectureTimeAnchor.from_time_range(
                TimeRange(start_ms=0, end_ms=1000)
            ),
            reaction_text=ReactionText(text="AI"),
            audio_data=AudioData.empty(),
            dialogue_sequence=1,
        ),
        "r1": Reaction(
            id="r1",
            lecture_id="lecture-1",
            speaker=DialogueSpeaker(role="user", display_name="ユーザー"),
            reply_target=ReplyTarget(reply_target_kind="utterance", reply_target_id="u1"),
            lecture_time_anchor=LectureTimeAnchor.from_time_range(
                TimeRange(start_ms=0, end_ms=1000)
            ),
            reaction_text=ReactionText(text="感想"),
            audio_data=AudioData.empty(),
            dialogue_sequence=0,
        ),
    }


def test_get_dialogue_returns_reactions_sorted_by_dialogue_sequence():
    use_case = GetDialogueUseCase(
        _lecture_repository=StubLectureRepository(by_id={"lecture-1": _lecture()}),
        _reaction_repository=StubReactionRepository(by_id={"lecture-1": _reactions()}),
    )

    result = use_case.execute(GetDialogueRequest(lecture_id="lecture-1"))

    assert result.is_ok()
    assert len(result.value.items) == 2
    assert result.value.items[0].reaction_id == "r1"
    assert result.value.items[0].dialogue_sequence == 0
    assert result.value.items[1].reaction_id == "r2"
    assert result.value.items[1].dialogue_sequence == 1


def test_get_dialogue_fails_when_invalid_request():
    use_case = GetDialogueUseCase(
        _lecture_repository=StubLectureRepository(),
        _reaction_repository=StubReactionRepository(),
    )

    result = use_case.execute(GetDialogueRequest(lecture_id=""))

    assert result.is_err()
    assert isinstance(result.error, InvalidRequest)


def test_get_dialogue_fails_when_lecture_not_found():
    use_case = GetDialogueUseCase(
        _lecture_repository=StubLectureRepository(),
        _reaction_repository=StubReactionRepository(),
    )

    result = use_case.execute(GetDialogueRequest(lecture_id="missing"))

    assert result.is_err()
    assert isinstance(result.error, LectureNotFound)


def test_get_dialogue_fails_when_load_fails():
    use_case = GetDialogueUseCase(
        _lecture_repository=StubLectureRepository(by_id={"lecture-1": _lecture()}),
        _reaction_repository=StubReactionRepository(fail_on_list=True),
    )

    result = use_case.execute(GetDialogueRequest(lecture_id="lecture-1"))

    assert result.is_err()
    assert isinstance(result.error, PersistenceFailed)
