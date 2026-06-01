# 仕様: docs/spec/interface.md#start_lecture_controller
from dataclasses import dataclass

from domain.value_objects.ai_persona_profile import AiPersonaProfile


@dataclass(frozen=True, slots=True)
class StartLectureFormEvent:
    persona_profiles: tuple[AiPersonaProfile, ...]
    title: str = ""
