# 仕様: docs/spec/interface.md#6.5
from dataclasses import dataclass

from domain.value_objects.time_range import TimeRange


@dataclass(frozen=True, slots=True)
class ReactionSnippet:
    speaker_label: str
    excerpt: str


@dataclass(frozen=True, slots=True)
class DialoguePresentationContext:
    utterance_times: dict[str, TimeRange]
    reaction_snippets: dict[str, ReactionSnippet]
