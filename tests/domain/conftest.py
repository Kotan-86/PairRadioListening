# 仕様: docs/spec/domain.md#lecture（集約ルート）
import pytest
from uuid import uuid4

from domain.value_objects.ai_persona_profile import AiPersonaProfile


@pytest.fixture
def single_persona() -> AiPersonaProfile:
    return AiPersonaProfile(
        id=uuid4(),
        display_name="サポートAI",
        persona_prompt="あなたは親切なAIです",
    )
