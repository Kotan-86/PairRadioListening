// 仕様: docs/spec/interface.md#7.3–7.4

export type LectureSessionStatus = 'idle' | 'active' | 'ended'

export interface TranscriptLineView {
  utterance_id: string
  time_label: string
  speaker_label: string
  body: string
}

export interface TranscriptViewModel {
  lecture_id: string
  lines: TranscriptLineView[]
  error_message: string
}

export interface DialogueLineView {
  reaction_id: string
  speaker_label: string
  body: string
  reference_time_label: string
  reference_quote_label: string
}

export interface DialogueViewModel {
  lecture_id: string
  lines: DialogueLineView[]
  error_message: string
}
