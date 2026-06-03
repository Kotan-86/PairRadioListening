<script setup lang="ts">
// 仕様: docs/spec/framework.md#7.2
import TranscriptPanel from './components/TranscriptPanel.vue'
import DialoguePanel from './components/DialoguePanel.vue'
import LectureControls from './components/LectureControls.vue'
import ReactionForm from './components/ReactionForm.vue'
import { useAppShellState, type FixturePreset } from './composables/useAppShellState'

const {
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
  startLecture,
  endLecture,
  setFixturePreset,
  submitReaction,
} = useAppShellState()

function onFixtureChange(event: Event) {
  setFixturePreset((event.target as HTMLSelectElement).value as FixturePreset)
}
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <h1 class="app-title">Pair Radio Listening</h1>
      <div class="dev-controls">
        <label>
          フィクスチャ:
          <select :value="fixturePreset" @change="onFixtureChange">
            <option value="idle">idle（空）</option>
            <option value="active">active（成功）</option>
            <option value="transcript_error">transcript エラー</option>
            <option value="dialogue_error">dialogue エラー</option>
          </select>
        </label>
      </div>
    </header>

    <main class="main-grid">
      <TranscriptPanel :model="transcript" />
      <DialoguePanel :model="dialogue" />
    </main>

    <footer class="bottom-bar">
      <LectureControls
        :status="sessionStatus"
        :disabled="controlsDisabled"
        :form="startLectureForm"
        :lecture_id="lecture_id"
        @update:form="startLectureForm = $event"
        @start="startLecture"
        @end="endLecture"
      />
      <ReactionForm
        :status="sessionStatus"
        :reaction_text="reactionText"
        :speaker_display_name="speakerDisplayName"
        :lecture_time_anchor="lectureTimeAnchor"
        @update:reaction_text="reactionText = $event"
        @update:speaker_display_name="speakerDisplayName = $event"
        @update:lecture_time_anchor="lectureTimeAnchor = $event"
        @submit="submitReaction"
      />
    </footer>
  </div>
</template>
