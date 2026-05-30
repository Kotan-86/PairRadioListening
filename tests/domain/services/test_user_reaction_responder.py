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
from domain.value_objects.dialogue_policies import (
    UserReactionAnalysisResult,
    UserReactionIntent,
    EmotionTone
)

def test_user_reaction_responder_determines_policies_and_interacts_correctly():
    """
    ユーザー投稿に対する返信方針決定処理において、
    LLMが正しい引数で呼び出され、その結果がドメインオブジェクトに変換されるかを検証する。
    """
    
    # ---------------------------------------------------------
    # Arrange: テスト条件とテストデータを準備する
    # ---------------------------------------------------------
    
    # 【テストダブルの目的 1】: 依存関係の振る舞いを制御する（スタブとしての役割）
    # LLMクライアントのインターフェースをモック化し、テスト用の固定の戻り値を設定する。
    # これにより、実際にLLMのAPIを叩くことなく、常に同じ条件でテストができる。
    mock_llm_client = MagicMock(spec=LlmAnalyzerProtocol)
    mock_llm_client.generate_response_policy.return_value = {
        "tone": "共感的",
        "response_intent": "相槌を打ちつつ補足する",
        "reference_facts": ["講師の先ほどの言葉"]
    }

    # テスト対象のサービスにモックを注入（DI）
    responder = UserReactionResponder(analyzer_client=mock_llm_client)

    # 入力データ（Reaction）の準備
    reaction = Reaction(
        id=uuid4(),
        lecture_id=uuid4(),
        speaker=DialogueSpeaker(role="user", display_name="ユーザーA"),
        reply_target=ReplyTarget(reply_target_kind="utterance", reply_target_id=uuid4()),
        lecture_time_anchor=LectureTimeAnchor(time_range=TimeRange(start_ms=1000, end_ms=2000)),
        reaction_text=ReactionText(text="ここが少しわかりにくいです"),
        audio_data=AudioData.empty(),
        created_at=1500
    )

    # 入力データ（解析結果とペルソナ）の準備
    analysis_result = UserReactionAnalysisResult(
        intent=UserReactionIntent.CONCERN,
        tone=EmotionTone.CONFUSED,
    )
    persona = AiPersonaProfile(
        id=uuid4(), 
        display_name="サポートAI", 
        persona_prompt="あなたは親切なAIです"
    )

    # ---------------------------------------------------------
    # Act: テスト対象の振る舞いを実行する
    # ---------------------------------------------------------
    policies = responder.determine_policies(
        reaction=reaction,
        analysis_result=analysis_result,
        personas=[persona]
    )

    # ---------------------------------------------------------
    # Assert: 期待される結果を検証する
    # ---------------------------------------------------------
    
    # 1. 期待されるドメイン状態（出力結果）の検証
    assert len(policies) == 1
    assert policies[0].persona_id == persona.id
    assert policies[0].tone == "共感的"
    assert policies[0].response_intent == "相槌を打ちつつ補足する"
    assert policies[0].reference_facts == ["講師の先ほどの言葉"]

    # 【テストダブルの目的 2】: コードが依存関係とどのようにやり取りしたかを検証する（モックとしての役割）
    # テスト対象のコードが、モック化されたLLMに対して「想定通りの引数で」「1回だけ」メソッドを呼び出したかを検証する。
    mock_llm_client.generate_response_policy.assert_called_once_with(
        reaction_text="ここが少しわかりにくいです",
        persona_prompt="あなたは親切なAIです",
        analysis={
            "intent": "CONCERN",
            "tone": "CONFUSED",
        },
    )
