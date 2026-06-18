import pytest
from uuid import uuid4

from domain.entities.lecture import Lecture
from domain.entities.utterance import Utterance
from domain.value_objects.time_range import TimeRange
from domain.value_objects.speech_text import SpeechText
from domain.value_objects.recording_speaker import RecordingSpeaker
from domain.value_objects.ai_persona_profile import AiPersonaProfile


def _persona() -> AiPersonaProfile:
    return AiPersonaProfile(
        id=uuid4(),
        display_name="サポートAI",
        persona_prompt="あなたは親切なAIです",
    )


def test_lecture_assigns_id_when_omitted():
    # 仕様: docs/spec/domain.md#lecture（集約ルート）
    lecture = Lecture(
        title="テスト講義",
        persona_profiles=[_persona()],
    )

    assert lecture.id is not None
    assert str(lecture.id) not in ("", "None")


def test_lecture_initial_state_matches_start_lecture():
    # 仕様: docs/spec/application.md#start_lecture
    lecture = Lecture(
        id=uuid4(),
        title="テスト講義",
        persona_profiles=[_persona()],
    )

    assert lecture.status == "active"
    assert lecture.started_at is None
    assert lecture.ended_at == 0
    assert lecture.utterances == []
    assert lecture.next_dialogue_sequence == 0


def test_lecture_rejects_zero_persona_profiles():
    # 仕様: docs/spec/domain.md#lecture（集約ルート）
    with pytest.raises(ValueError, match="persona_profiles"):
        Lecture(id=uuid4(), title="テスト講義", persona_profiles=[])


def test_lecture_rejects_multiple_persona_profiles():
    # 仕様: docs/spec/domain.md#lecture（集約ルート）
    with pytest.raises(ValueError, match="persona_profiles"):
        Lecture(
            id=uuid4(),
            title="テスト講義",
            persona_profiles=[_persona(), _persona()],
        )


def test_lecture_allocate_dialogue_sequence_is_monotonic():
    # 仕様: docs/spec/domain.md#lecture（集約ルート）
    lecture = Lecture(id=uuid4(), title="テスト講義", persona_profiles=[_persona()])

    assert lecture.allocate_dialogue_sequence() == 0
    assert lecture.allocate_dialogue_sequence() == 1
    assert lecture.next_dialogue_sequence == 2


def test_lecture_allocate_dialogue_sequence_raises_when_closed():
    # 仕様: docs/spec/domain.md#lecture（集約ルート）
    lecture = Lecture(id=uuid4(), title="テスト講義", persona_profiles=[_persona()])
    lecture.close()

    with pytest.raises(ValueError, match="closed"):
        lecture.allocate_dialogue_sequence()


def test_lecture_latest_utterance_returns_max_start_ms():
    # 仕様: docs/spec/domain.md#lecture（集約ルート）
    lecture = Lecture(id=uuid4(), title="テスト講義", persona_profiles=[_persona()])
    early = Utterance(
        id=uuid4(),
        time_range=TimeRange(start_ms=0, end_ms=500),
        speech_text=SpeechText(text="早い発話"),
        speaker=RecordingSpeaker(display_name="講師"),
    )
    late = Utterance(
        id=uuid4(),
        time_range=TimeRange(start_ms=2000, end_ms=3000),
        speech_text=SpeechText(text="遅い発話"),
        speaker=RecordingSpeaker(display_name="講師"),
    )
    lecture.add_utterance(early)
    lecture.add_utterance(late)

    assert lecture.latest_utterance() == late


def test_lecture_latest_utterance_returns_none_when_empty():
    lecture = Lecture(id=uuid4(), title="テスト講義", persona_profiles=[_persona()])

    assert lecture.latest_utterance() is None


def test_lecture_add_utterance_updates_ended_at():
    """
    発話を講義に追加した際、講義の終了時間（ended_at）が
    追加された発話の終了時間に正しく更新されるかを検証する。
    """
    lecture_id = uuid4()
    lecture = Lecture(
        id=lecture_id,
        title="テスト講義",
        started_at=0,
        ended_at=1000,
        persona_profiles=[_persona()],
        utterances=[],
    )

    new_utterance = Utterance(
        id=uuid4(),
        time_range=TimeRange(start_ms=1000, end_ms=2500),
        speech_text=SpeechText(text="ここから重要なポイントです。"),
        speaker=RecordingSpeaker(display_name="講師A"),
    )

    lecture.add_utterance(new_utterance)

    assert len(lecture.utterances) == 1
    assert lecture.utterances[0] == new_utterance
    assert lecture.ended_at == 2500


def test_lecture_first_utterance_establishes_started_at():
    # 仕様: docs/spec/domain.md#lecture（集約ルート）
    lecture = Lecture(id=uuid4(), title="テスト講義", persona_profiles=[_persona()])

    utterance = Utterance(
        id=uuid4(),
        time_range=TimeRange(start_ms=0, end_ms=500),
        speech_text=SpeechText(text="はじめまして。"),
        speaker=RecordingSpeaker(display_name="講師"),
    )

    lecture.add_utterance(utterance)

    assert lecture.started_at == 0


def test_lecture_add_utterance_raises_when_closed():
    # 仕様: docs/spec/domain.md#lecture（集約ルート）
    lecture = Lecture(id=uuid4(), title="テスト講義", persona_profiles=[_persona()])
    lecture.close()

    utterance = Utterance(
        id=uuid4(),
        time_range=TimeRange(start_ms=0, end_ms=500),
        speech_text=SpeechText(text="追加不可"),
        speaker=RecordingSpeaker(display_name="講師"),
    )

    with pytest.raises(ValueError, match="closed"):
        lecture.add_utterance(utterance)


def test_lecture_close_sets_status_and_ended_at():
    # 仕様: docs/spec/application.md#end_lecture
    lecture = Lecture(id=uuid4(), title="テスト講義", persona_profiles=[_persona()])
    utterance = Utterance(
        id=uuid4(),
        time_range=TimeRange(start_ms=0, end_ms=3000),
        speech_text=SpeechText(text="本日のテーマです。"),
        speaker=RecordingSpeaker(display_name="講師"),
    )
    lecture.add_utterance(utterance)

    lecture.close()

    assert lecture.status == "closed"
    assert lecture.ended_at == 3000


def test_lecture_close_with_no_utterances():
    lecture = Lecture(id=uuid4(), title="テスト講義", persona_profiles=[_persona()])

    lecture.close()

    assert lecture.status == "closed"
    assert lecture.ended_at == 0


def test_lecture_close_raises_when_already_closed():
    lecture = Lecture(id=uuid4(), title="テスト講義", persona_profiles=[_persona()])
    lecture.close()

    with pytest.raises(ValueError, match="既に closed"):
        lecture.close()


def test_lecture_upsert_utterance_replaces_existing_id():
    # 仕様: docs/spec/domain.md#utterance（エンティティ）
    lecture = Lecture(id=uuid4(), title="テスト講義", persona_profiles=[_persona()])
    utterance_id = uuid4()
    original = Utterance(
        id=utterance_id,
        time_range=TimeRange(start_ms=0, end_ms=500),
        speech_text=SpeechText(text="初稿"),
        speaker=RecordingSpeaker(display_name="講師"),
    )
    lecture.add_utterance(original)

    updated = Utterance(
        id=utterance_id,
        time_range=TimeRange(start_ms=0, end_ms=800),
        speech_text=SpeechText(text="確定稿"),
        speaker=RecordingSpeaker(display_name="講師"),
    )
    lecture.upsert_utterance(updated)

    assert len(lecture.utterances) == 1
    assert lecture.utterances[0].speech_text.text == "確定稿"
    assert lecture.ended_at == 800


def test_lecture_normalize_time_range_for_first_utterance():
    # 仕様: docs/spec/application.md#record_utterance
    normalized = Lecture.normalize_time_range_for_first_utterance(
        TimeRange(start_ms=1000, end_ms=2500)
    )

    assert normalized.start_ms == 0
    assert normalized.end_ms == 1500
