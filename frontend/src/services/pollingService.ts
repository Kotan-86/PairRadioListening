// 仕様: docs/spec/framework.md#7.3
import type { DialogueViewModel, TranscriptViewModel } from '../types/view_models'
import { fetchDialogue, fetchTranscript } from '../api/lectureApi'

export type PollingTickHandler = (payload: {
  transcript: TranscriptViewModel
  dialogue: DialogueViewModel
}) => void

export type PollingErrorHandler = (error: unknown) => void

const DEFAULT_INTERVAL_MS = 2500

export function startViewModelPolling(options: {
  lecture_id: string
  onTick: PollingTickHandler
  onError?: PollingErrorHandler
  intervalMs?: number
}): () => void {
  const intervalMs = options.intervalMs ?? DEFAULT_INTERVAL_MS
  let stopped = false

  async function tick() {
    if (stopped) return
    try {
      const [transcriptResult, dialogueResult] = await Promise.all([
        fetchTranscript(options.lecture_id),
        fetchDialogue(options.lecture_id),
      ])
      if (stopped) return
      options.onTick({
        transcript: transcriptResult.body,
        dialogue: dialogueResult.body,
      })
    } catch (error) {
      options.onError?.(error)
    }
  }

  void tick()
  const timerId = window.setInterval(() => {
    void tick()
  }, intervalMs)

  return () => {
    stopped = true
    window.clearInterval(timerId)
  }
}
