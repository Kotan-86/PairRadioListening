<script setup lang="ts">
// 仕様: docs/spec/interface.md#7.3
import PanelErrorBanner from './PanelErrorBanner.vue'
import type { TranscriptViewModel } from '../types/view_models'

defineProps<{
  model: TranscriptViewModel
}>()
</script>

<template>
  <section class="panel transcript-panel" aria-label="文字起こし">
    <header class="panel-header">
      <h2 class="panel-title">文字起こし</h2>
    </header>
    <PanelErrorBanner :error_message="model.error_message" />
    <ul v-if="model.lines.length" class="line-list">
      <li
        v-for="line in model.lines"
        :key="line.utterance_id"
        class="line-item transcript-line"
      >
        <span class="line-meta">
          <span class="time-label">{{ line.time_label }}</span>
          <span class="speaker-label">{{ line.speaker_label }}</span>
        </span>
        <p class="line-body">{{ line.body }}</p>
      </li>
    </ul>
    <p v-else-if="!model.error_message" class="panel-empty">文字起こしはまだありません。</p>
  </section>
</template>
