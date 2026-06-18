// 仕様: docs/spec/framework.md#2.3, docs/spec/interface.md#3.3
import type { DialogueViewModel, TranscriptViewModel } from '../types/view_models'
import type { StartLectureForm } from '../types/lecture'
import { apiFetch } from './apiClient'

export interface StartLectureOutcome {
  success: boolean
  lecture_id: string
  error_kind: string
}

export interface EndLectureOutcome {
  success: boolean
  lecture_id: string
  ended_at: number
  error_kind: string
}

export interface PostUserReactionOutcome {
  success: boolean
  reaction_id: string
  lecture_id: string
  error_kind: string
}

export async function startLecture(form: StartLectureForm) {
  const persona = form.persona_profiles[0]
  return apiFetch<StartLectureOutcome>('/api/lectures/start', {
    method: 'POST',
    body: JSON.stringify({
      persona_profiles: [
        {
          id: persona.id,
          display_name: persona.display_name,
          persona_prompt: persona.persona_prompt,
        },
      ],
      title: form.title,
    }),
  })
}

export async function endLecture(lecture_id: string) {
  return apiFetch<EndLectureOutcome>(`/api/lectures/${lecture_id}/end`, {
    method: 'POST',
  })
}

export async function fetchTranscript(lecture_id: string) {
  return apiFetch<TranscriptViewModel>(`/api/lectures/${lecture_id}/transcript`)
}

export async function fetchDialogue(lecture_id: string) {
  return apiFetch<DialogueViewModel>(`/api/lectures/${lecture_id}/dialogue`)
}

export async function postUserReaction(
  lecture_id: string,
  body: {
    reaction_text: string
    lecture_time_anchor: number
    speaker_display_name: string
  },
) {
  return apiFetch<PostUserReactionOutcome>(`/api/lectures/${lecture_id}/reactions`, {
    method: 'POST',
    body: JSON.stringify(body),
  })
}
