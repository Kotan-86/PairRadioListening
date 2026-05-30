import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from domain.services.lecture_log_formatter import LectureLogFormatter
from domain.entities.lecture import Lecture
from domain.entities.utterance import Utterance
from domain.entities.reaction import Reaction
from domain.value_objects.formatted_lecture_log import LogFormat
from domain.value_objects.time_range import TimeRange
from domain.value_objects.speech_text import SpeechText
from domain.value_objects.recording_speaker import RecordingSpeaker
from domain.value_objects.dialogue_speaker import DialogueSpeaker
from domain.value_objects.reply_target import ReplyTarget
from domain.value_objects.lecture_time_anchor import LectureTimeAnchor
from domain.value_objects.reaction_text import ReactionText
from domain.value_objects.audio_data import AudioData

class TestLectureLogFormatter:

    def test_format_generates_markdown_with_correct_chronological_order(self):
        """
        【ステートベーステスト】
        本物のデータを使用し、発話とリアクションが時系列（ミリ秒昇順）に
        正しくマージ・ソートされて出力されるかを検証する。
        """
        # ---------------------------------------------------------
        # Arrange: テスト条件とテストデータを準備する
        # ---------------------------------------------------------
        formatter = LectureLogFormatter()
        lecture = Lecture(id=uuid4(), title="テスト講義", started_at=0, ended_at=3000, persona_profiles=[])
        
        # 1000ms時点の講師の発話
        utterance = Utterance(
            id=uuid4(),
            time_range=TimeRange(start_ms=1000, end_ms=1500),
            speech_text=SpeechText(text="最初のポイントです"),
            speaker=RecordingSpeaker(display_name="講師")
        )
        
        # 2000ms時点のユーザーのリアクション
        reaction = Reaction(
            id=uuid4(),
            lecture_id=lecture.id,
            speaker=DialogueSpeaker(role="user", display_name="ユーザーA"),
            reply_target=ReplyTarget(reply_target_kind="utterance", reply_target_id=utterance.id),
            lecture_time_anchor=LectureTimeAnchor(time_range=TimeRange(start_ms=1000, end_ms=1500), utterance_id=utterance.id),
            reaction_text=ReactionText(text="なるほど、わかりやすい"),
            audio_data=AudioData.empty(),
            created_at=2000
        )

        # ---------------------------------------------------------
        # Act: テスト対象の振る舞いを実行する
        # ---------------------------------------------------------
        result = formatter.format(
            lecture=lecture,
            utterances=[utterance],
            reactions=[reaction],
            format_type=LogFormat.MARKDOWN
        )

        # ---------------------------------------------------------
        # Assert: 期待される結果を検証する
        # ---------------------------------------------------------
        assert result.format_type == LogFormat.MARKDOWN
        # 出力された文字列内に、時系列で情報が含まれているかを検証
        assert "最初のポイントです" in result.content
        assert "なるほど、わかりやすい" in result.content
        # 講師の発話（1000ms）がリアクション（2000ms）より前に出力されていること（時系列ソートの証明）
        assert result.content.index("最初のポイントです") < result.content.index("なるほど、わかりやすい")


    def test_format_raises_error_if_invariants_are_violated(self):
        """
        【異常系のテスト】
        不変条件（reply_target や lecture_time_anchor が欠落しているデータ）
        が渡された場合、期待通りにエラーを投げるかを検証する。
        """
        # Arrange
        formatter = LectureLogFormatter()
        lecture = Lecture(id=uuid4(), title="テスト講義", started_at=0, ended_at=1000, persona_profiles=[])
        
        # 意図的に lecture_time_anchor を None にした不正な Reaction を作成
        # (通常 dataclass の生成時には入るが、何らかのバグで None になった状態をシミュレート)
        invalid_reaction = MagicMock(spec=Reaction)
        invalid_reaction.id = uuid4()
        invalid_reaction.lecture_time_anchor = None 

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            formatter.format(
                lecture=lecture,
                utterances=[],
                reactions=[invalid_reaction],
                format_type=LogFormat.MARKDOWN
            )
        
        assert "lecture_time_anchor が欠落しています" in str(exc_info.value)


    def test_format_delegates_to_json_formatter_using_test_double(self):
        """
        【テストダブルを用いたインタラクションテスト】
        JSON形式が指定された際、モックを用いて振る舞いを制御し、
        内部の変換ロジックと正しくやり取りが行われているかを検証する。
        """
        # ---------------------------------------------------------
        # Arrange: テスト条件とテストデータを準備する
        # ---------------------------------------------------------
        formatter = LectureLogFormatter()
        
        # 引数用のダミーデータ（ここでは中身の正確性は重要ではない）
        dummy_lecture = MagicMock(spec=Lecture)
        dummy_utterances = [MagicMock(spec=Utterance)]
        dummy_reactions = [MagicMock(spec=Reaction)]
        # バリデーションを通過させるためのダミー設定
        dummy_reactions[0].lecture_time_anchor = MagicMock()
        dummy_reactions[0].reply_target = MagicMock()

        # 【テストダブルの目的 1】: 依存関係の振る舞いを制御する
        # patch を用いて、内部の `_to_json` メソッド（依存先ロジック）をモック化。
        # 複雑なJSON変換をスキップし、固定の文字列を返すように振る舞いを制御（Stubbing）する。
        with patch.object(formatter, '_to_json', return_value='{"mocked": "json_data"}') as mock_to_json:

            # ---------------------------------------------------------
            # Act: テスト対象の振る舞いを実行する
            # ---------------------------------------------------------
            result = formatter.format(
                lecture=dummy_lecture,
                utterances=dummy_utterances,
                reactions=dummy_reactions,
                format_type=LogFormat.JSON
            )

            # ---------------------------------------------------------
            # Assert: 期待される結果を検証する
            # ---------------------------------------------------------
            # モックによって制御された振る舞い（固定文字列）がそのまま出力されることの検証
            assert result.content == '{"mocked": "json_data"}'
            assert result.format_type == LogFormat.JSON

            # 【テストダブルの目的 2】: コードが依存関係とどのようにやり取りしたかを検証する
            # LogFormat.JSON を指定したことにより、`_to_markdown` ではなく、
            # `_to_json` メソッドに対して、「正しい引数で」「1回だけ」やり取り（委譲）が行われたかを検証（Spying）する。
            mock_to_json.assert_called_once_with(dummy_lecture, dummy_utterances, dummy_reactions)
