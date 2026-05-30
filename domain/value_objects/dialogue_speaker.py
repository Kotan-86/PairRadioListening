# 仕様: docs/spec/domain.md#speaker（対話側）
from dataclasses import dataclass
from typing import Literal

from domain.entities.entity import EntityId


@dataclass(frozen=True)
class DialogueSpeaker:
    role: Literal["user", "ai"]
    display_name: str
    persona_id: EntityId | None = None

    def __post_init__(self) -> None:
        if self.role not in ("user", "ai"):
            raise ValueError("dialogue_speaker の role は user または ai のみです")
        if not self.display_name.strip():
            raise ValueError("dialogue_speaker の display_name は空にできません")
        if self.role == "ai" and self.persona_id is None:
            raise ValueError("dialogue_speaker の role が ai のとき persona_id は必須です")
        if self.role == "user" and self.persona_id is not None:
            raise ValueError(
                "dialogue_speaker の role が user のとき persona_id は設定できません"
            )
        if isinstance(self.persona_id, str) and not self.persona_id.strip():
            raise ValueError("dialogue_speaker の persona_id は空にできません")
