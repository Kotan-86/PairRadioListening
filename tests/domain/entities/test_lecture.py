import pytest
from uuid import uuid4

from domain.entities.lecture import Lecture
from domain.entities.utterance import Utterance
from domain.value_objects.time_range import TimeRange
from domain.value_objects.speech_text import SpeechText
from domain.value_objects.recording_speaker import RecordingSpeaker

def test_lecture_add_utterance_updates_ended_at():
    """
    発話を講義に追加した際、講義の終了時間（ended_at）が
    追加された発話の終了時間に正しく更新されるかを検証する。
    """
    
    # ---------------------------------------------------------
    # Arrange: テスト条件とテストデータを準備する
    # ---------------------------------------------------------
    lecture_id = uuid4()
    # 初期状態の講義（終了時間は 1000ms と仮定）
    lecture = Lecture(
        id=lecture_id,
        title="テスト講義",
        started_at=0,
        ended_at=1000,
        persona_profiles=[],
        utterances=[]
    )
    
    # 追加する新しい発話データ（終了時間が 2500ms の事実）
    new_utterance = Utterance(
        id=uuid4(),
        time_range=TimeRange(start_ms=1000, end_ms=2500),
        speech_text=SpeechText(text="ここから重要なポイントです。"),
        speaker=RecordingSpeaker(display_name="講師A")
    )

    # ---------------------------------------------------------
    # Act: テスト対象の振る舞いを実行する
    # ---------------------------------------------------------
    lecture.add_utterance(new_utterance)

    # ---------------------------------------------------------
    # Assert: 期待される結果を検証する
    # ---------------------------------------------------------
    # 1. 発話リストに追加されていること
    assert len(lecture.utterances) == 1
    assert lecture.utterances[0] == new_utterance
    
    # 2. 講義の終了時間(ended_at)が、新しい発話の終了時間に合わせて更新されていること
    assert lecture.ended_at == 2500
