<script setup lang="ts">
// 仕様: docs/spec/interface.md#start_lecture_controller, docs/spec/framework.md#7.2
import type { StartLectureForm } from '../types/lecture'
import type { LectureSessionStatus } from '../types/view_models'

const props = defineProps<{
  status: LectureSessionStatus
  disabled: boolean
  form: StartLectureForm
  lecture_id: string | null
}>()

const emit = defineEmits<{
  'update:form': [form: StartLectureForm]
  start: []
  end: []
}>()

function updatePersonaField(field: 'display_name' | 'persona_prompt', value: string) {
  emit('update:form', {
    ...props.form,
    persona_profiles: [{ ...props.form.persona_profiles[0], [field]: value }],
  })
}

function updateTitle(value: string) {
  emit('update:form', { ...props.form, title: value })
}
</script>

<template>
  <section class="control-section lecture-controls" aria-label="講義操作">
    <div class="control-section-header">
      <h3>講義</h3>
      <span class="status-badge" :class="status">{{ status }}</span>
    </div>

    <template v-if="status === 'idle'">
      <div class="form-field">
        <label for="persona-display-name">AI 表示名</label>
        <input
          id="persona-display-name"
          type="text"
          :value="form.persona_profiles[0].display_name"
          :disabled="disabled"
          @input="updatePersonaField('display_name', ($event.target as HTMLInputElement).value)"
        />
      </div>
      <div class="form-field">
        <label for="persona-prompt">ペルソナプロンプト</label>
        <textarea
          id="persona-prompt"
          :value="form.persona_profiles[0].persona_prompt"
          :disabled="disabled"
          @input="updatePersonaField('persona_prompt', ($event.target as HTMLTextAreaElement).value)"
        />
      </div>
      <div class="form-field">
        <label for="lecture-title">タイトル（任意）</label>
        <input
          id="lecture-title"
          type="text"
          :value="form.title"
          :disabled="disabled"
          @input="updateTitle(($event.target as HTMLInputElement).value)"
        />
      </div>
    </template>

    <p v-else-if="lecture_id" class="form-note">
      講義 ID: {{ lecture_id }}
    </p>

    <div class="form-actions">
      <button
        v-if="status === 'idle'"
        type="button"
        class="primary"
        :disabled="disabled"
        @click="emit('start')"
      >
        開始
      </button>
      <button
        v-if="status === 'active'"
        type="button"
        class="danger"
        :disabled="disabled"
        @click="emit('end')"
      >
        終了
      </button>
    </div>
  </section>
</template>

<style scoped>
.control-section-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
</style>
