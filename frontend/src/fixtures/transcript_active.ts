// 仕様: docs/spec/interface.md#7.3

import type { TranscriptViewModel } from '../types/view_models'

export const MOCK_LECTURE_ID = 'lecture-mock-1'

export const transcriptActiveFixture: TranscriptViewModel = {
  lecture_id: MOCK_LECTURE_ID,
  error_message: '',
  latest_anchor_ms: 125000,
  lines: [
    {
      utterance_id: 'utt-001',
      time_label: '00:00',
      speaker_label: '講師',
      body: '今日はクリーンアーキテクチャについて話します。',
    },
    {
      utterance_id: 'utt-002',
      time_label: '00:15',
      speaker_label: '講師',
      body: '依存関係の方向を内側に向けることが重要です。',
    },
    {
      utterance_id: 'utt-003',
      time_label: '02:05',
      speaker_label: '講師',
      body: 'ユースケースはアプリケーションの意図を表します。',
    },
  ],
}
