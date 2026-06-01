# 仕様: docs/spec/domain.md#user_reaction_responder
import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from domain.services.user_reaction_responder import UserReactionResponder
from domain.services.llm_analyzer_protocol import LlmAnalyzerProtocol
from domain.entities.reaction import Reaction
from domain.value_objects.dialogue_speaker import DialogueSpeaker
from domain.value_objects.reply_target import ReplyTarget
from domain.value_objects.lecture_time_anchor import LectureTimeAnchor
from domain.value_objects.time_range import TimeRange
from domain.value_objects.reaction_text import ReactionText
from domain.value_objects.audio_data import AudioData
from domain.value_objects.ai_persona_profile import AiPersonaProfile


def _reaction(reply_target_kind: str) -> Reaction:
    return Reaction(
        id=uuid4(),
        lecture_id=uuid4(),
        speaker=DialogueSpeaker(role="user", display_name="ユーザーA"),
        reply_target=ReplyTarget(
            reply_target_kind=reply_target_kind,
            reply_target_id=uuid4(),
        ),
        lecture_time_anchor=LectureTimeAnchor(
            time_range=TimeRange(start_ms=1000, end_ms=2000)
        ),
        reaction_text=ReactionText(text="ここが少しわかりにくいです"),
        audio_data=AudioData.empty(),
        dialogue_sequence=0,
    )


@pytest.mark.parametrize("reply_target_kind", ["utterance", "reaction"])
def test_user_reaction_responder_determine_policy_by_reply_target_kind(
    reply_target_kind: str,
):
    mock_llm_client = MagicMock(spec=LlmAnalyzerProtocol)
    mock_llm_client.generate_response_policy.return_value = {
        "tone": "共感的",
        "response_intent": "相槌を打ちつつ補足する",
        "reference_facts": ["講師の先ほどの言葉"],
    }

    responder = UserReactionResponder(analyzer_client=mock_llm_client)
    reaction = _reaction(reply_target_kind)
    persona = AiPersonaProfile(
        id=uuid4(),
        display_name="サポートAI",
        persona_prompt="あなたは親切なAIです",
    )

    policy = responder.determine_policy(reaction=reaction, persona=persona)

    assert policy.persona_id == persona.id
    assert policy.tone == "共感的"
    assert policy.response_intent == "相槌を打ちつつ補足する"
    assert policy.reference_facts == ["講師の先ほどの言葉"]
    mock_llm_client.generate_response_policy.assert_called_once_with(
        reaction_text="ここが少しわかりにくいです",
        persona_prompt="あなたは親切なAIです",
        reply_target_kind=reply_target_kind,
    )
