// 仕様: docs/spec/interface.md#start_lecture_controller, docs/spec/framework.md#7.2

import type { LectureSessionStatus } from './view_models'

export interface AiPersonaProfileForm {
  id: string
  display_name: string
  persona_prompt: string
}

export interface StartLectureForm {
  persona_profiles: [AiPersonaProfileForm]
  title: string
}

export interface LectureShellState {
  lecture_id: string | null
  sessionStatus: LectureSessionStatus
}
