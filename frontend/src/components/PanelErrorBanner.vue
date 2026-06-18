<script setup lang="ts">
// 仕様: docs/spec/interface.md#7.2
defineProps<{
  error_message: string
}>()
</script>

<template>
  <div v-if="error_message" class="panel-error-banner" role="alert">
    {{ error_message }}
  </div>
</template>
