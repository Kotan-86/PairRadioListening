// 仕様: docs/spec/interface.md#7.2

import type { DialogueViewModel } from '../types/view_models'
import { MOCK_LECTURE_ID } from './transcript_active'

export const dialogueErrorFixture: DialogueViewModel = {
  lecture_id: MOCK_LECTURE_ID,
  lines: [],
  error_message: '対話の取得に失敗しました。ネットワーク接続を確認してください。',
}
