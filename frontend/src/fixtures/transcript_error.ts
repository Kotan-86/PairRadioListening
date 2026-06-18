// 仕様: docs/spec/interface.md#7.2

import type { TranscriptViewModel } from '../types/view_models'
import { MOCK_LECTURE_ID } from './transcript_active'

export const transcriptErrorFixture: TranscriptViewModel = {
  lecture_id: MOCK_LECTURE_ID,
  lines: [],
  latest_anchor_ms: 0,
  error_message: '文字起こしの取得に失敗しました。しばらくしてから再度お試しください。',
}
