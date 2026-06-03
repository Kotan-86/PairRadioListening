<script setup lang="ts">
// 仕様: docs/spec/interface.md#post_user_reaction_controller, docs/spec/framework.md#7.2
import type { LectureSessionStatus } from '../types/view_models'

defineProps<{
  status: LectureSessionStatus
  reaction_text: string
  speaker_display_name: string
  lecture_time_anchor: number
}>()

const emit = defineEmits<{
  'update:reaction_text': [value: string]
  'update:speaker_display_name': [value: string]
  'update:lecture_time_anchor': [value: number]
  submit: []
}>()
</script>

<template>
  <section class="control-section reaction-form" aria-label="リアクション投稿">
    <h3>投稿</h3>

    <div class="form-field">
      <label for="speaker-display-name">表示名</label>
      <input
        id="speaker-display-name"
        type="text"
        :value="speaker_display_name"
        :disabled="status !== 'active'"
        @input="emit('update:speaker_display_name', ($event.target as HTMLInputElement).value)"
      />
    </div>

    <div class="form-field">
      <label for="lecture-time-anchor">講義時刻（ms）</label>
      <input
        id="lecture-time-anchor"
        type="number"
        :value="lecture_time_anchor"
        :disabled="status !== 'active'"
        @input="emit('update:lecture_time_anchor', Number(($event.target as HTMLInputElement).value))"
      />
    </div>

    <div class="form-field">
      <label for="reaction-text">リアクション</label>
      <textarea
        id="reaction-text"
        :value="reaction_text"
        :disabled="status !== 'active'"
        placeholder="感想や疑問を入力..."
        @input="emit('update:reaction_text', ($event.target as HTMLTextAreaElement).value)"
      />
    </div>

    <p class="form-note">将来: AI 行をクリックして返信先（reply_target）を選択</p>

    <div class="form-actions">
      <button
        type="button"
        class="primary"
        :disabled="status !== 'active' || !reaction_text.trim()"
        @click="emit('submit')"
      >
        投稿
      </button>
    </div>
  </section>
</template>
