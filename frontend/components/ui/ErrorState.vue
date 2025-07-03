<template>
  <div class="text-center py-20">
    <ExclamationTriangleIcon class="h-12 w-12 text-primary-error mx-auto mb-4" />
    <p class="text-primary-silver mb-4">{{ message }}</p>
    <UiButton @click="$emit('retry')" variant="primary">{{ retryText }}</UiButton>
  </div>
</template>

<script setup lang="ts">
import { ExclamationTriangleIcon } from '@heroicons/vue/24/outline';
import UiButton from '~/components/ui/Button.vue';

defineProps<{
  message: string;
  retryText?: string;
}>();

defineEmits<{
  retry: [];
}>();
</script>