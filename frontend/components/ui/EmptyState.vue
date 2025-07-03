<template>
  <div class="text-center py-20">
    <VideoCameraSlashIcon class="h-12 w-12 text-primary-silver mx-auto mb-4" />
    <p class="text-primary-silver">{{ message }}</p>
  </div>
</template>

<script setup lang="ts">
import { VideoCameraSlashIcon } from '@heroicons/vue/24/outline';

defineProps<{
  message: string;
}>();
</script>