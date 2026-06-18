# 仕様: docs/spec/application.md#lecture_llm_context, docs/spec/framework_llm.md#3.1
from domain.entities.lecture import Lecture
from domain.entities.reaction import Reaction
from domain.value_objects.lecture_llm_context import LectureLlmContext, UtteranceExcerpt

_WINDOW_MS = 60_000
_MAX_EXCERPTS = 15


def _anchor_ms(reaction: Reaction) -> int:
    return reaction.lecture_time_anchor.time_range.end_ms


def _overlaps_window(*, start_ms: int, end_ms: int, window_start: int, window_end: int) -> bool:
    return start_ms <= window_end and end_ms >= window_start


def build_lecture_llm_context(lecture: Lecture, user_reaction: Reaction) -> LectureLlmContext:
    t0 = _anchor_ms(user_reaction)
    window_start = t0 - _WINDOW_MS
    window_end = t0

    candidates: list[UtteranceExcerpt] = []
    for utterance in lecture.utterances:
        start_ms = utterance.time_range.start_ms
        end_ms = utterance.time_range.end_ms
        if start_ms > t0:
            continue
        if not _overlaps_window(
            start_ms=start_ms,
            end_ms=end_ms,
            window_start=window_start,
            window_end=window_end,
        ):
            continue
        candidates.append(
            UtteranceExcerpt(
                utterance_id=str(utterance.id),
                start_ms=start_ms,
                end_ms=end_ms,
                speech_text=utterance.speech_text.text,
            )
        )

    if len(candidates) > _MAX_EXCERPTS:
        candidates = sorted(candidates, key=lambda item: item.end_ms, reverse=True)[
            :_MAX_EXCERPTS
        ]

    excerpts = tuple(sorted(candidates, key=lambda item: item.start_ms))
    return LectureLlmContext(anchor_ms=t0, utterance_excerpts=excerpts)
