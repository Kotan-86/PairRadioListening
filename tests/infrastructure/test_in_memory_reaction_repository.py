# 仕様: docs/spec/application.md#実装方針（ポート Outbound）
from domain.entities.reaction import Reaction
from domain.value_objects.audio_data import AudioData
from domain.value_objects.dialogue_speaker import DialogueSpeaker
from domain.value_objects.lecture_time_anchor import LectureTimeAnchor
from domain.value_objects.reaction_text import ReactionText
from domain.value_objects.reply_target import ReplyTarget
from domain.value_objects.time_range import TimeRange
from infrastructure.repositories.in_memory_reaction_repository import InMemoryReactionRepository


def _reaction(lecture_id: str, reaction_id: str) -> Reaction:
    return Reaction(
        id=reaction_id,
        lecture_id=lecture_id,
        speaker=DialogueSpeaker(role="user", display_name="ユーザー"),
        reply_target=ReplyTarget(reply_target_kind="utterance", reply_target_id="u1"),
        lecture_time_anchor=LectureTimeAnchor.from_time_range(
            TimeRange(start_ms=0, end_ms=100)
        ),
        reaction_text=ReactionText(text="テスト"),
        audio_data=AudioData.empty(),
        dialogue_sequence=0,
    )


def test_in_memory_reaction_repository_save_and_find():
    repo = InMemoryReactionRepository()
    reaction = _reaction("lecture-1", "reaction-1")

    save_result = repo.save(reaction)
    assert save_result.is_ok()

    find_result = repo.find_by_id("lecture-1", "reaction-1")
    assert find_result.is_ok()
    assert find_result.value is not None
    assert find_result.value.reaction_text.text == "テスト"


def test_in_memory_reaction_repository_list_by_lecture_id():
    repo = InMemoryReactionRepository()
    repo.save(_reaction("lecture-1", "reaction-1"))
    repo.save(_reaction("lecture-1", "reaction-2"))
    repo.save(_reaction("lecture-2", "reaction-3"))

    list_result = repo.list_by_lecture_id("lecture-1")

    assert list_result.is_ok()
    assert len(list_result.value) == 2


def test_in_memory_reaction_repository_find_returns_none_when_missing():
    repo = InMemoryReactionRepository()

    find_result = repo.find_by_id("lecture-1", "missing")

    assert find_result.is_ok()
    assert find_result.value is None
