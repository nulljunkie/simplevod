<template>
  <button
    v-if="uploadsStore.activeUploads.length > 0"
    @click="uploadsStore.toggleUploadPanel"
    class="relative h-10 w-10 rounded-full focus:outline-none"
    aria-label="View upload progress"
  >
    <svg class="h-full w-full transform -rotate-90" viewBox="0 0 40 40">
      <circle
        cx="20"
        cy="20"
        r="16"
        fill="transparent"
        stroke="#7e002b"
        stroke-width="4"
      />
      <circle
        cx="20"
        cy="20"
        r="16"
        fill="transparent"
        :stroke="progressColor"
        stroke-width="4"
        stroke-linecap="round"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="dashOffset"
      />
    </svg>

    <span class="absolute inset-0 flex items-center justify-center text-[10px] font-semibold text-primary-silver">
      {{ percentage }}%
    </span>

    <span
      v-if="showCompletedBadge"
      class="absolute top-0 right-0 transform translate-x-1/3 -translate-y-1/3 p-0.5 bg-primary-success rounded-full"
    >
      <CheckIcon class="h-3 w-3 text-background-DEFAULT" />
    </span>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useUploadsStore } from '~/stores/uploads';
import { CheckIcon } from '@heroicons/vue/24/outline';

const uploadsStore = useUploadsStore();

const percentage = computed(() => uploadsStore.overallProgress);

const radius = 16; // must match r in SVG
const circumference = 2 * Math.PI * radius;

const dashOffset = computed(() => {
  return circumference - (percentage.value / 100) * circumference;
});

const progressColor = computed(() => {
  return percentage.value === 100 ? '#22C55E' : '#FB2576';
});

const showCompletedBadge = computed(() => {
  return (
    uploadsStore.activeUploads.filter(u => u.status === 'completed').length > 0 &&
    !uploadsStore.hasActiveUploads
  );
});
</script>

<style scoped>
</style>
