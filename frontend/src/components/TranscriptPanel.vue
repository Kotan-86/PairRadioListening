<script setup lang="ts">
// 仕様: docs/spec/interface.md#7.1, docs/spec/interface.md#7.3
import { ref } from 'vue'
import PanelErrorBanner from './PanelErrorBanner.vue'
import { useStickyBottomScroll } from '../composables/useStickyBottomScroll'
import type { TranscriptViewModel } from '../types/view_models'

const props = defineProps<{
  model: TranscriptViewModel
}>()

const listEl = ref<HTMLElement | null>(null)

useStickyBottomScroll({
  listEl,
  tailId: () => props.model.lines.at(-1)?.utterance_id,
})
</script>

<template>
  <section class="panel transcript-panel" aria-label="文字起こし">
    <header class="panel-header">
      <h2 class="panel-title">文字起こし</h2>
    </header>
    <PanelErrorBanner :error_message="model.error_message" />
    <ul v-if="model.lines.length" ref="listEl" class="line-list">
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
