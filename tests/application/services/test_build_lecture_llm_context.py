# 仕様: docs/spec/framework_llm.md#8.2
import pytest

from application.services.build_lecture_llm_context import build_lecture_llm_context
from application.services.build_reply_target_focus import build_reply_target_focus
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


def _lecture_with_utterances(*utterances: Utterance) -> Lecture:
    lecture = Lecture(
        id="lecture-1",
        title="講義",
        persona_profiles=[
            AiPersonaProfile(id="p1", display_name="AI", persona_prompt="prompt"),
        ],
        started_at=0,
        utterances=list(utterances),
    )
    return lecture


def _utterance(
    utterance_id: str,
    *,
    start_ms: int,
    end_ms: int,
    text: str = "発話",
) -> Utterance:
    return Utterance(
        id=utterance_id,
        time_range=TimeRange(start_ms=start_ms, end_ms=end_ms),
        speech_text=SpeechText(text=text),
        speaker=RecordingSpeaker(role="lecturer", display_name="講師"),
    )


def _user_reaction(*, anchor_ms: int, reply_target_id: str = "u1") -> Reaction:
    return Reaction(
        id="user-1",
        lecture_id="lecture-1",
        speaker=DialogueSpeaker(role="user", display_name="ユーザー"),
        reply_target=ReplyTarget(reply_target_kind="utterance", reply_target_id=reply_target_id),
        lecture_time_anchor=LectureTimeAnchor.from_time_range(
            TimeRange(start_ms=anchor_ms, end_ms=anchor_ms)
        ),
        reaction_text=ReactionText(text="投稿"),
        audio_data=AudioData.empty(),
        dialogue_sequence=0,
    )


@pytest.mark.phase3
def test_build_lecture_llm_context_uses_reaction_anchor_as_t0():
    lecture = _lecture_with_utterances(
        _utterance("u1", start_ms=0, end_ms=30_000),
        _utterance("u2", start_ms=40_000, end_ms=50_000),
    )
    reaction = _user_reaction(anchor_ms=50_000)

    context = build_lecture_llm_context(lecture, reaction)

    assert context.anchor_ms == 50_000


@pytest.mark.phase3
def test_build_lecture_llm_context_excludes_utterances_after_t0():
    lecture = _lecture_with_utterances(
        _utterance("before", start_ms=10_000, end_ms=20_000),
        _utterance("after", start_ms=60_001, end_ms=70_000),
        _utterance("overlap", start_ms=45_000, end_ms=55_000),
    )
    reaction = _user_reaction(anchor_ms=50_000)

    context = build_lecture_llm_context(lecture, reaction)

    ids = [item.utterance_id for item in context.utterance_excerpts]
    assert "after" not in ids
    assert ids == ["before", "overlap"]


@pytest.mark.phase3
def test_build_lecture_llm_context_limits_to_15_newest_by_end_ms():
    utterances = [
        _utterance(f"u{i}", start_ms=i * 1000, end_ms=i * 1000 + 500)
        for i in range(20)
    ]
    lecture = _lecture_with_utterances(*utterances)
    reaction = _user_reaction(anchor_ms=25_000)

    context = build_lecture_llm_context(lecture, reaction)

    assert len(context.utterance_excerpts) == 15
    end_ms_values = [item.end_ms for item in context.utterance_excerpts]
    assert end_ms_values == sorted(end_ms_values)
    assert max(end_ms_values) == 19_500
    assert min(end_ms_values) == 5_500


@pytest.mark.phase3
def test_build_lecture_llm_context_sorts_by_start_ms_asc():
    lecture = _lecture_with_utterances(
        _utterance("late", start_ms=30_000, end_ms=40_000),
        _utterance("early", start_ms=5_000, end_ms=15_000),
    )
    reaction = _user_reaction(anchor_ms=40_000)

    context = build_lecture_llm_context(lecture, reaction)

    assert [item.utterance_id for item in context.utterance_excerpts] == [
        "early",
        "late",
    ]


@pytest.mark.phase3
def test_build_lecture_llm_context_allows_empty_window():
    lecture = _lecture_with_utterances(
        _utterance("future", start_ms=100_000, end_ms=110_000),
    )
    reaction = _user_reaction(anchor_ms=50_000)

    context = build_lecture_llm_context(lecture, reaction)

    assert context.utterance_excerpts == ()


@pytest.mark.phase3
def test_build_reply_target_focus_for_utterance():
    lecture = _lecture_with_utterances(
        _utterance("u1", start_ms=0, end_ms=1200, text="講義本文"),
    )
    reaction = _user_reaction(anchor_ms=1200, reply_target_id="u1")

    focus = build_reply_target_focus(lecture, reaction)

    assert focus is not None
    assert focus.kind == "utterance"
    assert focus.speech_text == "講義本文"
    assert focus.start_ms == 0
    assert focus.end_ms == 1200


@pytest.mark.phase3
def test_build_reply_target_focus_for_reaction():
    lecture = _lecture_with_utterances()
    user_reaction = Reaction(
        id="user-1",
        lecture_id="lecture-1",
        speaker=DialogueSpeaker(role="user", display_name="ユーザー"),
        reply_target=ReplyTarget(reply_target_kind="reaction", reply_target_id="ai-1"),
        lecture_time_anchor=LectureTimeAnchor.from_time_range(
            TimeRange(start_ms=1000, end_ms=1000)
        ),
        reaction_text=ReactionText(text="続きは？"),
        audio_data=AudioData.empty(),
        dialogue_sequence=1,
    )
    ai_reaction = Reaction(
        id="ai-1",
        lecture_id="lecture-1",
        speaker=DialogueSpeaker(role="ai", display_name="AI1", persona_id="p1"),
        reply_target=ReplyTarget(reply_target_kind="utterance", reply_target_id="u1"),
        lecture_time_anchor=LectureTimeAnchor.from_time_range(
            TimeRange(start_ms=1000, end_ms=1000)
        ),
        reaction_text=ReactionText(text="前の AI 返信"),
        audio_data=AudioData.empty(),
        dialogue_sequence=0,
    )

    focus = build_reply_target_focus(
        lecture,
        user_reaction,
        target_reaction=ai_reaction,
    )

    assert focus is not None
    assert focus.kind == "reaction"
    assert focus.reaction_text == "前の AI 返信"
    assert focus.speaker_display_name == "AI1"


@pytest.mark.phase3
def test_build_reply_target_focus_returns_none_when_utterance_missing():
    lecture = _lecture_with_utterances()
    reaction = _user_reaction(anchor_ms=1000, reply_target_id="missing")

    assert build_reply_target_focus(lecture, reaction) is None
