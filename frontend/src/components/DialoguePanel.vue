<script setup lang="ts">
// 仕様: docs/spec/interface.md#7.1, docs/spec/interface.md#7.4, docs/spec/framework.md#7.4
import { ref } from 'vue'
import PanelErrorBanner from './PanelErrorBanner.vue'
import { useStickyBottomScroll } from '../composables/useStickyBottomScroll'
import type { DialogueViewModel } from '../types/view_models'

const props = defineProps<{
  model: DialogueViewModel
}>()

const listEl = ref<HTMLElement | null>(null)

useStickyBottomScroll({
  listEl,
  tailId: () => props.model.lines.at(-1)?.reaction_id,
})
</script>

<template>
  <section class="panel dialogue-panel" aria-label="対話">
    <header class="panel-header">
      <h2 class="panel-title">対話</h2>
    </header>
    <PanelErrorBanner :error_message="model.error_message" />
    <ul v-if="model.lines.length" ref="listEl" class="line-list">
      <li
        v-for="line in model.lines"
        :key="line.reaction_id"
        class="line-item dialogue-line"
      >
        <span class="speaker-label">{{ line.speaker_label }}</span>
        <p class="line-body">{{ line.body }}</p>
        <p v-if="line.reference_time_label" class="reference-label reference-time">
          {{ line.reference_time_label }}
        </p>
        <p v-if="line.reference_quote_label" class="reference-label reference-quote">
          {{ line.reference_quote_label }}
        </p>
      </li>
    </ul>
    <p v-else-if="!model.error_message" class="panel-empty">対話はまだありません。</p>
  </section>
</template>
