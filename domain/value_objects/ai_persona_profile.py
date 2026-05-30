# 仕様: docs/spec/domain.md#ai_persona_profile
from dataclasses import dataclass

from domain.entities.entity import EntityId


@dataclass(frozen=True)
class AiPersonaProfile:
    id: EntityId
    display_name: str
    persona_prompt: str
    voice_id: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.id, str) and not self.id.strip():
            raise ValueError("ai_persona_profile の id は空にできません")
        if not self.display_name.strip():
            raise ValueError("ai_persona_profile の display_name は空にできません")
        if self.voice_id is not None and not self.voice_id.strip():
            raise ValueError("ai_persona_profile の voice_id は空文字にできません")
