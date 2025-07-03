<template>
  <div class="w-full bg-accent-DEFAULT rounded-full h-2.5" :class="containerClass">
    <div
      class="bg-[#FB2576] h-2.5 rounded-full transition-all duration-300 ease-out"
      :class="barClass"
      :style="{ width: `${progress}%` }"
    >
      <span v-if="showPercentage && percentagePosition === 'inside'" class="text-xs font-medium text-background-DEFAULT absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
        {{ Math.round(progress) }}%
      </span>
    </div>
    <span v-if="showPercentage && percentagePosition === 'outside'" class="text-xs font-medium text-text-muted ml-2">
      {{ Math.round(progress) }}%
    </span>
  </div>
</template>

<script setup lang="ts">
interface Props {
  progress: number; // 0-100
  showPercentage?: boolean;
  percentagePosition?: 'inside' | 'outside'; // 'inside' only works well for thicker bars
  barClass?: string;
  containerClass?: string;
}

withDefaults(defineProps<Props>(), {
  progress: 0,
  showPercentage: false,
  percentagePosition: 'outside',
  barClass: '',
  containerClass: 'relative', // For absolute positioning of text inside
});
</script>
