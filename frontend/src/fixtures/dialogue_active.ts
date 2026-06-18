// 仕様: docs/spec/interface.md#7.4

import type { DialogueViewModel } from '../types/view_models'
import { MOCK_LECTURE_ID } from './transcript_active'

export const dialogueActiveFixture: DialogueViewModel = {
  lecture_id: MOCK_LECTURE_ID,
  error_message: '',
  lines: [
    {
      reaction_id: 'react-001',
      speaker_label: 'ユーザー',
      body: '依存関係の方向って、具体的にどう意識すればいいですか？',
      reference_time_label: '00:15',
      reference_quote_label: '',
    },
    {
      reaction_id: 'react-002',
      speaker_label: 'AI アシスタント',
      body: '内側のドメインが外側のフレームワークを知らないようにする、というイメージですね。',
      reference_time_label: '',
      reference_quote_label: 'ユーザー: 依存関係の方向って、具体的にどう意識すればいいですか？',
    },
    {
      reaction_id: 'react-003',
      speaker_label: 'ユーザー',
      body: 'なるほど、Port と Adapter の例が欲しいです。',
      reference_time_label: '02:05',
      reference_quote_label: '',
    },
  ],
}
