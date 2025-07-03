<template>
  <svg
    :class="['animate-spin', sizeClass, colorClass]"
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
  >
    <circle
      class="opacity-25"
      cx="12"
      cy="12"
      r="10"
      stroke="currentColor"
      stroke-width="4"
    ></circle>
    <path
      class="opacity-75"
      fill="currentColor"
      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
    ></path>
  </svg>
</template>

<script setup lang="ts">
interface Props {
  size?: 'small' | 'medium' | 'large' | 'vSmall';
  color?: 'primary' | 'white' | 'current'; // current uses currentColor
}

const props = withDefaults(defineProps<Props>(), {
  size: 'medium',
  color: 'primary',
});

const sizeClass = computed(() => {
  switch (props.size) {
    case 'vSmall': return 'h-3 w-3';
    case 'small': return 'h-5 w-5';
    case 'medium': return 'h-8 w-8';
    case 'large': return 'h-12 w-12';
    default: return 'h-8 w-8';
  }
});

const colorClass = computed(() => {
  switch (props.color) {
    case 'primary': return 'text-primary-red';
    case 'white': return 'text-primary-smoke';
    case 'current': return 'text-current'; // Useful if parent controls color
    default: return 'text-primary-red';
  }
});
</script>
