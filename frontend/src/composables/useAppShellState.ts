// 仕様: docs/spec/framework.md#7.2, docs/spec/interface.md#7
import { ref, computed, onUnmounted } from 'vue'
import type {
  DialogueViewModel,
  LectureSessionStatus,
  TranscriptViewModel,
} from '../types/view_models'
import type { StartLectureForm } from '../types/lecture'
import {
  endLecture as endLectureApi,
  fetchDialogue,
  postUserReaction,
  startLecture as startLectureApi,
} from '../api/lectureApi'
import { startViewModelPolling } from '../services/pollingService'
import { transcriptActiveFixture } from '../fixtures/transcript_active'
import { transcriptErrorFixture } from '../fixtures/transcript_error'
import { dialogueActiveFixture } from '../fixtures/dialogue_active'
import { dialogueErrorFixture } from '../fixtures/dialogue_error'

export type FixturePreset = 'idle' | 'active' | 'transcript_error' | 'dialogue_error'

const emptyTranscript = (lecture_id: string): TranscriptViewModel => ({
  lecture_id,
  lines: [],
  latest_anchor_ms: 0,
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
  const useLiveApi = ref(true)
  const apiError = ref<string | null>(null)

  const startLectureForm = ref<StartLectureForm>({
    persona_profiles: [{ id: 'persona-1', display_name: 'AI', persona_prompt: '' }],
    title: '',
  })

  const reactionText = ref('')
  const speakerDisplayName = ref('ユーザー')

  const transcript = ref<TranscriptViewModel>(emptyTranscript(''))
  const dialogue = ref<DialogueViewModel>(emptyDialogue(''))

  let stopPolling: (() => void) | null = null

  const controlsDisabled = computed(() => sessionStatus.value === 'ended')
  const reactionFormEnabled = computed(() => sessionStatus.value === 'active')
  const reactionSubmitDisabled = computed(
    () =>
      !reactionText.value.trim() || transcript.value.latest_anchor_ms === 0,
  )

  function stopViewModelPolling() {
    stopPolling?.()
    stopPolling = null
  }

  function applyFixturePreset(preset: FixturePreset) {
    if (useLiveApi.value) return
    const id = lecture_id.value ?? 'mock-lecture'
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

  function beginPolling(id: string) {
    stopViewModelPolling()
    stopPolling = startViewModelPolling({
      lecture_id: id,
      onTick: ({ transcript: nextTranscript, dialogue: nextDialogue }) => {
        transcript.value = nextTranscript
        dialogue.value = nextDialogue
      },
      onError: (error) => {
        apiError.value = error instanceof Error ? error.message : String(error)
      },
    })
  }

  async function startLecture() {
    apiError.value = null
    if (!useLiveApi.value) {
      lecture_id.value = 'mock-lecture'
      sessionStatus.value = 'active'
      fixturePreset.value = 'active'
      applyFixturePreset('active')
      return
    }

    const result = await startLectureApi(startLectureForm.value)
    if (result.status !== 201 || !result.body.success) {
      apiError.value = result.body.error_kind || 'start_lecture_failed'
      return
    }

    lecture_id.value = result.body.lecture_id
    sessionStatus.value = 'active'
    transcript.value = emptyTranscript(result.body.lecture_id)
    dialogue.value = emptyDialogue(result.body.lecture_id)
    beginPolling(result.body.lecture_id)
  }

  async function endLecture() {
    if (!useLiveApi.value) {
      sessionStatus.value = 'ended'
      stopViewModelPolling()
      return
    }

    const id = lecture_id.value
    if (!id) return

    const result = await endLectureApi(id)
    if (result.status !== 200 || !result.body.success) {
      apiError.value = result.body.error_kind || 'end_lecture_failed'
      return
    }
    sessionStatus.value = 'ended'
    stopViewModelPolling()
  }

  function setFixturePreset(preset: FixturePreset) {
    fixturePreset.value = preset
    applyFixturePreset(preset)
  }

  function toggleLiveApi(enabled: boolean) {
    useLiveApi.value = enabled
    if (enabled) {
      stopViewModelPolling()
      lecture_id.value = null
      sessionStatus.value = 'idle'
      transcript.value = emptyTranscript('')
      dialogue.value = emptyDialogue('')
    } else {
      applyFixturePreset(fixturePreset.value)
    }
  }

  async function submitReaction() {
    if (!reactionFormEnabled.value) return

    const id = lecture_id.value
    const text = reactionText.value.trim()
    const anchor = transcript.value.latest_anchor_ms
    if (!id || !text || anchor === 0) return

    if (!useLiveApi.value) {
      reactionText.value = ''
      return
    }

    apiError.value = null
    const result = await postUserReaction(id, {
      reaction_text: text,
      lecture_time_anchor: anchor,
      speaker_display_name: speakerDisplayName.value,
    })
    if (result.status !== 200 || !result.body.success) {
      apiError.value = result.body.error_kind || 'post_user_reaction_failed'
      return
    }

    reactionText.value = ''
    const dialogueResult = await fetchDialogue(id)
    if (dialogueResult.status === 200) {
      dialogue.value = dialogueResult.body
    }
  }

  onUnmounted(() => {
    stopViewModelPolling()
  })

  return {
    lecture_id,
    sessionStatus,
    fixturePreset,
    useLiveApi,
    apiError,
    startLectureForm,
    reactionText,
    speakerDisplayName,
    transcript,
    dialogue,
    controlsDisabled,
    reactionFormEnabled,
    reactionSubmitDisabled,
    startLecture,
    endLecture,
    setFixturePreset,
    toggleLiveApi,
    submitReaction,
  }
}
