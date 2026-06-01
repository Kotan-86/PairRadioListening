# 仕様: docs/spec/domain.md#lecturer_reaction_generator
from unittest.mock import MagicMock
from uuid import uuid4

from domain.services.lecturer_reaction_generator import LecturerReactionGenerator
from domain.services.llm_analyzer_protocol import LlmAnalyzerProtocol
from domain.entities.utterance import Utterance
from domain.value_objects.time_range import TimeRange
from domain.value_objects.speech_text import SpeechText
from domain.value_objects.recording_speaker import RecordingSpeaker
from domain.value_objects.ai_persona_profile import AiPersonaProfile


def test_lecturer_reaction_generator_generate_policy_returns_single_policy():
    mock_llm_client = MagicMock(spec=LlmAnalyzerProtocol)
    mock_llm_client.generate_reaction_policy.return_value = {
        "summary_angle": "要点の整理",
        "personalization_angle": "身近な例え",
    }

    generator = LecturerReactionGenerator(analyzer_client=mock_llm_client)
    utterance = Utterance(
        id=uuid4(),
        time_range=TimeRange(start_ms=0, end_ms=1000),
        speech_text=SpeechText(text="本日のテーマです"),
        speaker=RecordingSpeaker(display_name="講師"),
    )
    persona = AiPersonaProfile(
        id=uuid4(),
        display_name="サポートAI",
        persona_prompt="あなたは親切なAIです",
    )

    policy = generator.generate_policy(utterance=utterance, persona=persona)

    assert policy.persona_id == persona.id
    assert policy.summary_angle == "要点の整理"
    assert policy.personalization_angle == "身近な例え"
    mock_llm_client.generate_reaction_policy.assert_called_once_with(
        utterance_text="本日のテーマです",
        persona_prompt="あなたは親切なAIです",
    )
