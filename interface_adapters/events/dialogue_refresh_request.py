# 仕様: docs/spec/interface.md#refresh_dialogue_controller
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DialogueRefreshRequest:
    lecture_id: str
