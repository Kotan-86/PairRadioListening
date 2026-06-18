# 仕様: docs/spec/application.md#StartLectureRequest
from collections.abc import Sequence
from dataclasses import dataclass

from application.errors import InvalidPersonaProfiles
from application.result import Err, Ok, Result
from domain.value_objects.ai_persona_profile import AiPersonaProfile


@dataclass(frozen=True, slots=True)
class StartLectureRequest:
    persona_profiles: tuple[AiPersonaProfile, ...]
    title: str = ""

    def validate(self) -> Result[None, InvalidPersonaProfiles]:
        if len(self.persona_profiles) != 1:
            return Err(
                InvalidPersonaProfiles(
                    reason="persona_profiles must contain exactly one item",
                )
            )
        return Ok(None)

    @classmethod
    def from_fields(
        cls,
        persona_profiles: Sequence[AiPersonaProfile],
        title: str = "",
    ) -> "StartLectureRequest":
        return cls(persona_profiles=tuple(persona_profiles), title=title)
