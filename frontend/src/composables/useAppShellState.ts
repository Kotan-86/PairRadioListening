// 仕様: docs/spec/framework.md#7.2, docs/spec/interface.md#7

import { ref, computed } from 'vue'
import type {
  DialogueViewModel,
  LectureSessionStatus,
  TranscriptViewModel,
} from '../types/view_models'
import type { StartLectureForm } from '../types/lecture'
import { MOCK_LECTURE_ID } from '../fixtures/transcript_active'
import { transcriptActiveFixture } from '../fixtures/transcript_active'
import { transcriptErrorFixture } from '../fixtures/transcript_error'
import { dialogueActiveFixture } from '../fixtures/dialogue_active'
import { dialogueErrorFixture } from '../fixtures/dialogue_error'

export type FixturePreset = 'idle' | 'active' | 'transcript_error' | 'dialogue_error'

const emptyTranscript = (lecture_id: string): TranscriptViewModel => ({
  lecture_id,
  lines: [],
  error_message: '',
})

const emptyDialogue = (lecture_id: string): DialogueViewModel => ({
  lecture_id,
  lines: [],
  error_message: '',
})

export function useAppShellState() {
  const lecture_id = ref<string | null>(null)
  const sessionStatus = ref<LectureSessionStatus>('idle')
  const fixturePreset = ref<FixturePreset>('idle')

  const startLectureForm = ref<StartLectureForm>({
    persona_profiles: [{ display_name: '', persona_prompt: '' }],
    title: '',
  })

  const reactionText = ref('')
  const speakerDisplayName = ref('ユーザー')
  const lectureTimeAnchor = ref(125000)

  const transcript = ref<TranscriptViewModel>(emptyTranscript(''))
  const dialogue = ref<DialogueViewModel>(emptyDialogue(''))

  const controlsDisabled = computed(() => sessionStatus.value === 'ended')
  const reactionFormEnabled = computed(() => sessionStatus.value === 'active')

  function applyFixturePreset(preset: FixturePreset) {
    const id = lecture_id.value ?? MOCK_LECTURE_ID
    switch (preset) {
      case 'idle':
        transcript.value = emptyTranscript(id)
        dialogue.value = emptyDialogue(id)
        break
      case 'active':
        transcript.value = { ...transcriptActiveFixture, lecture_id: id }
        dialogue.value = { ...dialogueActiveFixture, lecture_id: id }
        break
      case 'transcript_error':
        transcript.value = { ...transcriptErrorFixture, lecture_id: id }
        dialogue.value = { ...dialogueActiveFixture, lecture_id: id }
        break
      case 'dialogue_error':
        transcript.value = { ...transcriptActiveFixture, lecture_id: id }
        dialogue.value = { ...dialogueErrorFixture, lecture_id: id }
        break
    }
  }

  function startLecture() {
    lecture_id.value = MOCK_LECTURE_ID
    sessionStatus.value = 'active'
    fixturePreset.value = 'active'
    applyFixturePreset('active')
  }

  function endLecture() {
    sessionStatus.value = 'ended'
  }

  function setFixturePreset(preset: FixturePreset) {
    fixturePreset.value = preset
    applyFixturePreset(preset)
  }

  function submitReaction() {
    if (!reactionFormEnabled.value) return
    reactionText.value = ''
  }

  return {
    lecture_id,
    sessionStatus,
    fixturePreset,
    startLectureForm,
    reactionText,
    speakerDisplayName,
    lectureTimeAnchor,
    transcript,
    dialogue,
    controlsDisabled,
    reactionFormEnabled,
    startLecture,
    endLecture,
    setFixturePreset,
    submitReaction,
  }
}
