# 仕様: docs/spec/application.md#lecture_llm_context, docs/spec/framework_llm.md#3.1
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UtteranceExcerpt:
    utterance_id: str
    start_ms: int
    end_ms: int
    speech_text: str


@dataclass(frozen=True, slots=True)
class LectureLlmContext:
    anchor_ms: int
    utterance_excerpts: tuple[UtteranceExcerpt, ...]
