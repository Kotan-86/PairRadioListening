# 仕様: docs/spec/interface.md#7.4
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DialogueLineView:
    reaction_id: str
    speaker_label: str
    body: str
    reference_time_label: str
    reference_quote_label: str


@dataclass(frozen=True, slots=True)
class DialogueViewModel:
    lecture_id: str
    lines: tuple[DialogueLineView, ...]
    error_message: str
