<template>
    <button
      @click="emit('upload')"
      class="text-primary-silver hover:text-primary-smoke transition-colors"
      aria-label="Upload a video"
    >
      <ArrowUpTrayIcon class="h-6 w-6" />
    </button>

</template>

<script setup lang="ts">
import { ArrowUpTrayIcon } from '@heroicons/vue/24/outline';
const emit = defineEmits<{
  (e: 'upload'): void
}>()
</script>
