# 仕様: docs/spec/interface.md#refresh_dialogue_controller
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DialogueRefreshOutcome:
    success: bool
    item_count: int = 0
    error_kind: str = ""
